from orchestrator.schema import AgentState
from langchain_core.messages import AIMessage
from orchestrator.model.ModelService import SYSTEM_PROMPT
from orchestrator.model.ModelService import ModelService

def chat_node(state: AgentState, model : ModelService) -> AgentState:
    history = [
                    {
                        "role": ("user" if isinstance(m, type(state["messages"][0])) else "assistant"),
                        "content": m.content
                    }
                    for m in state["messages"][:-1]
                ]
    user_message = state["messages"][-1].content

    messages = (
                    [{"role": "system", "content": SYSTEM_PROMPT}]
                    + history
                    + [{"role": "user", "content": user_message}]
                )

    reply = model.generate(messages)

    return {
                "response": reply,
                "messages": [AIMessage(content=reply)],
            }