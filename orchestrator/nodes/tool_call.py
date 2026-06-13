import re
import json
import httpx
from config import get_settings
from common.logger import logger
from orchestrator.tools.registry import API_TOOL_SCHEMAS
from orchestrator.schema import AgentState
from langchain_core.messages import AIMessage, HumanMessage
from orchestrator.model.ModelService import ModelService
from orchestrator.model.prompt import SYSTEM_PROMPT

settings = get_settings()
BACKEND_URL = f"http://{settings.app.HOST}:{settings.app.PORT}" 

def tool_call_node(state: AgentState, model: ModelService) -> AgentState:
    history = [
                    {
                        "role": "user" if isinstance(m, HumanMessage) else "assistant",
                        "content": m.content,
                    }
                    for m in state["messages"][:-1]
                ]
    user_message  : str = state["messages"][-1].content

    messages = (
                    [{"role": "system", "content": SYSTEM_PROMPT}]
                    + history
                    + [{"role": "user", "content": user_message}]
                )

    # available tools to the model  : 
    raw = model.generate(messages, tools=API_TOOL_SCHEMAS)
    # logger.info("Tool generation: %s", raw[:200])

    match = re.search(r"<tool_call>(.*?)</tool_call>", raw, re.DOTALL)
    
    if not match:
        logger.info("No tool call produced — model asking for more info")
        return {
                    "response": raw,
                    "messages": [AIMessage(content=raw)],
                }

    try:
        call      = json.loads(match.group(1))
        tool_name = call["name"]
        arguments = call.get("arguments", {})
        
    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Failed to parse tool call: %s", e)
        reply = "Sorry, I could not parse the tool call."
        
        return {"response": reply, "messages": [AIMessage(content=reply)]}

    logger.info("Executing %s(%s)", tool_name, arguments)
    
    try:
        resp = httpx.post(
                            f"{BACKEND_URL}/infer/tool/{tool_name}",
                            json=arguments,
                            timeout=30,
                        )
        
        resp.raise_for_status()
        tool_result = resp.json()
        
    except httpx.HTTPError as e:
        logger.error("Tool execution failed: %s", e)
        tool_result = {"error": str(e)}

    logger.info("Tool result: %s", tool_result)
    messages.append({"role": "assistant", "content": raw})
    messages.append({"role": "tool", "content": json.dumps(tool_result), "name": tool_name})

    final_reply = model.generate(messages, tools=API_TOOL_SCHEMAS)
    logger.info("Final reply: %s", final_reply[:120])

    return {
        "response": final_reply,
        "messages": [AIMessage(content=final_reply)],
    }