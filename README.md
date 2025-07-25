# Claude Basics - MCP Implementation Reference Guide

Comprehensive reference for Claude AI + MCP integration patterns, progressing from simple hardcoded tools to sophisticated multi-turn conversations with entity tracking.

## Quick Start

```bash
# Setup environment
python3 -m venv claude-env
source claude-env/bin/activate
pip install fastmcp anthropic aiohttp
export ANTHROPIC_API_KEY="your_key"

# Run examples (choose based on complexity)
python simplest-client.py      # Hardcoded tools, no server
python simple-server.py        # Terminal 1: MCP server
python simple-client.py        # Terminal 2: Basic client

# Debug tools
python debug_tool.py           # Inspect available tools from server
```

## File Overview & Progression

### 1. simplest-client.py - No Server Required
- **Purpose**: Standalone client with hardcoded tools
- **Key Features**: 
  - Tools defined inline as dictionaries
  - Direct function calls via `tool_runners` mapping
  - No MCP server dependency
- **When to use**: Quick prototyping, learning the basics

### 2. simple-client.py - Basic MCP Integration
- **Purpose**: Client that connects to MCP server
- **Key Features**:
  - Dynamic tool discovery from server
  - Basic conversation loop
  - No memory persistence between runs
- **When to use**: Testing MCP server integration

### 3. simple-client-memory.py - Full Featured Client
- **Purpose**: Production-ready client with memory
- **Key Features**:
  - ConversationMemory for message history
  - EntityMemory for multi-person tracking
  - Tool result processing with entity updates
  - Stop reason based flow control
- **When to use**: Building conversational agents

### 4. medium-client.py - Token-Optimized Client
- **Purpose**: Client with sliding window memory
- **Key Features**:
  - ConversationMemorySlidingWindow for token management
  - Token-based and count-based windowing
  - Incomplete implementation (setup only)
- **When to use**: Long conversations with context limits

### 5. Server Implementations
- **simple-server.py**: Weather & city lookup tools
- **medium-server.py**: File I/O & web search tools

## Core Implementation Patterns

### Pattern 1: Simplest Client (No MCP Server)
```python
# simplest-client.py - Hardcoded tools without server
tools = [
    {
        "name": "get_city_from_name",
        "description": "return the city that is associated with the provided name",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the person"}
            },
            "required": ["name"]
        }
    }
]

# Tool implementation
def get_city_from_name(name: str) -> str:
    data = [{"name": "Brian", "city": "Boston"}]
    for block in data:
        if block["name"].lower() == name.lower():
            return block["city"]
    return "unknown name"

# Tool runners mapping
tool_runners = {
    "get_city_from_name": lambda inp: get_city_from_name(**inp)
}

# In conversation loop
result = tool_runners[block.name](tool_input)
```

### Pattern 2: MCP Server Setup
```python
# simple-server.py - FastMCP server
from fastmcp import FastMCP

mcp = FastMCP("weather_server")

@mcp.tool
async def get_city_from_name(name: str) -> str:
    """Get user's city from their first name"""
    # Enhanced with multiple people support
    data = [
        {"id": "brian1", "first_name": "Brian", "city": "Boston", 
         "notes": ["Works at AWS"]},
        {"id": "brian2", "first_name": "Brian", "city": "Seattle",
         "notes": ["Plays hockey with you"]}
    ]
    # Implementation
    return city

# Run server
mcp.run(transport="http", host="localhost", port=8000)
```

### Pattern 3: MCP Client Connection
```python
# Connect to MCP server and get tools
from fastmcp import Client
from anthropic import AsyncAnthropic

async with Client("http://localhost:8000/mcp/") as client:
    tools = await client.list_tools()
    
    # Convert MCP → Anthropic format
    anthropic_tools = [{
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.inputSchema
    } for tool in tools]
```

