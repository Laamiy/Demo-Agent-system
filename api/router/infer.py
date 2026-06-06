import re
import json
import inspect
from typing import Annotated, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from api.common.logger import logger 
from api.deps.state import get_agent
from api.deps.core import get_connection
from api.deps.Agent import QwenModelAgent
from .tool_utils import TOOL_FUNCTIONS, TOOL_SCHEMAS ,SYSTEM_PROMPT
from .schema import ChatRequest, ChatResponse, ToolCall, ToolResult 
from api.deps.schema import chatModel
from .service import _extract_tool_calls 

router = APIRouter()
Agent  = Annotated[QwenModelAgent, Depends(get_agent)]



@router.get("/health")
async def health(agent: Agent):

    return {
                "status": "ok",
                "model_loaded": agent is not None,
            }


@router.post("/chat", response_model=ChatResponse)
async def chat(    req: ChatRequest, agent: Agent, session: AsyncSession = Depends(get_connection),):

    if not agent:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try : 
        chat = chatModel("system" , SYSTEM_PROMPT)
    
        messages = [chat]

        if req.history:
            messages.extend(req.history)
            
        messages.append( chatModel("user" , req.message))

        logger.info("User: %s", req.message)
        # First generationchatModel
        
        response_text = agent.chat(messages, tools=TOOL_SCHEMAS, max_new_tokens=512)
        logger.info("First generation: %s", response_text[:400])

        tool_calls: List[ToolCall] = []
        tool_results: List[ToolResult] = []

        # Robust extraction (handles unclosed tags)
        calls = _extract_tool_calls(response_text)
        
        if not calls:
            calls = agent.parse_tool_calls(response_text)

        if calls:
            messages.append(chatModel("assistant" , response_text))

            for call in calls:
                tool_name = call.get("name")
                arguments = call.get("arguments", {})

                if not tool_name:
                    continue

                tool_calls.append(ToolCall(name=tool_name, arguments=arguments))
                logger.info("Executing: %s(%s)", tool_name, arguments)

                if tool_name not in TOOL_FUNCTIONS:
                    err = f"Unknown tool: {tool_name}"
                    tool_results.append(ToolResult(tool=tool_name, error=err))
                    messages.append(  chatModel(role = "tool",name = tool_name , content  = json.dumps({"error":err})) )
                    continue

                func = TOOL_FUNCTIONS[tool_name]
                try:
                    if inspect.iscoroutinefunction(func):
                        result = await func(session, **arguments)
                    else:
                        result = func(**arguments)

                    tool_results.append(ToolResult(tool=tool_name, result=result))
                    messages.append(chatModel(role = "tool",name = tool_name , content = json.dumps(result)))
                    logger.info("Result: %s", result)

                except Exception as e:
                    err = str(e)
                    logger.error("Tool %s failed: %s", tool_name, err)
                    tool_results.append(ToolResult(tool=tool_name, error=err))
                    messages.append(chatModel(role  = "tool",name = tool_name , content = json.dumps({"error":err})))

            # Second generation with tool results
            response_text = agent.chat(messages, tools=TOOL_SCHEMAS, max_new_tokens=512)
            logger.info("Second generation: %s", response_text[:400])

        return ChatResponse(
            response=response_text,
            tool_calls=tool_calls if tool_calls else None,
            tool_results=tool_results if tool_results else None
        )
        
    except HTTPException as e :
        logger.error(e)
        raise  
    except Exception as e : 
        raise HTTPException(detail = f"Exception thrown {e}" , status_code = 500)
    
@router.get("/tools")
async def list_tools():
    return {"tools": TOOL_SCHEMAS}


@router.post("/tool/{tool_name}")
async def execute_tool( tool_name: str, params: Dict[str, Any], session: AsyncSession = Depends(get_connection)):
    """Direct tool execution for testing."""
    if tool_name not in TOOL_FUNCTIONS:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    func = TOOL_FUNCTIONS[tool_name]
    
    sig = inspect.signature(func)
    
    valid_names = set(sig.parameters.keys())
    filtered = {k: v for k, v in params.items() if k in valid_names}

    required = [ p.name for p in sig.parameters.values()
                                                if p.default is inspect.Parameter.empty and p.name != "session" ]
    
    missing = [ r for r in required if r not in filtered ]

    if missing:
        raise HTTPException( status_code=400, detail=f"Missing required: {missing}. Valid: {list(valid_names)}" )

    try:
        if inspect.iscoroutinefunction(func):
    
            filtered.pop("session", None)
            return await func(session, **filtered)
    
        return func(**filtered)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))