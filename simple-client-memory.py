import asyncio
import json
import time
from anthropic import AsyncAnthropic
from fastmcp import Client
from typing import List, Dict, Any
from simple_weather_agent.models import ProfileInput, CityInput

class ConversationMemory:
    def __init__(self):
        # this is our storage
        self.messages: List[Dict[str, Any]] = []

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content: List[Dict[str, Any]]):
        self.messages.append({"role": "assistant", "content": content})
    
    def add_tool_result(self, tool_id: str, result: str):
        self.messages.append({
            "role": "user", 
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": result
            }]
        })
    
    def get_messages(self) -> List[Dict[str, Any]]:
        # only share copy in order to protect original - can't just append
        return self.messages.copy()
    
class EntityMemory:
    def __init__(self):
        self.entities: Dict[str, Any] = {}
        
    def upsert(self, key: str, value: Any):
        """update or insert an entity"""
        self.entities[key] = value
    
    def get(self, key: str):
        """return values using key"""
        return self.entities.get(key)

    def as_prompt_context(self) -> str:
        """serialize and put in format for LLM"""
        if not self.entities:
            return ""
        
        context_list = []
        for key, value in self.entities.items():
            context_list.append(f"{key}: {value}")

        # new line with each key/value pair, but label in brackets to match context_list list type
        return "/n".join(["Known entities:"] + context_list)
    
    # lets us inspect entity with memory=new EntityMemory(), print memory instead of a memory address blob
    def __repr__(self):
        return f"Entity Memory({self.entities})"

tool_model_map = {
    "get_city_from_profile": ProfileInput,
    "get_weather_from_city": CityInput
}

def enrich_tool_schema(tool, model_class):
    """Enrich tool.inputSchema with field descriptions from the Pydantic model."""
    model_schema = model_class.model_json_schema()
    for prop_name, prop_meta in tool.inputSchema["properties"].items():
        pyd_desc = model_schema["properties"].get(prop_name, {}).get("description")
        if pyd_desc:
            prop_meta["description"] = pyd_desc
    return tool

async def get_enriched_tools(client: Client) -> List[Dict[str, Any]]:
    tools = await client.list_tools()
    enriched = []

    for tool in tools:
        model_class = tool_model_map.get(tool.name)
        if model_class:
            tool = enrich_tool_schema(tool, model_class)
        enriched.append(tool)

    return enriched

def load_system_prompt(path: str = "prompts/system_prompt.txt") -> str:
    with open(path, "r") as f:
        return f.read().strip()
    
async def chat_with_memory(client: Client, 
                           anthropic_client: AsyncAnthropic, 
                           memory: ConversationMemory,
                           anthropic_tools: List[Dict[str, Any]], 
                           system_prompt: str,
                           max_iterations: int = 25):
    
    # add some safeguards
    max_tokens = 100000
    max_iterations = 30

    tokens_used = 0
    iterations = 0

    # Track repeated tool calls across all turns
    global_called_tools = {}  # tool_key -> count

    while (iterations < max_iterations and 
        tokens_used < max_tokens):

        # track safeguard progress
        iterations += 1
        messages = memory.get_messages()
        

        # call Claude with information
        response = await anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            system=system_prompt,
            messages=messages,
            tools=anthropic_tools,
            max_tokens=1024 # 800 word response
        )

        # Track token usage
        if hasattr(response, 'usage') and hasattr(response.usage, 'output_tokens'):
            tokens_used += response.usage.output_tokens

        # track if Claude used tools response
        assistant_content = []
        used_tools=False
        # this one tracks repeated same tool call + same arguments
        turn_repeated_tools = False # flag for this turn

        # handle responses
        for block in response.content:
            if block.type == "tool_use":
                used_tools=True 

                #build hashable block for call
                tool_key = f"{block.name}:{json.dumps(block.input, sort_keys=True)}"

                # track repeated calls
                if tool_key in global_called_tools:
                    global_called_tools[tool_key] += 1
                    print(f"Repeated tool call with same args with {tool_key}")

                    if global_called_tools[tool_key] > 2:
                        print("Claude retrying same tool + args more than 2 times")
                        turn_repeated_tools= True
                        break
                else:
                    global_called_tools[tool_key] = 1

                print(f"Tool call: {block.name}")
                print(f"Arguments: {block.input}")

                # record tool_use as assistant message
                memory.add_assistant_message([{
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                }])

                #execute tool
                result = await client.call_tool(block.name, block.input)
                print(f"Tool result: {result.data}")

                # Add tool result to memory
                memory.add_tool_result(block.id, result.data)

            elif block.type == "text":
                print(f"Claude: {block.text}")
                assistant_content.append({
                    "type": "text",
                    "text": block.text
                })
            else:
                print(f"Unknown block type: {block.type}")

        # Add assistant response to messages
        if assistant_content:
            memory.add_assistant_message(assistant_content)

        # Exit conditions
        if turn_repeated_tools:
            print("Exiting due to repeated tool calls")
            break
            
        if not used_tools:
            print("Claude finished - no tools used on this turn")
            break
        
    return memory

async def main():
    
    # connect to server
    async with Client("http://localhost:8000/mcp/") as client:
        print("Connected! Getting tools...")

        # get prompt
        print("Loading system prompt...")
        system_prompt = load_system_prompt()

        # list tools
        enriched = await get_enriched_tools(client)

        # convert to anthropic tools
        anthropic_tools = []

        for tool in enriched:
            anthropic_tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            })
        
        for tool in anthropic_tools:
            print(f"\nTool: {tool['name']}")
            props = tool["input_schema"].get("properties", {})
            for prop_name, prop in props.items():
                desc = prop.get("description", "No description")
                print(f" - {prop_name}: {desc}")

        #initialize memory
        memory = ConversationMemory()
        #initialize anthropic client to talk to LLM
        anthropic_client = AsyncAnthropic()

        # Example conversation
        user_input = input("Tell me what you want: ")
        memory.add_user_message(user_input)

        # run conversation - put in fastmcp client, claude client, memory, anthro tools, prompt
        final_memory = await chat_with_memory(client, 
                                              anthropic_client, 
                                              memory, 
                                              anthropic_tools, 
                                              system_prompt)

        # Print conversation history
        print("\n--- Conversation History ---")
        for i, msg in enumerate(final_memory.get_messages()):
            print(f"{i+1}. {msg['role']}: {msg['content']}")

    # Client is automatically closed here
    print("Disconnected from MCP server")

if __name__ == "__main__":
    asyncio.run(main())