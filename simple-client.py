import asyncio
from fastmcp import Client
from anthropic import AsyncAnthropic

async def run_agent(user_input: str):

	async with Client("http://localhost:8000/mcp/") as client:
		
		# get tools
		tools = client.list_tools()
		anthropic_tools = []

		# get tools into anthropic format
		for tool in tools:
			anthropic_tools.append({
				"name": tool.name,
				"input_schema": tool.inputSchema
			})

		# load system prompt
		system_prompt = load_system_prompt()

		# may need memory - get core loop done
		user_input = input("enter something: ")
		messages = [{"role": "user", "content": user_input}]

		conversation_memory = ConversationMemory()
		entity_memory = EntityMemory()

		anthropic_client = AsyncAnthropic()

		max_iterations = 20
		iteration = 0

		while iteration < max_iterations:

			iteration += 1

			response = await anthropic_client.messages.create(
				model="claude-sonnet-4-20250514",
				system=system_prompt,
				messages=messages,
				tools=anthropic_tools,
				max_tokens=1024 # 800 word response
			)

			for block in response.content:
				if block.type == "tool_use":
					print(f"Tool Id: {block.id}")
					print(f"Tool name: {block.name}")
					print(f"Inputs: {block.input}")

					try:
						result = await client.call_tool(block.name, block.input)
						print(f"Results: {result.data}")

						messages.append[{
							"role": "user",
							"content": [{
								"type": "tool_result",
								"tool_use_id": block.id,
								"content": result.data
							}]
						}]
					except Exception as e:
						print(f"error: {str(e)}")
						continue

				elif block.type == "text":
					print(f"Claude: {block.text}")

				else:
					print(f"Unknown block type: {block.type}")

			if response.stop_reason == "end turn":
				break

def load_system_prompt(path: str="system_prompts/system_prompt.txt"):
	with open(path, "r") as f:
		f.read().strip()

if __name__ == "__main__":
	asyncio.run(main())