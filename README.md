# Claude Basics - MCP Weather Assistant

A Python project demonstrating the Model Context Protocol (MCP) with Claude AI integration, featuring weather tools, conversation memory management, and sliding window memory optimization.

## Project Overview

This project implements a complete MCP (Model Context Protocol) system with:
- **MCP Server**: Provides weather and user profile tools
- **Basic Client**: Simple one-turn interaction with Claude
- **Advanced Client**: Multi-turn conversations with memory management
- **Medium Client**: Intermediate client with sliding window memory integration
- **Sliding Window Memory**: Optimized memory management for long conversations
- **Weather Agent**: Modular weather tools and models
- **Stock Agent**: Archived example of a stock market information agent

## Features

- Real-time weather information retrieval
- User profile-based location lookup
- Conversation memory and context management
- Sliding window memory optimization for token efficiency
- Tool call tracking and repetition prevention
- Multi-turn dialogue capabilities
- Safeguards against infinite loops and excessive API usage
- Modular architecture with reusable components

## Project Structure

```
claude-basics/
├── simple-server.py          # MCP server with weather tools
├── medium-server.py          # Enhanced MCP server
├── simple-client.py          # Basic MCP client (single interaction)
├── simple-client-memory.py   # Advanced client with conversation memory
├── medium-client.py          # Client with sliding window memory integration
├── debug_tool.py            # Debugging utilities
├── classes/
│   ├── __init__.py
│   └── ConversationMemorySlidingWindow.py  # Sliding window memory class
├── simple_weather_agent/
│   ├── __init__.py
│   ├── models.py            # Weather data models
│   └── tools.py             # Weather tool implementations
├── prompts/
│   ├── system_prompt.txt    # System prompt for Claude
│   └── system_prompt2.txt   # Alternative system prompt
├── example_messages/
│   └── message.py           # Example message format structures
├── files/
│   └── ceo.txt             # Sample data file
├── archive/
│   └── practice1_stock_agent.py  # Stock market agent example
└── claude-env/              # Python virtual environment
```

## Setup

### 1. Create Virtual Environment

```bash
python3 -m venv claude-env
```

### 2. Activate Environment

**macOS/Linux:**
```bash
source claude-env/bin/activate
```

**Windows:**
```bash
claude-env\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install fastmcp anthropic aiohttp
```

### 4. Set Environment Variables

Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY="your_api_key_here"
```

## Usage

### Running the MCP Servers

Start the basic weather server on localhost:8000:
```bash
python simple-server.py
```

Or start the enhanced server:
```bash
python medium-server.py
```

The servers provide tools for:
- `get_city_from_profile(profile)`: Get user's city from their profile
- `get_weather_from_city(city)`: Get weather information for a city

### Client Options

#### Basic Client (Single-turn)
For simple one-time interactions:
```bash
python simple-client.py
```

#### Advanced Client (Full Memory)
For multi-turn conversations with complete memory:
```bash
python simple-client-memory.py
```

#### Medium Client (Sliding Window Memory)
For optimized multi-turn conversations with sliding window memory:
```bash
python medium-client.py
```

## Memory Management Systems

### Basic Memory (`simple-client-memory.py`)
- **Complete History**: Stores all conversation messages
- **Tool Call Tracking**: Prevents repetitive tool calls
- **Safety Limits**: Token, iteration, and time constraints

### Sliding Window Memory (`ConversationMemorySlidingWindow`)
- **Window by Count**: Keep last N messages (default: 20)
- **Window by Tokens**: Keep messages within token limit (default: 10,000)
- **Token Estimation**: Rough heuristic for message size calculation
- **Memory Efficiency**: Automatically manages context size for long conversations

#### Sliding Window Methods:
```python
# Get recent messages by count
memory.get_recent_messages(window_size=20)

# Get recent messages by token limit
memory.get_recent_messages_token_limit(token_limit=10000)

# Get all messages (traditional approach)
memory.get_messages()
```

## Available Tools

### Weather Tools

1. **get_city_from_profile**
   - Input: User profile name (string)
   - Output: City associated with the profile
   - Supported profiles: "brian" (Boston), "jocelyn" (San Francisco)

2. **get_weather_from_city**
   - Input: City name (string)
   - Output: Current weather conditions
   - Supported cities: Boston, San Francisco

## Modular Components

### Weather Agent (`simple_weather_agent/`)
- **models.py**: Data structures for weather information
- **tools.py**: Weather tool implementations
- **Reusable**: Can be imported into different client implementations

### Memory Classes (`classes/`)
- **ConversationMemorySlidingWindow**: Optimized memory management
- **Token-aware**: Estimates message sizes for efficient windowing
- **Flexible**: Supports both count-based and token-based windowing

## System Prompts

The AI assistant can be configured with different prompts:
- **system_prompt.txt**: Basic weather assistant configuration
- **system_prompt2.txt**: Enhanced prompt for advanced interactions

Key behaviors:
- Use available tools for weather and user information
- Determine user location from profiles when needed
- Provide clear, formatted responses
- Handle errors transparently
- Limit repetitive tool usage

## Example Interactions

```
User: "What's the weather like?"
Assistant: [Uses get_city_from_profile if user is known, then get_weather_from_city]

User: "What's the weather in Boston?"
Assistant: [Directly calls get_weather_from_city with "Boston"]

User: "Tell me more about the weather patterns"
Assistant: [Continues conversation using sliding window memory for context]
```

## Development Notes

- **FastMCP**: Server implementation framework
- **Claude 3.5 Sonnet**: Default language model
- **Async/await**: Throughout for better performance
- **Error Handling**: Comprehensive input validation and error management
- **Mock Data**: Weather information (easily replaceable with real APIs)
- **Modular Design**: Reusable components and clear separation of concerns
- **Memory Optimization**: Sliding window approach for long conversations

## Safety Features

- **Token Limits**: Prevent excessive API usage
- **Iteration Limits**: Avoid infinite conversation loops
- **Timeout Protection**: Maximum conversation duration
- **Tool Call Tracking**: Prevent repetitive identical calls
- **Memory Management**: Automatic context size optimization

## Archived Components

- `practice1_stock_agent.py`: Example implementation of a stock market information agent with tool usage patterns

## Requirements

- Python 3.7+
- fastmcp
- anthropic
- aiohttp

## License

This project is for educational and demonstration purposes.
