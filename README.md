# Claude Basics - MCP Cheat Sheet & Implementation Guide

Quick reference guide for Claude AI + MCP integration with real-world patterns for memory management, tool usage, and multi-person entity tracking.

## Quick Reference

### Essential Commands
```bash
# Setup
python3 -m venv claude-env
source claude-env/bin/activate
pip install fastmcp anthropic aiohttp
export ANTHROPIC_API_KEY="your_key"

# Run (2 terminals)
python simple-server.py        # Terminal 1: MCP server
python simple-client.py        # Terminal 2: Client
```

### Key Files to Know
- `simple-server.py` - Basic MCP server with tools
- `simple-client.py` - Single request/response
- `simple-client-memory.py` - Multi-turn conversations with entity tracking
- `medium-client.py` - Sliding window memory (token-efficient)

### Model & Stop Reasons
```python
model="claude-sonnet-4-20250514"  # Latest Claude 4

# Stop reasons:
# "tool_use" → Claude needs to call more tools
# "end_turn" → Claude finished, await user input
# "max_tokens" → Hit token limit
```

## Core Implementation Patterns

### 1. MCP Server Quick Setup
```python
from fastmcp import FastMCP

mcp = FastMCP("weather_server")

@mcp.tool
async def get_city_from_name(name: str) -> str:
    """Get user's city from their first name"""
    # Tool implementation
    return city

mcp.run(transport="http", host="localhost", port=8000)
```

### 2. Client Connection Pattern
```python
from fastmcp import Client
from anthropic import AsyncAnthropic

# Connect to MCP server
async with Client("http://localhost:8000/mcp/") as client:
    tools = await client.list_tools()
    
    # Convert MCP → Anthropic format
    anthropic_tools = [{
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.inputSchema
    } for tool in tools]
```

### 3. Claude API Call (Updated for Claude 4)
```python
anthropic_client = AsyncAnthropic()

response = await anthropic_client.messages.create(
    model="claude-sonnet-4-20250514",  # Claude 4
    system=system_prompt,
    messages=messages,
    tools=anthropic_tools,
    max_tokens=1024
)

# Check stop reason for flow control
print(f"Stop reason: {response.stop_reason}")
```

### 4. Response Handling Pattern
```python
assistant_content = []

for block in response.content:
    if block.type == "tool_use":
        # Execute tool
        result = await client.call_tool(block.name, block.input)
        memory.add_tool_result(block.id, result.data)
        
        # Track for entity updates
        assistant_content.append({
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input
        })
        
    elif block.type == "text":
        print(f"Claude: {block.text}")
        assistant_content.append({
            "type": "text",
            "text": block.text
        })

# Add complete assistant response to memory
memory.add_assistant_message(assistant_content)
```

## Memory Systems

### Basic Conversation Memory
```python
class ConversationMemory:
    def __init__(self):
        self.messages = []
        self.metadata = []  # Track stop_reasons, etc.
    
    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content: List[Dict]):
        self.messages.append({"role": "assistant", "content": content})
    
    def add_tool_result(self, tool_use_id: str, result: str):
        self.messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result
            }]
        })
```

### Entity Memory (Multi-Person Tracking)
```python
class EntityMemory:
    def __init__(self):
        self.entities = {}  # id -> full entity data
    
    def hydrate_from_data(self, data: List[Dict]):
        """Load from database/JSON"""
        for record in data:
            self.entities[record["id"]] = record
    
    def upsert(self, entity_id: str, key: str, value: Any):
        """Update entity attributes"""
        if entity_id not in self.entities:
            self.entities[entity_id] = {"id": entity_id}
        self.entities[entity_id][key] = value
    
    def add_note(self, entity_id: str, note: str):
        """Add disambiguation notes"""
        self.entities[entity_id].setdefault("notes", []).append(note)
    
    def as_prompt_context(self, filter_by_name: str = None) -> str:
        """Generate Claude-friendly context"""
        lines = ["Known entities (use id or notes for disambiguation):"]
        
        for entity in self.entities.values():
            if filter_by_name and entity.get("first_name", "").lower() != filter_by_name.lower():
                continue
                
            # Build entity description
            parts = []
            for key in ["id", "first_name", "last_name", "department", "job_title"]:
                if entity.get(key):
                    parts.append(f"{key}: {entity[key]}")
            
            if entity.get("notes"):
                parts.append(f"notes: {', '.join(entity['notes'])}")
                
            lines.append(", ".join(parts))
        
        return "\n".join(lines)
```

## Conversation Loop (Updated Pattern)

