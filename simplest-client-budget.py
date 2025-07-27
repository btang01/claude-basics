from anthropic import AsyncAnthropic
import json
import asyncio

async def run_agent():
    # define tools or connect to mcp server
    tools = [
        {
            "name": "get_transactions",
            "description": "given the account name, return all transactions (which have an associated category as well) from the account",
            "input_schema": {
                "type": "object",
                "properties": {
                    "user_account_name": {
                        "type": "string",
                        "description": "name of the account, e.g. briantang1, kristinaheng2"
                    }
                },
                "required": ["user_account_name"]
            }
        },
        {
            "name": "get_account_balance",
            "description": "returns the current account balance with the provided account name",
            "input_schema": {
                "type": "object",
                "properties": {
                    "user_account_name": {
                        "type": "string",
                        "description": "name of the account, e.g. briantang1, kristinaheng2"
                    }
                },
                "required": ["user_account_name"]
            }
        },
        {
            "name": "get_budget_per_category",
            "description": "given an account name and a category return the budget associated with the account name and selected category",
            "input_schema": {
                "type": "object",
                "properties": {
                    "user_account_name": {
                        "type": "string",
                        "description": "name of the account, e.g. briantang1, kristinaheng2"
                    },
                    "selected_category": {
                        "type": "string",
                        "description": "name of the category of spending, e.g. snacks, entertainment, dinner, utilities"
                    }
                },
                "required": ["user_account_name"]
            }
        }
    ]

    anthropic_client = AsyncAnthropic()
    messages = []
    user_input = input("Please enter your account name, and if you'd like, a category to check your budget (e.g., 'lunch', 'utilities'). You can also just ask to see your balance or recent transactions: ")

    messages.append({"role": "user", "content": user_input})

    system_prompt = load_system_prompt()

    # loop to handle llm calls and tool use
    max_iterations = 20
    iterations = 0

    while iterations < max_iterations:

        iterations += 1
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

                messages.append({
                    "role": "assistant",
                    "content": [{
                        "type": "tool_use",
                        "name": block.name,
                        "id": block.id,
                        "input": tool_input
                    }]
                })

                result = tool_runners[block.name](tool_input)

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
    "get_transactions": lambda inp: get_transactions(**inp),
    "get_account_balance": lambda inp: get_account_balance(**inp),
    "get_budget_per_category": lambda inp: get_budget_per_category(**inp)
}

def get_transactions(user_account_name: str):

    data = [{"account_name": "jorgemartinez1", "transaction_name": "aix123", "transaction_amt": 15.00, "category": "snacks"},
    {"account_name": "jorgemartinez1", "transaction_name": "aix123", "transaction_amt": 12.32, "category": "snacks"},
    {"account_name": "jorgemartinez1", "transaction_name": "aix123", "transaction_amt": 52.80, "category": "entertainment"},
    {"account_name": "sarahjohnson1", "transaction_name": "jjf111", "transaction_amt": 20.22, "category": "lunch"}]

    transactions_result = []

    for tx in data:
        if tx["account_name"] == user_account_name:
            transactions_result.append(tx)

    return transactions_result

def get_account_balance(user_account_name: str) -> float:
    data = {
        "jorgemartinez1": 2450.75,
        "sarahjohnson1": 1380.40,
        "alexkim2": 785.20,
        "briantang": 5020.10
        }
    balance = data.get(user_account_name)
    return balance

def get_budget_per_category(user_account_name: str, selected_category: str) -> float:

    data = {
        "jorgemartinez1": {
            "lunch": 300.50,
            "utilities": 250.50,
            "snacks": 30.21
        },
        "sarahjohnson1": {
            "lunch": 200.00,
            "entertainment": 400.00
        }
    }

    budgets = data.get(user_account_name, {})
    relevant_budget = budgets.get(selected_category, 0.0)

    return relevant_budget

def load_system_prompt(path: str="prompts/system_prompt.txt"):
    with open(path, "r") as f:
        return f.read().strip()

if __name__=="__main__":
    asyncio.run(run_agent())