### Pattern 4: Enhanced Tool Schema (with Pydantic)
```python
# simple_weather_agent/models.py
from pydantic import BaseModel, Field

class NameInput(BaseModel):
    name: str = Field(..., description="The name e.g. brian")

# In client - enrich tool schemas
from simple_weather_agent.models import NameInput

for tool in anthropic_tools:
    if tool["name"] == "get_city_from_name":
        tool["input_schema"] = NameInput.model_json_schema()
```

### Pattern 5: Conversation Loop with Memory
```python
# Full conversation pattern with all features
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
        
        # Process response blocks
        assistant_content = []
        for block in response.content:
            if block.type == "tool_use":
                # Execute tool
                result = await client.call_tool(block.name, block.input)
                memory.add_tool_result(block.id, result.data)
                
                # Update entities based on tool results
                if block.name == "get_city_from_name":
                    name = block.input.get("name")
                    entity_id = f"{name.lower()}1"
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

## Memory Management Classes

### ConversationMemory (Basic)
```python
class ConversationMemory:
    def __init__(self):
        self.messages = []
        self.metadata = []
    
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
    
    def get_messages(self) -> List[Dict]:
        return self.messages.copy()
```

### ConversationMemorySlidingWindow (Token-Aware)
```python
class ConversationMemorySlidingWindow:
    def __init__(self):
        self.messages = []
    
    def get_recent_messages(self, window_size: int = 10):
        """Get last N messages"""
        return self.messages[-window_size:] if self.messages else []
    
    def get_recent_messages_token_limit(self, token_limit: int = 10000):
        """Get messages within token budget"""
        if not self.messages:
            return []
        
        recent_messages = []
        total_tokens = 0
        
        # Iterate backwards
        for msg in reversed(self.messages):
            msg_tokens = self.rough_token_estimate(msg)
            if total_tokens + msg_tokens > token_limit:
                break
            recent_messages.insert(0, msg)
            total_tokens += msg_tokens
        
        return recent_messages
    
    @staticmethod
    def rough_token_estimate(msg):
        """Estimate tokens as chars/4"""
        content = msg.get("content", "")
        if isinstance(content, list):
            content_str = json.dumps(content)
        else:
            content_str = str(content)
        return len(content_str) // 4
```

### EntityMemory (Multi-Person Tracking)
```python
class EntityMemory:
    def __init__(self):
        self.entities = {}  # id -> entity data
    
    def hydrate_from_data(self, data: List[Dict]):
        """Load from data source"""
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
        """Generate context for Claude"""
        lines = ["Known entities (use id or notes for disambiguation):"]
        
        for entity in self.entities.values():
            if filter_by_name and entity.get("first_name", "").lower() != filter_by_name.lower():
                continue
            
            parts = []
            for key in ["id", "first_name", "last_name", "department", "job_title"]:
                if entity.get(key):
                    parts.append(f"{key}: {entity[key]}")
            
            if entity.get("notes"):
                parts.append(f"notes: {', '.join(entity['notes'])}")
            
            lines.append(", ".join(parts))
        
        return "\n".join(lines)
```

## Message Format Reference

```python
# User message
{"role": "user", "content": "What's the weather for Brian?"}

# Assistant with tool use
{
    "role": "assistant",
    "content": [
        {
            "type": "tool_use",
            "id": "toolu_123abc",
            "name": "get_city_from_name",
            "input": {"name": "Brian"}
        }
    ]
}

# Tool result
{
    "role": "user",
    "content": [{
        "type": "tool_result",
        "tool_use_id": "toolu_123abc",
        "content": "Boston"
    }]
}

# Assistant text response
{
    "role": "assistant",
    "content": [{
        "type": "text",
        "text": "Brian is in Boston. Let me check the weather there."
    }]
}
```

## Common Patterns & Best Practices

### 1. Tool Execution Pattern
```python
# Simplest (hardcoded tools)
result = tool_runners[block.name](tool_input)

