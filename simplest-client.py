from anthropic import AsyncAnthropic
import asyncio 

async def run_agent():

    tools = [
        {
            "name": "get_city_from_name",
            "description": "return the city that is associated with the provided name",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the person, e.g. brian"
                    }
                },
                "required": ["name"]
            }
        },
        {
            "name": "get_weather_from_city",
            "description": "return the weather associated with the provided city",
            "input_schema": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "the provided city e.g. boston"
                    }
                },
                "required": ["city"]
            }
        }
    ]

    # init LLM
    anthropic_client = AsyncAnthropic()
    input_text = input("enter a name: ")

    messages = [{"role": "user", "content": input_text}]
    system_prompt = load_system_prompt()

    max_iterations = 20
    iteration = 0

    while iteration < max_iterations:

        used_tool = False 

        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            system=system_prompt,
            messages=messages,
            tools=tools,
            max_tokens=1024
        )

        for block in response.content:
            if block.type == "tool_use":
                used_tool = True 

                if hasattr(block.input, "model_dump"):
                    tool_input = block.input.model_dump() # if it's pydantic-like object
                else:
                    tool_input = block.input # already a dict

                messages.append(
                    {
                        "role": "assistant",
                        "content": [{
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": tool_input
                        }]
                    })

                result = tool_runners[block.name](tool_input) # use tool runner, get function with param inputs
                
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    }]
                })

            elif block.type == "text":
                print(f"Claude: {block.text}")
                messages.append({
                    "role": "assistant",
                    "content": [{
                        "type": "text",
                        "text": block.text
                    }]
                })

        if response.stop_reason == "end_turn" or not used_tool:
            break

def load_system_prompt(path: str="prompts/system_prompt.txt"):
    with open(path, "r") as f:
        return f.read().strip()

tool_runners = {
    "get_city_from_name": lambda inp: get_city_from_name(**inp),
    "get_weather_from_city": lambda inp: get_weather_from_city(**inp)
}

def run_get_city(inp):
    return get_city_from_name(**inp)

def run_get_weather(inp):
    return get_weather_from_city(**inp)

def get_city_from_name(name: str) -> str:
    """return the city that is associated with the provided name"""
    try:
        data = [{"name": "Brian", "city": "Boston"}, 
        {"name": "Kristina", "city": "Portland"}]

        for block in data:
            if block["name"].lower() == name.lower():
                return block["city"]

        return "unknown name"

    except Exception as e:
        print(f"error: {str(e)}")
        return "error"

def get_weather_from_city(city: str) -> str:
    """return the weather associated with the provided city"""
    try:
        data = [{"city": "Boston", "weather": "70F, sunny"},
        {"city": "Portland", "weather": "85F, cloudy"}]

        for block in data:
            if block["city"].lower() == city.lower():
                return block["weather"]
        
        return "unknown city"
    except Exception as e:
        print(f"error: {str(e)}")
        return "error"

if __name__ == "__main__":
    asyncio.run(run_agent())