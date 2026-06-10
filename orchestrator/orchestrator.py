# orchestrator/orchestrator.py
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from orchestrator.model.ModelService import ModelService
from orchestrator.nodes.router    import router_node
from orchestrator.nodes.chat      import chat_node
from orchestrator.nodes.tool_call import tool_call_node
from orchestrator.nodes.clarify   import clarify_node

class AgentState(TypedDict):
    messages:  Annotated[list[BaseMessage], add_messages]
    intent:    str
    response:  str | None

def build_graph(model: ModelService):
    # Bind model into each node via closures
    def _router(state):    return router_node(state, model)
    def _chat(state):      return chat_node(state, model)
    def _tool_call(state): return tool_call_node(state, model)
    def _clarify(state):   return clarify_node(state, model)

    def route(state) -> Literal["_tool_call", "_chat", "_clarify"]:
        return f"_{state['intent']}"

    builder = StateGraph(AgentState)

    builder.add_node("router_node",    _router)
    builder.add_node("_tool_call",     _tool_call)
    builder.add_node("_chat",          _chat)
    builder.add_node("_clarify",       _clarify)

    builder.add_edge(START, "router_node")
    builder.add_conditional_edges(
        "router_node",
        route,
        {
            "_tool_call": "_tool_call",
            "_chat":      "_chat",
            "_clarify":   "_clarify",
        },
    )
    builder.add_edge("_tool_call", END)
    builder.add_edge("_chat",      END)
    builder.add_edge("_clarify",   END)

    return builder.compile()