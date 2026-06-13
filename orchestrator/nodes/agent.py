import re
import json
import inspect
import httpx
from common.logger import logger
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from orchestrator.model.ModelService import ModelService
from orchestrator.tools.registry import AGENT_TOOL_FUNCTIONS, AGENT_TOOL_SCHEMAS
from orchestrator.nodes.prompts.agent_node_prompt import AGENT_SYSTEM
from config import get_settings


settings = get_settings()
BACKEND_URL = f"http://{settings.app.HOST}:{settings.app.PORT}" 

API_TOOL_NAMES = {
    "get_user_info", "get_user_orders",
    "place_order", "book_ride",
    "search_restaurants", "control_screen_backlight",
}


def _extract_tool_calls(raw: str) -> list[dict]:
    """
    Robustly extract tool calls from model output.
    Handles:
    - Properly closed tags
    - Unclosed tags
    - Leading garbage before JSON (>, whitespace, newlines)
    - Markdown code fences inside tags
    - Multiple tool calls in one response
    - JSON embedded in prose without tags
    """
    results = []

    # properly closed tags
    for match in re.finditer(r"<tool_call>(.*?)</tool_call>", raw, re.DOTALL):
        parsed = _try_parse_json(match.group(1))
        if parsed:
            results.append(parsed)

    if results:
        return results

    # unclosed tag — grab everything after <tool_call> to end of string
    match = re.search(r"<tool_call>(.*?)$", raw, re.DOTALL)
    if match:
        parsed = _try_parse_json(match.group(1))
        if parsed:
            return [parsed]

    # bare JSON object that looks like a tool call (no tags at all)
    for match in re.finditer(r"\{[^{}]*\"name\"\s*:[^{}]*\"arguments\"\s*:[^{}]*\{[^{}]*\}[^{}]*\}", raw, re.DOTALL):
        parsed = _try_parse_json(match.group(0))
        if parsed and "name" in parsed and "arguments" in parsed:
            results.append(parsed)

    return results


def _try_parse_json(raw_json: str) -> dict | None:
    """
    Clean and parse a JSON string that may contain:
    - Leading/trailing whitespace or newlines
    - Leading > characters (model artifact)
    - Markdown code fences (```json ... ```)
    - Truncated/incomplete JSON
    """
    if not raw_json:
        return None

    text = raw_json.strip()

    # Remove markdown code fences
    text = re.sub(r"^```[\w]*\n?", "", text)
    text = re.sub(r"\n?```$",      "", text)
    text = text.strip()

    # Remove leading > artifacts and whitespace
    text = re.sub(r"^[>\s]+", "", text)
    text = text.strip()

    # Find the first { and last } — extract the outermost JSON object
    start = text.find("{")
    if start == -1:
        return None

    # Walk from start to find matching closing brace
    depth   = 0
    end_idx = -1
    in_str  = False
    escape  = False

    for i, ch in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if ch == "\\" and in_str:
            escape = True
            continue
        if ch == '"' and not escape:
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end_idx = i + 1
                break

    if end_idx == -1:
        # Try to close incomplete JSON by appending braces
        open_braces = text.count("{") - text.count("}")
        text_fixed  = text[start:] + "}" * open_braces
        try:
            return json.loads(text_fixed)
        except json.JSONDecodeError:
            logger.debug("Could not repair JSON: %r", text[:100])
            return None

    try:
        return json.loads(text[start:end_idx])
    except json.JSONDecodeError as e:
        logger.debug("JSON parse failed: %s — %r", e, text[start:end_idx][:100])
        return None


def _execute_tool(tool_name: str, arguments: dict) -> dict:
    """Route tool execution — API tools go to backend, system tools run locally."""
    if tool_name in API_TOOL_NAMES:
        try:
            resp = httpx.post(
                f"{BACKEND_URL}/infer/tool/{tool_name}",
                json=arguments,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            return {"error": str(e)}

    func = AGENT_TOOL_FUNCTIONS.get(tool_name)
    if func is None:
        return {"error": f"Unknown tool: {tool_name}. Available: {list(AGENT_TOOL_FUNCTIONS.keys())}"}

    try:
        if inspect.iscoroutinefunction(func):
            import asyncio
            return asyncio.run(func(**arguments))
        return func(**arguments)
    except TypeError as e:
        return {"error": f"Wrong arguments for {tool_name}: {e}"}
    except Exception as e:
        logger.error("Tool %s failed: %s", tool_name, e)
        return {"error": str(e)}


def agent_node(state: dict, model: ModelService) -> dict:
    # Build message history
    history = []
    for m in state["messages"]:
        if isinstance(m, HumanMessage):
            history.append({"role": "user",      "content": m.content})
        elif isinstance(m, AIMessage):
            history.append({"role": "assistant",  "content": m.content})
        elif isinstance(m, ToolMessage):
            history.append({"role": "tool",       "content": m.content, "name": m.name})

    messages = [{"role": "system", "content": AGENT_SYSTEM}] + history

    raw = model.generate(messages, tools=AGENT_TOOL_SCHEMAS, max_new_tokens=512)
    logger.info("Agent raw: %s", raw[:300])

    calls = _extract_tool_calls(raw)

    if not calls:
        # No tool call — agent is done
        # Strip any leftover <tool_call> artifacts from the final response
        clean = re.sub(r"<tool_call>.*?(?:</tool_call>|$)", "", raw, flags=re.DOTALL).strip()
        return {
            "response": clean or raw,
            "messages": [AIMessage(content=clean or raw)],
            "iterations": state.get("iterations", 0),
        }

    new_messages = [AIMessage(content=raw)]
    executed_any = False

    for call in calls:
        tool_name = call.get("name")
        arguments = call.get("arguments", {})

        if not tool_name:
            logger.warning("Tool call missing name: %s", call)
            continue

        if not isinstance(arguments, dict):
            logger.warning("Arguments not a dict for %s: %r", tool_name, arguments)
            arguments = {}

        logger.info("Executing %s(%s)", tool_name, arguments)
        result = _execute_tool(tool_name, arguments)
        logger.info("Result: %s", str(result)[:300])
        executed_any = True

        new_messages.append(
            ToolMessage(
                content=json.dumps(result),
                name=tool_name,
                tool_call_id=tool_name,
            )
        )

    if not executed_any:
        # Parsed calls but none had valid names — tell model to retry
        logger.warning("No tools executed — injecting retry message")
        new_messages.append(
            ToolMessage(
                content=json.dumps({
                    "error": "Could not parse tool call. Use exactly: "
                             "<tool_call>{\"name\": \"tool_name\", \"arguments\": {}}</tool_call>"
                }),
                name="system",
                tool_call_id="system",
            )
        )

    return {
        "response":   None,
        "messages":   new_messages,
        "iterations": state.get("iterations", 0) + 1,
    }