from orchestrator.model.QwenModel import QwenModelAgent
from orchestrator.schema import chatModel

SYSTEM_PROMPT = """You are an AI assistant. When the user asks for an action, you MUST use a tool call.
Do not confirm, do not apologize, and do not make up results. Only the system can provide results after you call a tool.
If the user does not provide all required information for an action, ask them for the missing details.
Example - booking a ride:
User: Book me a ride from Anosy to Analakely for user john_doe
Assistant: <tool_call>{"name": "book_ride", "arguments": {"pickup": "Anosy", "destination": "Analakely", "user_id": "john_doe"}}</tool_call>
Now assist the user."""

class ModelService:
    def __init__(self):
        self.agent = QwenModelAgent()

    def generate(self, messages: list[dict], max_new_tokens: int = 512, temperature: float = 0.7 ,tools: list = None) -> str:
        chat_messages = [
                            m if isinstance(m, chatModel) else chatModel(role=m["role"], content=m.get("content", ""))
                            for m in messages
                        ]
        
        return self.agent.chat(chat_messages, tools = tools ,max_new_tokens=max_new_tokens)

    def parse_tool_calls(self, text: str) -> list[dict]:
        return self.agent.parse_tool_calls(text)