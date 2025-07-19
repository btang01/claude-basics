import asyncio
from fastmcp import Client
from anthropic import AsyncAnthropic

# main
async def main():
	# connect to server
	async with Client("http://localhost:8000/mcp/") as client:

		# get tools from server
		tools = await client.list_tools()

		# convert to anthropic format
		anthropic_tools = []

		# future, think about lightweight tool access service to filter tool access!
		# no need to patch all mcp servers for access, just central service

		# memory thought: store convo in dynamodb or something, process with category
		# hash category+user then think about pulling them with token limits as context into convos

		for tool in tools:
			anthropic_tools.append({
				"name": tool.name,
				"description": tool.description,
				"input_schema": tool.inputSchema # should be a proper dict/JSON
			})

		# load system prompt
		system_prompt = load_system_prompts()

		user_input = input("Tell me what you want: ")

		# call Claude
		anthropic_client = AsyncAnthropic()

		response = await anthropic_client.messages.create(
			model="claude-3-5-sonnet-20241022",
			system=system_prompt,
			messages=[{"role": "user", "content": user_input}],
			tools=anthropic_tools,
			max_tokens=1024
		)

		# handle tools calls - just print them
		for block in response.content:
			if block.type == "tool_use":
				print(f"Tool call: {block.name}")
				print(f"Arguments: {block.input}")

				result = await client.call_tool(block.name, block.input)

				print(f"Tool result: {result.data}")

			elif block.type == "text":
				print(f"Claude: {block.text}")
			
			else:
				print(f"Unknown block type: {block.type}")

#load the prompt
def load_system_prompts(path: str = "prompts/system_prompt.txt") -> str:
	with open(path, "r") as f:
		return f.read().strip()

if __name__ == "__main__":
	asyncio.run(main())