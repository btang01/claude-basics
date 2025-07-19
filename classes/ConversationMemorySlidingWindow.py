class ConversationMemorySlidingWindow:
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: List[Dict[str, Any]]):
        self.messages.append({"role": "assistant", "content": content})

    def add_tool_result(self, tool_id: str, result: str):
        self.messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_id": tool_id,
                "content": result
            }]
        })

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.messages.copy()
    
    # last 20 messages
    def get_recent_messages(self, window_size: int=20) -> List[Dict[str, Any]]:
        return self.messages[-window_size:]
    
    # can also get by token limit
    def get_recent_messages_token_limit(self, token_limit: int=10000) -> List[Dict[str, Any]]:
        total = 0
        recent = []

        # iterate backwards to get most relevant recent turns
        for msg in reversed(self.messages):
            estimated += rough_token_estimate(msg)
            if estimated > token_limit:
                break
            # iterating backwards through list, so stick new messages to the beginning of recent list
            recent.insert(0, msg)
            total+= estimated   
        return recent 
    
    def rough_token_estimate(msg: Dict[str, Any]) -> int:
        content = msg.get("content", "")
        if isinstance(content, list):  # structured tool_use or tool_result
            content_str = json.dumps(content)

        elif isinstance(content, str):
            content_str = content
        else:
            content_str = str(content)

        return len(content_str) // 4  # rough heuristic