# MCP Client
result = await client.call_tool(block.name, block.input)
print(f"Result: {result.data}")
```

### 2. Stop Reason Flow Control
```python
# Modern pattern (Claude 4)
if response.stop_reason == "tool_use":
    continue  # More tools needed
elif response.stop_reason == "end_turn":
    # Await user input or break
```

### 3. Entity Update Pattern
```python
# Define tool-to-update mapping
TOOL_ENTITY_UPDATES = {
    "get_city_from_name": update_from_profile_input
}

# Update function
def update_from_profile_input(block: ToolUseBlock, result: ToolResult, entity_memory: EntityMemory):
    name = block.input.get("name")
    entity_id = f"{name.lower()}1"
    entity_memory.upsert(entity_id, "first_name", name)
    entity_memory.upsert(entity_id, "city", result.data.strip())
```

### 4. System Prompt Loading
```python
def load_system_prompt(path: str = "prompts/system_prompt.txt") -> str:
    with open(path, "r") as f:
        return f.read().strip()

# Use in Claude call
system_prompt = load_system_prompt()
```

### 5. Error Handling
```python
try:
    result = await client.call_tool(block.name, block.input)
    memory.add_tool_result(block.id, result.data)
except Exception as e:
    memory.add_tool_result(block.id, f"Error: {str(e)}")
```

## Debugging & Testing

### Debug Available Tools
```python
# debug_tool.py - Inspect MCP server tools
async def debug_tools():
    async with Client("http://localhost:8000/mcp/") as client:
        tools = await client.list_tools()
        
        for tool in tools:
            print(f"\n=== Tool: {tool.name} ===")
            print(f"Description: {tool.description}")
            pprint.pprint(tool.inputSchema)
```

### Testing Progression
1. **simplest-client.py** - Test basic flow without server
2. **simple-client.py** - Test MCP integration
3. **simple-client-memory.py** - Test full conversation with memory
4. **medium-client.py** - Test token management (setup only)

## Project Structure
```
claude-basics/
├── simplest-client.py            # Standalone client (no server)
├── simple-server.py              # Basic MCP server
├── simple-client.py              # Basic MCP client
├── simple-client-memory.py       # Client with full memory
├── medium-server.py              # Advanced server with file I/O
├── medium-client.py              # Token-optimized client
├── debug_tool.py                 # Tool inspection utility
├── classes/
│   └── ConversationMemorySlidingWindow.py
├── simple_weather_agent/
│   ├── models.py                 # Pydantic models
│   └── tools.py                  # Tool implementations
├── prompts/
│   ├── system_prompt.txt
│   └── system_prompt2.txt
└── example_messages/
    └── message.py                # Message format examples
```

## Key Configuration

### Environment Variables
```bash
export ANTHROPIC_API_KEY="your_api_key"
```

### Model Selection
```python
model="claude-sonnet-4-20250514"  # Latest Claude 4
```

### Common Parameters
- `max_tokens`: 1024 (typical for ~800 word responses)
- `max_iterations`: 30 (prevent infinite loops)
- Token estimation: ~4 characters per token

## Troubleshooting

### Tool Not Found
- Check server is running: `python simple-server.py`
- Verify URL: `http://localhost:8000/mcp/`
- Use `debug_tool.py` to inspect available tools

### Memory Issues
- Use sliding window for long conversations
- Monitor token usage with `rough_token_estimate()`
- Clear old messages periodically

### Entity Confusion
- Use unique IDs (e.g., "brian1", "brian2")
- Add disambiguation notes
- Filter context by name when appropriate

### Stop Reason Handling
- Always check `response.stop_reason`
- "tool_use" → Continue loop
- "end_turn" → Await input or exit
- "max_tokens" → Consider shorter responses

---

This guide progresses from simple hardcoded tools to sophisticated conversation management with entity tracking and token optimization. Start with `simplest-client.py` to understand the basics, then progress through the examples as your needs grow more complex.