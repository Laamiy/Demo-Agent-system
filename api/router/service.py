import uuid
import random
import json 
import re 
import subprocess
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List 
from api.deps.state import get_agent
from api.deps.Agent import QwenModelAgent
from api.entities.user import User, Order, Restaurant, Ride  
from sqlalchemy import func , or_
from api.common.logger import logger 
from sqlalchemy.ext.asyncio import AsyncSession
router = APIRouter()
Agent = Annotated[QwenModelAgent, Depends(get_agent)]
# db_session = Annotated[AsyncGenerator[AsyncSession,None] , Depends(get_connection)]
# ─── REAL TOOL IMPLEMENTATIONS (hit your actual DB) ───────


async def get_user_info(session: AsyncSession, username: str = None, phone: str = None):
    if not username and not phone:
        raise ValueError("Provide username or phone")

    stmt = select(User)
    if username:
        logger.info("current username : %s " , username)
        stmt = stmt.where(func.lower(User.username) == username.lower())
    else:
        stmt = stmt.where(User.phone == phone)

    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError(f"User not found: {username or phone}")

    return {
        "user_id": str(user.uid),
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "address": user.address,
    }


async def get_user_orders(session: AsyncSession, user_id: str):
    # Try UUID first, fallback to username
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        user_stmt = select(User).where(User.username == user_id)
        res = await session.execute(user_stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        uid = user.uid

    stmt = select(Order).where(Order.user_id == uid).order_by(Order.created_at.desc())
    result = await session.execute(stmt)
    orders = result.scalars().all()

    return {
        "orders": [
            {
                "order_id": o.order_id,
                "item": o.item,
                "status": o.status,
                "total": o.total,
                "currency": o.currency,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ]
    }


async def place_order(session: AsyncSession, restaurant_id: str, items: list, user_id: str):
    # Resolve user
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        user_stmt = select(User).where(User.user_id == user_id)
        res = await session.execute(user_stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        uid = user.uid

    # Verify restaurant exists
    rest_stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
    rest_res = await session.execute(rest_stmt)
    restaurant = rest_res.scalar_one_or_none()
    if not restaurant:
        raise ValueError(f"Restaurant not found: {restaurant_id}")

    # NOTE: Your Order.item is String(255). If items list is long, it may truncate.
    # Consider changing item to Text or adding an OrderItem table later.
    total = len(items) * 15000  # placeholder pricing until you parse restaurant.menu JSON

    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    new_order = Order(
        order_id=order_id,
        user_id=uid,
        item=", ".join(items),
        status="confirmed",
        total=total,
        currency="MGA",
    )
    session.add(new_order)
    # await session.commit()

    return {
        "order_id": order_id,
        "status": "confirmed",
        "items": items,
        "restaurant": restaurant.name,
        "total": total,
        "currency": "MGA",
    }


async def search_restaurants(session: AsyncSession, query: str):
    stmt = select(Restaurant).where(
        (Restaurant.name.ilike(f"%{query}%")) |
        (Restaurant.cuisine.ilike(f"%{query}%"))
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()

    return {
        "results": [
            {
                "id": r.id,
                "name": r.name,
                "cuisine": r.cuisine,
                "rating": r.rating,
                "delivery_time": r.delivery_time,
            }
            for r in rows
        ]
    }


async def book_ride(session: AsyncSession, destination: str, pickup: str , user_id: str = None ) :#, username : str = None ):
    uid = None
    if user_id:
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            user_stmt = select(User).where( User.uid == user_id  , 
                                           #     func.lower(User.username) == (username or "").lower()
                                           )
            res = await session.execute(user_stmt)
            user = res.scalar_one_or_none()
            if user:
                uid = user.uid
 # Just set price to random for demo only anyway
    price = random.randint(5000, 20000)
    ride_id = uuid.uuid4()#f"RIDE-{random.randint(1000, 9999)}"

    ride = Ride(
        ride_id=ride_id,
        user_id=uid,
        destination=destination,
        pickup=pickup or "Current location",
        status="confirmed",
        price=price,
        currency="MGA",
    )
    logger.info("current ride %s to %s " , ride.pickup , ride.destination)
    session.add(ride)
    await session.commit()

    return {
        "ride_id": str(ride_id),
        "status": "confirmed",
        "destination": destination,
        "pickup": pickup or "Current location",
        "price": f"{price} MGA",
        "user_id": str(uid) if uid else None,
    }


def control_keyboard(state: str):
    """Real keyboard backlight control. Linux (brightnessctl)."""
    try:
        brightness = 255 if state == "on" else 0
        subprocess.run(
            ["sudo","brightnessctl", "set", str(brightness)],
            check=True,
            capture_output=True,
            text=True,
        )
        return {"status": "success", "device": "keyboard_backlight", "state": state}
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "brightnessctl not found. Install it: sudo apt install brightnessctl"
        }
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": e.stderr}

def _normalize_call(data: dict) -> dict:
    """Normalize Qwen tool-call formats."""
    name = data.get("name")
    if not name and "function" in data:
        name = data["function"].get("name")

    args = data.get("arguments") or data.get("parameters") or {}
    if "function" in data and isinstance(data["function"], dict):
        args = data["function"].get("arguments", args)

    return {"name": name, "arguments": args}


def _extract_tool_calls(text: str) -> List[dict]:
    """
    Extract tool calls from raw model output.
    Handles both closed <tool_call>...</tool_call> and unclosed tags.
    """
    calls = []

    for match in re.finditer(r'<tool_call>(.*?)</tool_call>', text, re.DOTALL):
        try:
            data = json.loads(match.group(1).strip())
            calls.append(_normalize_call(data))
            
        except (json.JSONDecodeError, KeyError):
            continue

    if calls:
        return calls

    # Unclosed tag (model outputs <tool_call>{"name":...} without closing)
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





