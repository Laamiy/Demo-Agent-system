from api.utils.service import (
    get_user_info,
    book_ride,
    control_keyboard,
    place_order,
    get_user_orders,
    search_restaurants,
)

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_user_info",
            "description": "Get customer information by username or phone number",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "phone": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_orders",
            "description": "Get order history for a customer",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Username or UUID"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "place_order",
            "description": "Place a food order at a restaurant",
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_id": {"type": "string"},
                    "items": {"type": "array", "items": {"type": "string"}},
                    "user_id": {"type": "string", "description": "username or UUID"}
                },
                "required": ["restaurant_id", "items", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_ride",
            "description": "Book a ride/taxi to a destination",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "pickup": {"type": "string"},
                    "user_name": {"type": "string", "description": " username "}
                },
                "required": ["destination" , "pickup" , "username"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_restaurants",
            "description": "Search for restaurants by cuisine or name",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_keyboard",
            "description": "Turn keyboard backlight on or off",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {"type": "string", "enum": ["on", "off"]}
                },
                "required": ["state"]
            }
        }
    }
]

TOOL_FUNCTIONS = {
    "get_user_info": get_user_info,
    "get_user_orders": get_user_orders,
    "place_order": place_order,
    "book_ride": book_ride,
    "search_restaurants": search_restaurants,
    "control_keyboard": control_keyboard,
}

SYSTEM_PROMPT = """You are an AI assistant. When the user asks for an action, you MUST use a tool call.
Do not confirm, do not apologize, and do not make up results. Only the system can provide results after you call a tool.

If the user does not provide all required information for an action, ask them for the missing details. Do not guess or use placeholder values.

Example - booking a ride (requires pickup, destination, and user_id):
User: Book me a ride from Anosy to Analakely for user john_doe
Assistant: <tool_call>{"name": "book_ride", "arguments": {"pickup": "Anosy", "destination": "Analakely", "user_id": "john_doe"}}</tool_call>

Example - fetching a user:
User: Get user john_doe
Assistant: <tool_call>{"name": "get_user_info", "arguments": {"username": "john_doe"}}</tool_call>

Now assist the user."""