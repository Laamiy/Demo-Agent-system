from enum  import Enum   
from dataclasses import dataclass 
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing import TypedDict ,  Annotated  , Literal

@dataclass
class chatModel : 
    role : str  
    content  : str 
    name : str | None = None 
    
    
class AgentState(TypedDict):
    messages:  Annotated[list[BaseMessage], add_messages]
    intent:    Literal["tool_call", "chat", "clarify"]
    response:  str | None
    iterations: int          # add this


class Commands(Enum):
    QUIT    = "quit" 
    CLEAR   = "clear"

VALID_INTENT = {"tool_call", "chat", "clarify" , "agent"}