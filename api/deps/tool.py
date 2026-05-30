import json
from  datetime import datetime
from deps.core import get_connection
from sqlalchemy import select, insert , func 
from sqlalchemy.ext.asyncio import AsyncSession
from entities.user import User, Order, Restaurant

async def get_user_info(name: str = None, user_id: str = None) -> dict:
    async with get_connection() as session:
        if user_id:
            result = await session.execute(select(User).where(User.uid == user_id))
        elif name:
            result = await session.execute(
                select(User).where(User.username.ilike(f"%{name}%"))
            )
        else:
            return {"success": False, "error": "Provide name or user_id"}
        
        user = result.scalar_one_or_none()
        if not user:
            return {"success": False, "error": "User not found"}
        
        return {
            "success": True,
            "user": {
                "id": str(user.uid),
                "name": user.username,
                "email": user.email,
                "phone": user.phone,
                "address": user.address
            }
        }

async def get_customer_order(order_id: str = None, user_name: str = None) -> dict:
    async with get_connection() as session:
        if order_id:
            result = await session.execute(
                select(Order).where(Order.order_id == order_id)
            )
            order = result.scalar_one_or_none()
            if not order:
                return {"success": False, "error": f"Order {order_id} not found"}
            
            return {
                "success": True,
                "order": {
                    "order_id": order.order_id,
                    "customer": order.user.username,
                    "item": order.item,
                    "status": order.status,
                    "total": f"{order.total} {order.currency}"
                }
            }
        
        elif user_name:
            # Find user first
            user_result = await session.execute(
                select(User).where(User.username.ilike(f"%{user_name}%"))
            )
            user = user_result.scalar_one_or_none()
            if not user:
                return {"success": False, "error": f"User '{user_name}' not found"}
            
            # Get their orders
            orders_result = await session.execute(
                select(Order).where(Order.user_id == user.uid)
            )
            orders = orders_result.scalars().all()
            
            return {
                "success": True,
                "customer": user.username,
                "orders": [
                    {
                        "order_id": o.order_id,
                        "item": o.item,
                        "status": o.status,
                        "total": f"{o.total} {o.currency}"
                    }
                    for o in orders
                ]
            }
        
        return {"success": False, "error": "Provide order_id or user_name"}

async def place_food_order(restaurant: str, item: str, quantity: int = 1, address: str = None) -> dict:
    async with get_connection() as session:
        # Find restaurant
        result = await session.execute(
            select(Restaurant).where(
                (Restaurant.id == restaurant.lower()) | 
                (Restaurant.name.ilike(f"%{restaurant}%"))
            )
        )
        rest = result.scalar_one_or_none()
        
        if not rest:
            return {"success": False, "error": f"Restaurant '{restaurant}' not found"}
        
        # Check menu
        menu = json.loads(rest.menu)
        if item not in menu:
            return {"success": False, "error": f"'{item}' not on menu. Available: {', '.join(menu)}"}
        
        # Create order
        order_id = f"ORD-{datetime.now().year}-{await session.execute(select(func.count(Order.order_id))) + 1:03d}"
        
        new_order = Order(
            order_id=order_id,
            user_id="GUEST",  # Or get from auth context
            item=f"{quantity}x {item}",
            status="confirmed",
            total=quantity * 15000,
            restaurant_id=rest.id,
            delivery_address=address or "Default address"
        )
        session.add(new_order)
        await session.commit()
        
        return {
            "success": True,
            "order_id": order_id,
            "message": f"Order placed at {rest.name}: {quantity}x {item}",
            "delivery_time": rest.delivery_time,
            "total": f"{quantity * 15000} MGA"
        }

# ... similar async rewrites for book_ride, get_weather, list_restaurants