[
    # User message
    {
        "role": "user", 
        "content": "What's the weather in Boston?"
    },
    
    # Assistant message with tool use
    {
        "role": "assistant",
        "content": [
            {
                "type": "tool_use",
                "id": "toolu_123abc",
                "name": "get_weather",
                "input": {"location": "Boston"}
            }
        ]
    },
    
    # Tool result
    {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": "toolu_123abc",
                "content": "Boston: 72°F, sunny"
            }
        ]
    },
    
    # Assistant text response
    {
        "role": "assistant",
        "content": "The weather in Boston is currently 72°F and sunny!"
    },
    
    # Another user message
    {
        "role": "user",
        "content": "What about New York?"
    }
]