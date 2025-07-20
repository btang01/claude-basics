# Claude Basics - MCP Implementation Guide

A comprehensive Python project demonstrating Model Context Protocol (MCP) integration with Claude AI, featuring practical examples of memory management, tool usage, and conversation handling.

## Quick Start

```bash
# Setup
python3 -m venv claude-env
source claude-env/bin/activate  # macOS/Linux
pip install fastmcp anthropic aiohttp
export ANTHROPIC_API_KEY="your_key_here"

# Run server + client
python simple-server.py        # Terminal 1
python simple-client.py        # Terminal 2
```

## Project Components

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| `simple-server.py` | Basic MCP server | Weather tools, profile lookup |
| `simple-client.py` | Single-turn client | Basic tool usage |
| `simple-client-memory.py` | Multi-turn client | Full conversation memory |
| `medium-client.py` | Optimized client | Sliding window memory |
| `ConversationMemorySlidingWindow` | Memory class | Token-aware windowing |

## Core Patterns

### 1. MCP Server Setup
```python
from fastmcp import FastMCP

mcp = FastMCP("server_name")

@mcp.tool
async def my_tool(param: str) -> str:
    """Tool description for Claude"""
    return f"Result: {param}"

if __name__ == "__main__":
    mcp.run(transport="http", host="localhost", port=8000)
```

### 2. MCP Client Connection
```python
from fastmcp import Client
from anthropic import AsyncAnthropic

async with Client("http://localhost:8000/mcp/") as client:
    tools = await client.list_tools()
    
    # Convert to Anthropic format
    anthropic_tools = [{
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.inputSchema
    } for tool in tools]
```

### 3. Claude Integration
```python
anthropic_client = AsyncAnthropic()

response = await anthropic_client.messages.create(
    model="claude-3-5-sonnet-20241022",
    system=system_prompt,
    messages=messages,
    tools=anthropic_tools,
    max_tokens=1024
)
```

### 4. Tool Call Handling
```python
for block in response.content:
    if block.type == "tool_use":
        result = await client.call_tool(block.name, block.input)
        # Add tool result to conversation
    elif block.type == "text":
        print(f"Claude: {block.text}")
```

## Memory Management

### Basic Memory (All Messages)
```python
class ConversationMemory:
    def __init__(self):
        self.messages = []
    
    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})
    
    def get_messages(self):
        return self.messages.copy()
```

### Sliding Window Memory (Optimized)
```python
from classes.ConversationMemorySlidingWindow import ConversationMemorySlidingWindow

memory = ConversationMemorySlidingWindow()

# Get last 20 messages
recent = memory.get_recent_messages(window_size=20)

# Get messages within token limit
recent = memory.get_recent_messages_token_limit(token_limit=10000)
```

## Conversation Loop Pattern

```python
async def chat_with_memory(client, anthropic_client, memory, tools, system_prompt):
    max_iterations = 30
    iterations = 0
    
    while iterations < max_iterations:
        iterations += 1
        messages = memory.get_messages()  # or get_recent_messages()
        
        response = await anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            system=system_prompt,
            messages=messages,
            tools=tools,
            max_tokens=1024
        )
        
        used_tools = False
        for block in response.content:
            if block.type == "tool_use":
                used_tools = True
                # Execute tool and add results to memory
                result = await client.call_tool(block.name, block.input)
                memory.add_tool_result(block.id, result.data)
            elif block.type == "text":
                memory.add_assistant_message([{"type": "text", "text": block.text}])
        
        if not used_tools:
            break  # Conversation complete
    
    return memory
```

## Safety Mechanisms

### Tool Call Tracking
```python
global_called_tools = {}  # tool_key -> count

tool_key = f"{block.name}:{json.dumps(block.input, sort_keys=True)}"
if tool_key in global_called_tools:
    global_called_tools[tool_key] += 1
    if global_called_tools[tool_key] > 2:
        break  # Prevent infinite loops
```

### Resource Limits
```python
# Conversation safeguards
max_tokens = 100000
max_iterations = 30
max_timeout_seconds = 600
start_time = time.time()

# Check limits in loop
if (iterations >= max_iterations or 
    tokens_used >= max_tokens or 
    time.time() - start_time >= max_timeout_seconds):
    break
```

## System Prompt Template

```python
def load_system_prompt(path: str = "prompts/system_prompt.txt") -> str:
    with open(path, "r") as f:
        return f.read().strip()

# Example system prompt structure:
"""
You are a helpful AI assistant with access to tools.

## Your capabilities:
- Tool 1: Description
- Tool 2: Description

## Guidelines:
1. Always use available tools when appropriate
2. Be concise and clear
3. Handle errors gracefully
4. Limit repetitive tool calls

## Response style:
- Friendly and conversational
- Format information clearly
- Provide context when helpful
"""
```

## File Structure

```
claude-basics/
├── simple-server.py              # Basic MCP server
├── medium-server.py              # Enhanced server
├── simple-client.py              # Single-turn client
├── simple-client-memory.py       # Full memory client
├── medium-client.py              # Sliding window client
├── classes/
│   └── ConversationMemorySlidingWindow.py
├── simple_weather_agent/
│   ├── models.py                 # Data structures
│   └── tools.py                  # Tool implementations
├── prompts/
│   ├── system_prompt.txt
│   └── system_prompt2.txt
└── example_messages/
    └── message.py                # Message format examples
```

## Common Patterns

### Error Handling
```python
try:
    result = await client.call_tool(tool_name, tool_input)
    return result.data
except Exception as e:
    return f"Error: {str(e)}"
```

### Message Format
```python
# User message
{"role": "user", "content": "Hello"}

# Assistant with tool use
{"role": "assistant", "content": [
    {"type": "tool_use", "id": "123", "name": "tool_name", "input": {...}}
]}

# Tool result
{"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": "123", "content": "result"}
]}
```

### Token Estimation
```python
def rough_token_estimate(msg):
    content = msg.get("content", "")
    if isinstance(content, list):
        content_str = json.dumps(content)
    else:
        content_str = str(content)
    return len(content_str) // 4  # ~4 chars per token
```

## Testing Commands

```bash
# Test basic functionality
python simple-client.py

# Test memory management
python simple-client-memory.py

# Test sliding window
python medium-client.py

# Debug tools
python debug_tool.py
```

## Key Dependencies

```bash
pip install fastmcp      # MCP framework
pip install anthropic    # Claude API
pip install aiohttp      # Async HTTP
```

## Environment Variables

```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key"
# Optional: export OPENWEATHER_API_KEY="your_weather_key"
```

This project demonstrates practical MCP implementation patterns, memory optimization techniques, and robust conversation handling for AI assistant applications.
