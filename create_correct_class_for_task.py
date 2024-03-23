from restaurant_manager import RestaurantManager
from search_creative_work_manager import SearchCreativeWorkManager

def create_class(task):
    if task == "bookRestaurant":
        return RestaurantManager()
    elif task == "searchCreativeWorks":
        return SearchCreativeWorkManager()
    else:
        return None