from django.core.cache import cache
from math import radians, cos, sin, asin, sqrt

def add_remove_online_user(action, username):
    online_users = cache.get('online_users')
    if not online_users:
        online_users = set()
    if action == "add":
        online_users.add(username)
    elif action == "remove":
        online_users.discard(username)
    else:
        return False
    print(action, username)
    cache.set("online_users" ,online_users)
    return online_users

def add_remove_room_user(action, user, room_id):
    online_users = cache.get(f'r-{room_id}')
    if not online_users:
        online_users = {}
    if action == "add":
        online_users[user["id"]] = user
    elif action == "remove":
        online_users.pop(user["id"],None)
    else:
        return False
    print(action, username)
    cache.set(f"r-{room_id}" ,online_users)
    return online_users

def updateLocationList(action, username, latitude=None, longitude=None):
    location_users = cache.get("location_sharing")
    if not location_users:
        location_users = {}
    if action == "add":
        location_users[username] = (latitude, longitude)
    elif action == "remove":
        location_users.pop(username,None)
    else:
        return False
    print(location_users)
    cache.set("location_sharing", location_users)
    return location_users
    

def calculateDistance(lat1, long1, lat2, long2):
    long1 = radians(long1)
    long2 = radians(long2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
      
    # Haversine formula
    dlon = long2 - long1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
 
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371
      
    # calculate the result (in KM)
    return(c * r)