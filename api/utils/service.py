import uuid
import random
import subprocess
from sqlalchemy import func
from sqlalchemy import select
from common.logger import logger 
from sqlalchemy.ext.asyncio import AsyncSession
from api.entities.user import User, Order, Restaurant, Ride  



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


async def get_user_orders(session: AsyncSession, username: str):

    user_stmt = select(User).where(func.lower( User.username )== username.strip().lower())
    res = await session.execute(user_stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise ValueError("User with username : %s not found ", username)
    uid = user.uid

    stmt = select(Order).where(Order.user_id == uid).order_by(Order.created_at.desc())
    result = await session.execute(stmt)
    orders = result.scalars().all()
    if orders : 
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
    return  {"orders" : []}

async def place_order(session: AsyncSession, restaurantname: str, items: list, username: str):
    
# Resolve user
    user_stmt = select(User).where(func.lower(User.username) == username.strip().lower())
    res = await session.execute(user_stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise ValueError("User with username : %s not found ", username)
    uid = user.uid
    
# Resolve Restaurant
    rest_stmt = select(Restaurant).where(func.lower(Restaurant.name) == restaurantname.strip().lower())
    rest_res = await session.execute(rest_stmt)
    restaurant = rest_res.scalar_one_or_none()
    if not restaurant:
        raise ValueError("User with username : %s not found ", restaurantname)

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


async def book_ride(session: AsyncSession, destination: str, pickup: str , username: str ) :
    logger.info("destination : %s , pickup : %s , username : %s" , destination , pickup , username)
    uid = None
    user_stmt = select(User).where( func.lower(User.username) == username.strip().lower())
    res = await session.execute(user_stmt)
    user = res.scalar_one_or_none()
    if user:
        uid = user.uid
    else : 
        logger.warning("No id found for %s", username)  
    # random price 
    price = random.randint(5000, 20000)
    ride_id = uuid.uuid4()

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


def control_screen_backlight(state: str):
    """ Real screen backlight control. 
        Linux (brightnessctl).
    """
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






