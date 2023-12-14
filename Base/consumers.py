import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async

class UserConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = self.room_name
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        await self.authenticate_user()
    
    async def disconnect(self, close_code):
        await self.change_status("logout")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    

    @sync_to_async
    def authenticate_user(self):
        if self.scope ['user'].is_authenticated:
            user = self.scope["user"]
            self.user = {"id": user.user_profile.unique_id, "name": user.username}

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        msg_type = text_data_json.get("type")
        if msg_type == "login":
            await self.change_status("login")

    async def room_request(self, event):
        await self.send(text_data=json.dumps({
            'type' : "room_request",
            'response' : event["response"],
            'room_id': event["room_id"]
        }))

    @database_sync_to_async
    def change_status(self, action):
        active = False
        if action == "login":
            active = True
        profile = self.scope["user"].user_profile
        profile.active = active
        profile.save()

        