# Claude Basics - MCP Implementation Guide

Practical patterns for building Claude AI agents with MCP (Model Context Protocol), from standalone tools to sophisticated conversation management.

## Quick Start

```bash
# Environment setup
python3 -m venv claude-env
source claude-env/bin/activate
pip install fastmcp anthropic aiohttp
export ANTHROPIC_API_KEY="your_key"

# Choose your starting point
python simplest-client.py        # Weather agent (no server)
python simplest-client-stocks.py # Stock agent (no server)
python simple-server.py          # Terminal 1: MCP server
python simple-client.py          # Terminal 2: MCP client
```

## Implementation Progression

### Level 1: Standalone Agents (No Server)
Start here to understand tool calling without complexity.

**simplest-client.py** - Weather & location agent
```python
tools = [{
    "name": "get_city_from_name",
    "description": "return the city associated with the name",
    "input_schema": {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"]
    }
}]

# Direct function mapping
tool_runners = {
    "get_city_from_name": lambda inp: get_city_from_name(**inp)
}

# Tool result format (latest)
messages.append({
    "role": "user",
    "content": [{
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": [{
            "type": "text",
            "text": result
        }]
    }]
})
```

**simplest-client-stocks.py** - Financial agent
```python
# Three stock tools: yesterday's price, today's price, latest news
tools = [
    {
        "name": "get_stock_price_today",
        "description": "returns current stock price",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker_name": {"type": "string", "description": "e.g. AAPL, AMZN"}
            },
            "required": ["ticker_name"]
        }
    }
]

# JSON serialization for results
result = tool_runners[block.name](tool_input)
content = json.dumps(result)  # Serialize numeric/complex data
```

### Level 2: MCP Server Integration
Connect to external tool servers for dynamic capabilities.

**simple-server.py** + **simple-client.py**
```python
# Server: Define tools with FastMCP
@mcp.tool
async def get_city_from_name(name: str) -> str:
    """Get user's city - handles multiple people"""
    data = [
        {"id": "brian1", "first_name": "Brian", "city": "Boston"},
        {"id": "brian2", "first_name": "Brian", "city": "Seattle"}
    ]
    # Return city for matching name

# Client: Connect and discover tools
async with Client("http://localhost:8000/mcp/") as client:
    tools = await client.list_tools()
    
    # Convert MCP → Anthropic format
    anthropic_tools = [{
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.inputSchema
    } for tool in tools]
    
    # Execute tools via MCP
    result = await client.call_tool(block.name, block.input)
```

### Level 3: Conversation Memory
Add state management for multi-turn conversations.

**simple-client-memory.py** - Full conversation tracking
```python
# Initialize memory systems
memory = ConversationMemory()        # Message history
entity_memory = EntityMemory()       # Track people/entities

# Main conversation loop
while iterations < max_iterations:
    # Add entity context to messages
    messages = memory.get_messages()
    if entity_context := entity_memory.as_prompt_context():
        messages.append({"role": "user", "content": entity_context})
    
    # Claude 4 call
    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        system=system_prompt,
        messages=messages,
        tools=tools,
        max_tokens=1024
    )
    
    # Process based on stop_reason
    if response.stop_reason == "tool_use":
        continue  # More tools needed
    elif response.stop_reason == "end_turn":
        user_input = input("\nYou: ")
        memory.add_user_message(user_input)
```

### Level 4: Token Optimization
Manage long conversations with sliding windows.

**medium-client.py** + **ConversationMemorySlidingWindow**
```python
memory = ConversationMemorySlidingWindow()

# Get recent messages by count
recent = memory.get_recent_messages(window_size=20)

# Or by token limit
recent = memory.get_recent_messages_token_limit(token_limit=10000)

# Token estimation: ~4 chars per token
def rough_token_estimate(msg):
    content = json.dumps(msg.get("content", ""))
    return len(content) // 4
```

## Core Patterns

### Message Format (Latest)
```python
# Tool result with nested content structure
{
    "role": "user",
    "content": [{
        "type": "tool_result",
        "tool_use_id": "toolu_123",
        "content": [{
            "type": "text",
            "text": "Result text or JSON"
        }]
    }]
}

# Assistant text response
{
    "role": "assistant",
    "content": [{
        "type": "text",
        "text": "Response text"
    }]
}
```

### Memory Classes

**ConversationMemory** - Basic message tracking
```python
memory.add_user_message("Hello")
memory.add_assistant_message([{"type": "text", "text": "Hi!"}])
memory.add_tool_result(tool_id, result)
messages = memory.get_messages()
```

**EntityMemory** - Multi-person disambiguation
```python
# Track multiple people with same name
entity_memory.upsert("brian1", "first_name", "Brian")
entity_memory.upsert("brian1", "city", "Boston")
entity_memory.add_note("brian1", "Works at AWS")

# Generate context for Claude
context = entity_memory.as_prompt_context(filter_by_name="Brian")
```

### Tool Patterns

**Pattern 1: Direct mapping (simplest)**
```python
tool_runners = {
    "tool_name": lambda inp: function_name(**inp)
}
result = tool_runners[block.name](tool_input)
```

**Pattern 2: MCP client (dynamic)**
```python
result = await client.call_tool(block.name, block.input)
print(f"Result: {result.data}")
```

**Pattern 3: Entity updates**
```python
TOOL_ENTITY_UPDATES = {
    "get_city_from_name": lambda block, result, em: 
        em.upsert(f"{block.input['name']}1", "city", result.data)
}
```

## Key Configuration

```python
# Model
model = "claude-sonnet-4-20250514"

# Common parameters
max_tokens = 1024        # ~800 words
max_iterations = 30      # Prevent infinite loops

# Stop reasons
"tool_use"   → Continue loop
"end_turn"   → Await input
"max_tokens" → Hit limit
```

## File Reference

| File | Purpose | Key Feature |
|------|---------|-------------|
| `simplest-client.py` | Weather agent | No server needed |
| `simplest-client-stocks.py` | Stock agent | Financial tools |
| `simple-client.py` | Basic MCP client | Server connection |
| `simple-client-memory.py` | Full conversation | Memory + entities |
| `medium-client.py` | Token management | Sliding window |
| `debug_tool.py` | Tool inspection | Debug MCP tools |

## Quick Debugging

```bash
# Check available tools
python debug_tool.py

# Common issues
- Server not running → Start simple-server.py first
- Tool not found → Check tool name matches exactly
- Memory overflow → Use sliding window
- Entity confusion → Add disambiguation notes
```

## Project Structure
```
claude-basics/
├── simplest-*.py                 # Standalone agents
├── simple-*.py                   # MCP integration
├── medium-*.py                   # Advanced features
├── classes/                      # Memory implementations
├── simple_weather_agent/         # Tool definitions
└── prompts/                      # System prompts
```

Start with the simplest examples and progress as needed. Each level builds on the previous while remaining self-contained for easy understanding.