```python
async def chat_with_memory(client, anthropic_client, memory, entity_memory, tools, system_prompt):
    max_iterations = 30
    iterations = 0
    
    while iterations < max_iterations:
        iterations += 1
        
        # Get messages and add entity context
        messages = memory.get_messages()
        entity_context = entity_memory.as_prompt_context()
        
        if entity_context:
            messages.append({
                "role": "user",
                "content": entity_context
            })
        
        # Call Claude 4
        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            system=system_prompt,
            messages=messages,
            tools=tools,
            max_tokens=1024
        )
        
        # Track metadata
        memory.add_metadata({"stop_reason": response.stop_reason})
        
        # Process response
        assistant_content = []
        for block in response.content:
            if block.type == "tool_use":
                # Execute tool
                result = await client.call_tool(block.name, block.input)
                memory.add_tool_result(block.id, result.data)
                
                # Update entities if needed
                if block.name == "get_city_from_name":
                    name = block.input.get("name")
                    entity_id = f"{name.lower()}1"  # Simple ID generation
                    entity_memory.upsert(entity_id, "first_name", name)
                    entity_memory.upsert(entity_id, "city", result.data)
                
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
                
            elif block.type == "text":
                assistant_content.append({
                    "type": "text",
                    "text": block.text
                })
        
        # Save assistant response
        if assistant_content:
            memory.add_assistant_message(assistant_content)
        
        # Flow control based on stop_reason
        if response.stop_reason == "tool_use":
            continue  # Claude needs more tools
        elif response.stop_reason == "end_turn":
            # Get user input
            user_input = input("\nYou: ")
            if user_input.lower() == "end conversation":
                break
            memory.add_user_message(user_input)
    
    return memory
```

## Message Format Reference

```python
# User message
{"role": "user", "content": "What's the weather in Boston?"}

# Assistant with tool use
{
    "role": "assistant",
    "content": [
        {
            "type": "tool_use",
            "id": "toolu_123abc",
            "name": "get_weather",
            "input": {"location": "Boston"}
        }
    ]
}

# Tool result (MCP: result.data, Direct: block["content"][0]["content"])
{
    "role": "user",
    "content": [{
        "type": "tool_result",
        "tool_use_id": "toolu_123abc",
        "content": "Boston: 72°F, sunny"
    }]
}

# Assistant text response
{
    "role": "assistant",
    "content": [{
        "type": "text",
        "text": "The weather in Boston is 72°F and sunny!"
    }]
}
```

## Tool Implementation Example

```python
@mcp.tool
async def get_city_from_name(name: str) -> str:
    """Get city from first name - handles multiple people with same name"""
    
    # Sample data with multiple Brians
    data = [
        {
            "id": "brian1",
            "first_name": "Brian",
            "last_name": "Wang",
            "department": "Engineering",
            "locations": [{"city": "Boston", "state": "MA"}],
            "notes": ["Works at AWS", "Leads cloud migration"]
        },
        {
            "id": "brian2", 
            "first_name": "Brian",
            "last_name": "Johnson",
            "department": "Marketing",
            "locations": [{"city": "Seattle", "state": "WA"}],
            "notes": ["Plays hockey with you"]
        }
    ]
    
    # Find matching person
    name = name.strip().lower()
    for record in data:
        if record["first_name"].lower() == name:
            return record["locations"][0]["city"]
    
    raise ValueError(f"Name '{name}' not found")
```

## Common Pitfalls & Solutions

### 1. Tool Result Format
```python
# Wrong - Missing tool result structure
memory.add_assistant_message(result.data)

# Correct - Proper tool result format
memory.add_tool_result(block.id, result.data)
```

### 2. Stop Reason Handling
```python
# Old pattern - Manual tracking
used_tools = False
if block.type == "tool_use":
    used_tools = True
if not used_tools:
    break

# New pattern - Use stop_reason
if response.stop_reason == "tool_use":
    continue
elif response.stop_reason == "end_turn":
    # Handle user input
```

### 3. Entity Memory Updates
```python
# Wrong - Overwriting entire entity
entity_memory.entities[name] = city

# Correct - Structured updates
entity_id = f"{name.lower()}1"
entity_memory.upsert(entity_id, "first_name", name)
entity_memory.upsert(entity_id, "city", city)
```

### 4. Message Content Format
```python
# Wrong - String content for assistant with tools
{"role": "assistant", "content": "Using tool..."}

# Correct - List format for content blocks
{"role": "assistant", "content": [
    {"type": "tool_use", "id": "123", "name": "tool", "input": {}}
]}
```

## Testing Checklist

```bash
# 1. Basic tool test
python simple-client.py
# Expected: Single tool call and response

# 2. Memory conversation test  
python simple-client-memory.py
# Expected: Multi-turn conversation with entity tracking

# 3. Sliding window test
python medium-client.py
# Expected: Efficient memory management

# 4. Debug specific tools
python debug_tool.py
```

## Project Structure
```
claude-basics/
├── simple-server.py              # MCP server with tools
├── simple-client.py              # Basic client (single turn)
├── simple-client-memory.py       # Full memory + entities
├── medium-client.py              # Sliding window memory
├── classes/
│   └── ConversationMemorySlidingWindow.py
├── simple_weather_agent/
│   ├── models.py                 # Pydantic models
│   └── tools.py                  # Tool implementations
├── prompts/
│   ├── system_prompt.txt         # Basic prompt
│   └── system_prompt2.txt        # Enhanced prompt
└── example_messages/
    └── message.py                # Message format examples
```

## Key Takeaways

1. **Claude 4 Model**: Use `claude-sonnet-4-20250514`
2. **Stop Reasons**: Control flow with `response.stop_reason`
3. **Entity Memory**: Track multiple people with same names using IDs and notes
4. **Tool Results**: Always use proper tool_result format
5. **Message Format**: Assistant responses with tools must use list format
6. **Memory Context**: Add entity context as user message before Claude call

---

Ready for testing? Start with `python simple-server.py` in one terminal and `python simple-client.py` in another!