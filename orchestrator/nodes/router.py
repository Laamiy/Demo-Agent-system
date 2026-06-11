import re
from common.logger import logger
from orchestrator.schema import AgentState

    
ROUTER_SYSTEM = """You are an intent classifier. Reply with exactly one word:
- tool_call  → user wants to DO something (book ride, order food, get user info)
- chat       → user wants to talk or ask a question
- clarify    → message is too vague

One word only. No punctuation. No explanation."""

def router_node(state: AgentState, model) -> AgentState:
        
    user_message  : str = state["messages"][-1].content
    logger.info("Routing: %s", user_message)

    messages = [
                    {"role": "system",  "content": ROUTER_SYSTEM},
                    {"role": "user",    "content": user_message},
                ]
    raw = model.generate(messages, max_new_tokens=5, temperature=0.1)
    intent = re.sub(r"[^a-z_]", "", raw.strip().lower().split()[0])

    if intent not in {"tool_call", "chat", "clarify"}:
        intent = "clarify"

    logger.info("Intent: %s", intent)
    return {"intent": intent }#, "messages":  messages}