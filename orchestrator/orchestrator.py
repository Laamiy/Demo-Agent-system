# orchestrator/orchestrator.py
from typing import Literal
from langgraph.graph import StateGraph, START, END

from orchestrator.schema          import AgentState
from orchestrator.nodes.chat      import chat_node
from orchestrator.nodes.router    import router_node
from orchestrator.nodes.clarify   import clarify_node
from orchestrator.nodes.tool_call import tool_call_node
from orchestrator.model.ModelService import ModelService



def build_graph(model: ModelService):
    # Bind model into each node via closures
    def _router(state : AgentState):    
        return router_node(state, model)
    
    def _chat(state : AgentState):      
        return chat_node(state, model)
    
    def _tool_call(state : AgentState): 
        return tool_call_node(state, model)
    
    def _clarify(state : AgentState):   
        return clarify_node(state, model)

    def route(state : AgentState) -> Literal["_tool_call", "_chat", "_clarify"]:
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