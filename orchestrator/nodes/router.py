import re
from common.logger import logger
from orchestrator.schema import AgentState
from langchain_core.messages import HumanMessage
from orchestrator.nodes.prompts.router_prompt import  ROUTER_SYSTEM
from orchestrator.schema import VALID_INTENT

def router_node(state: AgentState, model) -> AgentState:
    user_message = state["messages"][-1].content
    logger.info("Routing: %s", user_message)

    # Give router last 3 messages for context
    
    context = "\n".join([
                            f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
                            for m in state["messages"][-3:]
                        ])

    messages = [
                    {"role": "system", "content": ROUTER_SYSTEM},
                    {"role": "user",   "content": context},
                ]
    
    raw    = model.generate(messages, max_new_tokens=5, temperature=0.1)
    logger.info("raw model output : %s", raw) 
    
    intent = re.sub(r"[^a-z_]", " ", raw.strip().lower().split()[0])
    logger.info("raw model output : %s", raw) 

    if intent not in VALID_INTENT:
        logger.warning("intent not in valid list, defaulting to chat")
        intent = "chat"   

    logger.info("router deduced intent is : %s", intent)
    return {"intent": intent}