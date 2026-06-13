from api.utils.service import (
    get_user_info,
    book_ride,
    place_order,
    get_user_orders,
    search_restaurants,
)


TOOL_FUNCTIONS = {
                        "get_user_info": get_user_info,
                        "get_user_orders": get_user_orders,
                        "place_order": place_order,
                        "book_ride": book_ride,
                        "search_restaurants": search_restaurants,
                    }
