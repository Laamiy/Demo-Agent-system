from langchain_core.messages import AIMessage
from orchestrator.schema import AgentState

def clarify_node(state: AgentState, model) -> dict:
    reply = "Could you clarify what you'd like to do? I'm not sure I understood."
    return {
                "response": reply,
                "messages": [AIMessage(content=reply)],
            }