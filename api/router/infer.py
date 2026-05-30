import json
import inspect
import logging
import re
from typing import Annotated, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps.state import get_agent
from api.deps.Agent import QwenModelAgent
from api.deps.core import get_connection
from .tool_utils import TOOL_FUNCTIONS, TOOL_SCHEMAS
from .schema import ChatRequest, ChatResponse, ToolCall, ToolResult

router = APIRouter()
Agent = Annotated[QwenModelAgent, Depends(get_agent)]
logger = logging.getLogger(__name__)


def _extract_tool_calls(text: str) -> List[dict]:
    """
    Extract tool calls from raw model output.
    Handles both closed <tool_call>...</tool_call> and unclosed tags.
    """
    calls = []

    # Pattern 1: Properly closed tags
    for match in re.finditer(r'<tool_call>(.*?)</tool_call>', text, re.DOTALL):
        try:
            data = json.loads(match.group(1).strip())
            calls.append(_normalize_call(data))
        except (json.JSONDecodeError, KeyError):
            continue

    if calls:
        return calls

    # Pattern 2: Unclosed tag (model outputs <tool_call>{"name":...} without closing)
    for match in re.finditer(r'<tool_call>\s*(\{.*)', text, re.DOTALL):
        json_str = match.group(1)
        brace_count = 0
        end_idx = 0
        in_string = False
        escape_next = False

        for i, ch in enumerate(json_str):
            if escape_next:
                escape_next = False
                continue
            if ch == '\\':
                escape_next = True
                continue
            if ch == '"' and not in_string:
                in_string = True
            elif ch == '"' and in_string:
                in_string = False
            elif not in_string:
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break

        if end_idx > 0:
            try:
                data = json.loads(json_str[:end_idx])
                calls.append(_normalize_call(data))
            except (json.JSONDecodeError, KeyError):
                continue

    return calls


def _normalize_call(data: dict) -> dict:
    """Normalize Qwen tool-call formats."""
    name = data.get("name")
    if not name and "function" in data:
        name = data["function"].get("name")

    args = data.get("arguments") or data.get("parameters") or {}
    if "function" in data and isinstance(data["function"], dict):
        args = data["function"].get("arguments", args)

    return {"name": name, "arguments": args}


SYSTEM_PROMPT = """You are an AI assistant for a Malagasy delivery and ride service.
You help with: account lookup, orders, restaurant search, ride booking, device control.

When you need to perform an action, you MUST use a tool call:
<<tool_call>{"name": "tool_name", "arguments": {"param": "value"}}</tool_call>

After the system returns the result, summarize it naturally.
If the user speaks Malagasy, respond in Malagasy."""


@router.get("/health")
async def health(agent: Agent):
    return {
        "status": "ok",
        "model_loaded": agent is not None,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    agent: Agent,
    session: AsyncSession = Depends(get_connection),
):
    if not agent:
        raise HTTPException(status_code=503, detail="Model not loaded")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if req.history:
        messages.extend(req.history)
    messages.append({"role": "user", "content": req.message})

    logger.info("User: %s", req.message)

    # First generation
    response_text = agent.chat(messages, tools=TOOL_SCHEMAS, max_new_tokens=512)
    logger.info("First generation: %s", response_text[:400])

    tool_calls: List[ToolCall] = []
    tool_results: List[ToolResult] = []

    # Robust extraction (handles unclosed tags)
    calls = _extract_tool_calls(response_text)
    if not calls:
        calls = agent.parse_tool_calls(response_text)

    if calls:
        messages.append({"role": "assistant", "content": response_text})

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
                messages.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": json.dumps({"error": err})
                })
                continue

            func = TOOL_FUNCTIONS[tool_name]
            try:
                if inspect.iscoroutinefunction(func):
                    result = await func(session, **arguments)
                else:
                    result = func(**arguments)

                tool_results.append(ToolResult(tool=tool_name, result=result))
                messages.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": json.dumps(result)
                })
                logger.info("Result: %s", result)

            except Exception as e:
                err = str(e)
                logger.error("Tool %s failed: %s", tool_name, err)
                tool_results.append(ToolResult(tool=tool_name, error=err))
                messages.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": json.dumps({"error": err})
                })

        # Second generation with tool results
        response_text = agent.chat(messages, tools=TOOL_SCHEMAS, max_new_tokens=512)
        logger.info("Second generation: %s", response_text[:400])

    return ChatResponse(
        response=response_text,
        tool_calls=tool_calls if tool_calls else None,
        tool_results=tool_results if tool_results else None
    )


@router.get("/tools")
async def list_tools():
    return {"tools": TOOL_SCHEMAS}


@router.post("/tool/{tool_name}")
async def execute_tool(
    tool_name: str,
    params: Dict[str, Any],
    session: AsyncSession = Depends(get_connection)
):
    """Direct tool execution for testing."""
    if tool_name not in TOOL_FUNCTIONS:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    func = TOOL_FUNCTIONS[tool_name]
    sig = inspect.signature(func)
    valid_names = set(sig.parameters.keys())
    filtered = {k: v for k, v in params.items() if k in valid_names}

    required = [
        p.name for p in sig.parameters.values()
        if p.default is inspect.Parameter.empty and p.name != "session"
    ]
    missing = [r for r in required if r not in filtered]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required: {missing}. Valid: {list(valid_names)}"
        )

    try:
        if inspect.iscoroutinefunction(func):
            filtered.pop("session", None)
            return await func(session, **filtered)
        return func(**filtered)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))