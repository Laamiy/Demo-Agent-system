# orchestrator/tools/registry.py
from orchestrator.tools.bash  import bash
from orchestrator.tools.files import read_file, write_file, list_dir, delete_file
from orchestrator.tools.fetch import fetch_url

from api.utils.tools import TOOL_FUNCTIONS as API_TOOL_FUNCTIONS

API_TOOL_SCHEMAS = [
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
                    "username": {"type": "string", "description": "Username"}
                },
                "required": ["username"]
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
                    "restaurantname": {"type": "string"},
                    "items": {"type": "array", "items": {"type": "string"}},
                    "username": {"type": "string", "description": "username"}
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
                    "username": {"type": "string", "description": " username "}
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
]

AGENT_TOOL_SCHEMAS = API_TOOL_SCHEMAS + [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command. Use for installing packages, running scripts, compiling code, checking system state, or any OS-level action. Supports sudo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the content of a file from disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or workspace-relative path"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates parent directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path":    {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and directories at a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file from disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "Fetch content from a URL. Use to pull documentation, download raw files, or call external APIs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                },
                "required": ["url"],
            },
        },
    },
]

# ── Functions ─────────────────────────────────────────────────────────────────
AGENT_TOOL_FUNCTIONS = {
    **API_TOOL_FUNCTIONS,
    "bash":        bash,
    "read_file":   read_file,
    "write_file":  write_file,
    "list_dir":    list_dir,
    "delete_file": delete_file,
    "fetch_url":   fetch_url,
}