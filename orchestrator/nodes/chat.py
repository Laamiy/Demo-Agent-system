from common.logger import logger 

from orchestrator.schema import AgentState

from orchestrator.model.ModelService import ModelService
from langchain_core.messages import HumanMessage, AIMessage
from orchestrator.nodes.prompts.chat_prompt import CHAT_SYSTEM

def chat_node(state: AgentState, model :ModelService) -> AgentState:

    history = [
                    {
                        "role": "user" if isinstance(m, HumanMessage) else "assistant",
                        "content": m.content,
                    }
                    for m in state["messages"][:-1]
                ]
    user_message = state["messages"][-1].content

    messages = (
                    [{"role": "system", "content": CHAT_SYSTEM}]
                    + history
                    + [{"role": "user", "content": user_message}]
                )

    reply = model.generate(messages, tools=None)  # no tools passed
    logger.info("Chat reply: %s", reply[:120])

    return {
                "response": reply,
                "messages": [AIMessage(content=reply)],
            }