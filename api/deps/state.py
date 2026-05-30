from fastapi import Request
from api.deps.Agent import QwenModelAgent
 
def get_agent(req : Request) -> QwenModelAgent : 
    return req.app.state.qwen_model_agent