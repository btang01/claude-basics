from fastmcp import Client
from anthropic import AsyncAnthropic
from classes.ConversationMemorySlidingWindow import ConversationMemorySlidingWindow
import asyncio


async def main():
    async with Client("http://localhost:8000/mcp/") as client:

        tools = await client.list_tools()

        # optional: filter tools through downstream access control MCP server
        # enforce claims, env, user role
        """
        async with Client("http://localhost:5000/mcp/") as downstream:
            response = await downstream.call_tool("filter_allowed_tools", {"tools": tools})
            tools = response.data
        """

        anthropic_tools = []
        
        for tool in tools:
            anthropic_tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            })
        
        system_prompt = load_system_prompt()
        anthropic_client = AsyncAnthropic()
        memory = ConversationMemorySlidingWindow()
        user_input = input("Tell me who you think OpenAI CEO is: ")
        memory.add_user_message(user_input)

        final_memory = await chat_with_memory(client,
                                              system_prompt,
                                              memory,
                                              anthropic_tools,
                                              anthropic_client)
        
        # Print conversation history
        print("\n--- Conversation History ---")
        for i, msg in enumerate(final_memory.get_messages()):
            print(f"{i+1}. {msg['role']}: {msg['content']}")

async def chat_with_memory(client: Client,
                           system_prompt: str,
                           memory: ConversationMemorySlidingWindow,
                           anthropic_tools: List[Dict[str, Any]],
                           anthropic_client: AsyncAnthropic):

    messages = memory.get_messages()

    global_called_tools = {}
    
    response = await anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        system=system_prompt,
        messages = messages,
        tools=anthropic_tools,
        max_tokens=1024
    )

def load_system_prompt(path: str="prompts/system_prompt2.txt") -> str:
    with open(path, "r") as f:
        return f.read().strip()
    
if __name__=="__main__":
    asyncio.run(main())