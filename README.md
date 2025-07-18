# Claude Basics - MCP Weather Assistant

A Python project demonstrating the Model Context Protocol (MCP) with Claude AI integration, featuring weather tools and conversation memory management.

## Project Overview

This project implements a complete MCP (Model Context Protocol) system with:
- **MCP Server**: Provides weather and user profile tools
- **Basic Client**: Simple one-turn interaction with Claude
- **Advanced Client**: Multi-turn conversations with memory management
- **Stock Agent**: Archived example of a stock market information agent

## Features

- Real-time weather information retrieval
- User profile-based location lookup
- Conversation memory and context management
- Tool call tracking and repetition prevention
- Multi-turn dialogue capabilities
- Safeguards against infinite loops and excessive API usage

## Project Structure

```
claude-basics/
├── simple-server.py          # MCP server with weather tools
├── simple-client.py          # Basic MCP client (single interaction)
├── simple-client-memory.py   # Advanced client with conversation memory
├── prompts/
│   └── system_prompt.txt     # System prompt for Claude
├── example_messages/
│   └── message.py           # Example message format structures
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

### Running the MCP Server

Start the weather server on localhost:8000:

```bash
python simple-server.py
```

The server provides two tools:
- `get_city_from_profile(profile)`: Get user's city from their profile
- `get_weather_from_city(city)`: Get weather information for a city

### Basic Client Usage

For single-turn interactions:

```bash
python simple-client.py
```

### Advanced Client with Memory

For multi-turn conversations with memory:

```bash
python simple-client-memory.py
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

## Memory Management

The advanced client (`simple-client-memory.py`) includes:

- **Conversation History**: Maintains complete dialogue context
- **Tool Call Tracking**: Prevents repetitive tool calls
- **Safety Limits**: 
  - Maximum 30 iterations per conversation
  - 100,000 token limit
  - 10-minute timeout
  - Maximum 3 identical tool calls

## System Prompt

The AI assistant is configured to:
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
```

## Development Notes

- The project uses FastMCP for the server implementation
- Claude 3.5 Sonnet is the default model
- Async/await pattern throughout for better performance
- Error handling and input validation included
- Mock data used for weather information (easily replaceable with real APIs)

## Archived Components

- `practice1_stock_agent.py`: Example implementation of a stock market information agent with tool usage patterns

## Requirements

- Python 3.7+
- fastmcp
- anthropic
- aiohttp

## License

This project is for educational and demonstration purposes.
