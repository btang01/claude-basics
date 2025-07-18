import asyncio
import json
import time
from anthropic import AsyncAnthropic
from fastmcp import Client
from typing import List, Dict, Any

class ConversationMemory:
    def __init__(self):
        # this is our storage
        self.messages: List[Dict[str, Any]] = []

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def add_tool_use(self, tool_name: str, tool_input: Dict[str, Any], tool_id: str):
        self.messages.append({
            "role": "assistant",
            "content": [{
                "type": "tool_use",
                "id": tool_id,
                "name": tool_name,
                "input": tool_input
            }]
        })
    
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
    max_timeout_seconds = 600

    start_time = time.time()
    tokens_used = 0
    iterations = 0

    while (iterations < max_iterations and 
        tokens_used < max_tokens and 
        time.time() - start_time < max_timeout_seconds):

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
        called_tools_set=set()
        tool_key_repeat_count = 0

        # handle responses
        for block in response.content:
            if block.type == "tool_use":
                #build hashable block for call
                used_tools=True 
                tool_key = f"{block.name}:{json.dumps(block.input, sort_keys=True)}"
                if tool_key in called_tools_set:
                    print(f"Repeated tool call with same args with {tool_key}")
                    tool_key_repeat_count += 1
                    if tool_key_repeat_count > 2:
                        print("Claude retrying same tool + args more than 2 times")
                        break
                else:
                    called_tools_set.add(tool_key)

                print(f"Tool call: {block.name}")
                print(f"Arguments: {block.input}")

                #execute tool
                result = await client.call_tool(block.name, block.input)
                print(f"Tool result: {result.text}")

                # Add to assistant content for this turn
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
                
                # Add tool result to memory
                memory.add_tool_result(block.id, result.text)

            elif block.type == "text":
                print(f"Claude: {block.text}")
                assistant_content.append({
                    "type": "text",
                    "text": block.text
                })
            else:
                print("Unknown block type: {block.type}")

        # Add assistant response to messages
        if assistant_content:
            memory.add_assistant_message(assistant_content)

        # Check if Claude is done (no tools repeated)
        if not used_tools:
            print("Claude finished - no tools used")
            break
        
    return memory

async def main():
    
    # connect to server
    client = Client("http://localhost:5000")

    # get prompt
    system_prompt = load_system_prompt()

    # list tools
    tools = await client.list_tools()

    # convert to anthropic tools
    anthropic_tools = []

    for tool in tools:
        anthropic_tools.append({
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        })
    
    #initialize memory and client
    memory = ConversationMemory()
    anthropic_client = AsyncAnthropic()

    # Example conversation
    user_input = input("Tell me what you want: ")
    memory.add_user_message(user_input)
    await chat_with_memory(client, anthropic_client, memory, anthropic_tools, system_prompt)

    # Print conversation history
    print("\n--- Conversation History ---")
    for i, msg in enumerate(memory.get_messages()):
        print(f"{i+1}. {msg['role']}: {msg['content']}")

if __name__ == "__main__":
    asyncio.run(main())