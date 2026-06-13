from orchestrator.model.QwenModel import QwenModelAgent
from orchestrator.schema import chatModel

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