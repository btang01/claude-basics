import asyncio
import json
import time
from anthropic import AsyncAnthropic
from fastmcp import Client
from typing import List, Dict, Any, Type
from simple_weather_agent.models import ProfileInput, CityInput
from pydantic import BaseModel

class ConversationMemory:
    def __init__(self):
        # this is our conversation storage
        self.messages: List[Dict[str, Any]] = []
        self.metadata: List[Dict[str, Any]] = []

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

    def add_metadata(self, data: Dict[str, Any]):
        self.metadata.append(data)

    def get_messages(self) -> List[Dict[str, Any]]:
        # only share copy in order to protect original - can't just append
        return self.messages.copy()
    

class EntityMemory:
    def __init__(self):
        # primary key is id 'brian1'
        self.entities: Dict[str, Dict[str, Any]] = {}

    def hydrate_from_data(self, data: List[Dict[str, Any]]):
        """Load entities from a long-term JSON dataset."""
        for record in data:
            self.entities[record["id"]] = record
        
    def upsert(self, entity_id: str, key: str, value: Any):
        """Add or update an attribute for an entity."""
        if entity_id not in self.entities:
            self.entities[entity_id] = {"id": entity_id}
        self.entities[entity_id][key] = value 

    def add_note(self, entity_id: str, note: str):
        """Append a note to the entity's notes list."""
        if entity_id not in self.entities:
            self.entities[entity_id] = {"id": entity_id, "notes": [note]}
        else:
            self.entities[entity_id].setdefault("notes", []).append(note)

    def get(self, entity_id: str) -> Dict[str, Any]:
        """Retrieve a single entity by ID."""
        return self.entities.get(entity_id)

    def as_prompt_context(self, filter_by_name: str = None) -> str:
        """
        Generate a Claude-friendly string.
        Optionally filter by first_name to only show relevant entities.
        """
        lines = ["Known entities (use id or notes for disambiguation):"]
        for entity in self.entities.values():
            if filter_by_name and entity.get("first_name", "").lower() != filter_by_name.lower():
                continue

            parts = []
            for key in ["id", "first_name", "last_name", "department", "job_title"]:
                if entity.get(key):
                    parts.append(f"{key}: {entity[key]}")

            if entity.get("locations"):
                city = entity["locations"][0].get("city")
                if city:
                    parts.append(f"city: {city}")

            if entity.get("notes"):
                parts.append(f"notes: {', '.join(entity['notes'])}")
            lines.append(", ".join(parts))
        return "\n".join(lines)
    
    # lets us inspect entity with memory=new EntityMemory(), print memory instead of a memory address blob
    def __repr__(self):
        return f"Entity Memory({self.entities})"


class ToolUseBlock(BaseModel):
    type: str
    name: str
    id: str
    input: Dict[str, Any]

class ToolResult(BaseModel):
    data: str

def update_from_profile_input(block: ToolUseBlock, result: ToolResult, entity_memory: EntityMemory):
    profile = block.input.get("name")
    if profile:
        # Use a generated ID (e.g., lowercase name + 1)
        entity_id = f"{profile_name.lower()}1"
        entity_memory.upsert(entity_id, "first_name", profile_name)
        entity_memory.upsert(entity_id, "city", result.data.strip())
        print(f"Updated entity memory: {entity_memory.as_prompt_context()}")

TOOL_ENTITY_UPDATES = {
    "get_city_from_profile": update_from_profile_input
}

tool_model_map = {
    "get_city_from_profile": ProfileInput,
    "get_weather_from_city": CityInput
}

def enrich_tool_schema(tool: Any, model_class: Type[BaseModel]) -> Any:
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
                           entity_memory: EntityMemory,
                           anthropic_tools: List[Dict[str, Any]], 
                           system_prompt: str,
                           max_iterations: int = 25):
    
    # add some safeguards
    max_iterations = 30
    iterations = 0

    # outside loop, bounded by limits
    while iterations < max_iterations:

        # track safeguard progress
        iterations += 1
        
        # add memory
        messages = memory.get_messages()
        entity_memory_context = entity_memory.as_prompt_context()
        if entity_memory_context:
            messages.insert(0, {
                "role": "user",
                "content": entity_memory_context
            })

        # track assistant messages
        assistant_content = []

        # call Claude with information
        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            system=system_prompt,
            messages=messages,
            tools=anthropic_tools,
            max_tokens=1024 # 800 word response
        )

        # remember stop reasons, not used right now though
        print(f"Stop reason: {response.stop_reason}")
        memory.add_metadata({"stop_reason: {response.stop_reason}"})

        # handle responses
        for block in response.content:
            # Entity Memory check
            entity_memory_context = entity_memory.as_prompt_context()
            print(f"This is what's in my entity memory right now: {entity_memory_context} !!!")
            if block.type == "tool_use":

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
                try:
                    result = await client.call_tool(block.name, block.input)
                    print(f"Tool result: {result.data}")
                    memory.add_tool_result(block.id, result.data)

                except Exception as e:
                    print(f"Tool error: {e}")
                    memory.add_tool_result(block.id, f"error: {e}")
                    continue

                # update entity memory if necessary - returns function
                tool_updater = TOOL_ENTITY_UPDATES.get(block.name)
                if tool_updater:
                    tool_block = ToolUseBlock(
                        type = "tool_use",
                        name = block.name,
                        id = block.id, 
                        input = block.input
                    )
                    tool_updater(tool_block, ToolResult(data=result.data), entity_memory)

            elif block.type == "text":
                print(f"Claude: {block.text}")
                assistant_content.append({
                    "type": "text",
                    "text": block.text,
                })
            else:
                print(f"Unknown block type: {block.type}")

        # Add assistant response to messages
        if assistant_content:
            memory.add_assistant_message(assistant_content)

        # Exit conditions

        if response.stop_reason == "tool_use":
            continue

        elif response.stop_reason == "end_turn":
            user_input = input(f"\nYou: ")
            memory.add_user_message(user_input)
            if user_input.strip().lower()=="end conversation":
                print("User ended conversation")
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

        # used enriched to force mcp list_tools format to include description
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
        entity_memory = EntityMemory()
        #initialize anthropic client to talk to LLM
        anthropic_client = AsyncAnthropic()

        # Example conversation
        user_input = input("Ask me about person and I'll tell you about cities and weather related to them: ")
        memory.add_user_message(user_input)

        # run conversation - put in fastmcp client, claude client, memory, anthro tools, prompt
        final_memory = await chat_with_memory(client, 
                                              anthropic_client, 
                                              memory,
                                              entity_memory,
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