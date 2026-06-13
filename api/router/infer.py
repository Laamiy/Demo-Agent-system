import inspect
from typing import Dict, Any
from sqlalchemy import select
from api.entities.user import User
from api.deps.core import get_connection
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from api.utils.tools import TOOL_FUNCTIONS
from common.logger import logger 

router = APIRouter()

@router.get("/health")
async def health(session: AsyncSession = Depends(get_connection)):
    res = await session.execute(select(User))
    return {
                "status": "ok",
                "db_ready": res.scalars().one() is not None,
            }


@router.post("/tool/{tool_name}")
async def execute_tool(
                            tool_name: str,
                            params: Dict[str, Any],
                            session: AsyncSession = Depends(get_connection),
                        ):
    
    if tool_name not in TOOL_FUNCTIONS:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    func = TOOL_FUNCTIONS[tool_name]
    logger.info("tool being called %s", func)
    sig  = inspect.signature(func)
    logger.info("function signature : %s", sig )
    valid_names = set(sig.parameters.keys())

    filtered    = {k: v for k, v in params.items() if k in valid_names}
    logger.info("filtered : ")
    logger.info(filtered)
    required    = [
                        p.name for p in sig.parameters.values()
                        if p.default is inspect.Parameter.empty and p.name != "session"
                    ]
    logger.info("required : ")
    logger.info(required)

    missing = [r for r in required if r not in filtered]

    if missing:
        raise HTTPException(
                                status_code=400,
                                detail=f"Missing required: {missing}. Valid: {list(valid_names)}",
                            )

    try:
        if inspect.iscoroutinefunction(func):
            filtered.pop("session", None)
            return await func(session, **filtered)
    
        return func(**filtered)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))