from anthropic import AsyncAnthropic
import asyncio
import json

async def run_agent():

    tools = [
        {
            "name": "get_stock_price_yesterday",
            "description": "returns price of stock at market close yesterday given the stock ticker name",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker_name": {
                        "type": "string",
                        "description": "name of the stock ticker e.g. meta, pltr"
                    }
                }, 
                "required": ["ticker_name"]
            }
        },
        {
            "name": "get_stock_price_today",
            "description": "returns price of stock today right now, given the stock ticker name",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker_name": {
                        "type": "string",
                        "description": "name of the stock ticker e.g. goog, tsla"
                    }
                },
                "required": ["ticker_name"]
            }
        },
        {
            "name": "get_latest_stock_news",
            "description": "returns latest news related to the stock ticker name",
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker_name": {
                        "type": "string",
                        "description": "news information related to the stock ticker value e.g. big drop in price today"
                    }
                },
                "required": ["ticker_name"]
            }
        },
    ]

    # prep messages, prompt, LLM call
    messages = []
    input_prompt = input("Enter a stock ticker and ask about prices and news: ")
    messages.append({"role": "user", "content": input_prompt})

    system_prompt = load_system_prompt()

    anthropic_client = AsyncAnthropic()

    # loop to make calls and handle responses
    max_iterations = 20
    iteration = 0 

    while iteration < max_iterations:
        used_tool = False

        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            messages=messages,
            system=system_prompt,
            tools=tools,
            max_tokens=1024
        )

        for block in response.content:
            if block.type == "tool_use":
                used_tool = True

                if hasattr(block.input, "model_dump"):
                    tool_input = block.input.model_dump()
                else:
                    tool_input = block.input 

                print(f"Calling tool {block.name} with inputs: {tool_input}")

                messages.append({
                    "role": "assistant",
                    "content": [{
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": tool_input 
                    }]
                })

                try:
                    result = tool_runners[block.name](tool_input)
                except Exception as e:
                    print(f"Error getting result for '{block.name}': {str(e)}")
                    result = f"An error occurred: {str(e)}"

                messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": [{
                                "type": "text",
                                "text": json.dumps(result)
                            }]
                        }]
                    })

                print(f"results of tool call: {json.dumps(result)}")

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

tool_runners = {
    "get_stock_price_yesterday": lambda inp: get_stock_price_yesterday(**inp),
    "get_stock_price_today": lambda inp: get_stock_price_today(**inp),
    "get_latest_stock_news": lambda inp: get_latest_stock_news(**inp)
}

def get_stock_price_yesterday(ticker_name: str):
    data = [{"ticker_name": "amzn", "stock_price": 100.12}, {"ticker_name": "aapl", "stock_price": 203.33}]  

    for dic in data:
        if dic["ticker_name"] == ticker_name:
            return dic["stock_price"]

def get_stock_price_today(ticker_name: str):
    data = [{"ticker_name": "amzn", "stock_price": 80.11}, {"ticker_name": "aapl", "stock_price": 240.23}]  

    for dic in data:
        if dic["ticker_name"] == ticker_name:
            return dic["stock_price"]

def get_latest_stock_news(ticker_name: str):
    data = [{"ticker_name": "amzn", "ticker_news": "bad earnings today"}, {"ticker_name": "aapl", "ticker_news": "big beat, on a tear"}]
    for dic in data:
        if dic["ticker_name"] == ticker_name:
            return dic["ticker_news"]

def load_system_prompt(path: str="prompts/system_prompt.txt"):
    with open(path, "r") as f:
        return f.read().strip()

if __name__=="__main__":
    asyncio.run(run_agent())