import json
from typing import Text

from django.contrib.auth import authenticate
from Program.models import ChatRoom, Message
from channels.generic.websocket import AsyncWebsocketConsumer
from .service import add_remove_online_user, updateLocationList, add_remove_room_user
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async

class ChatRoomConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = self.room_name
        print(self.room_group_name)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        await self.authenticate_user()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type' : 'chatroom_message',
                'message' : "add",
                'to' : "all",
                'from' : self.user,
                "event" : "online_traffic",
            }
        )
    
    async def disconnect(self, close_code):      
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type' : 'chatroom_message',
                'to' : "all",
                'from' : self.user,
                'event' : 'online_traffic',
                'message' : "remove"
            }
        )
        await self.authenticate_user(add=False)
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    @sync_to_async
    def get_user_profile(self):
        user = self.scope['user']
        return user.user_profile

    @database_sync_to_async
    def authenticate_user(self, add=True):
        if self.scope['user'].is_authenticated:
            self.room = ChatRoom.objects.get(room_id=self.room_group_name)
            user = self.scope["user"]
            profile = user.user_profile
            self.user = {"id": user.user_profile.unique_id, "name": user.first_name if user.first_name else user.username, "profile_pic": user.user_profile.profile_pic.url}
            if add:
                profile.active = True
                profile.save()
                self.room.online.add(user)
                add_remove_online_user(self.room, user)  # Update the list of active users
            else:
                profile.active = False
                profile.save()
                self.room.online.remove(user)
                add_remove_online_user(self.room, user)  # Update the list of active users
            self.room.save()


    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print(text_data_json)
        msgType = text_data_json.get("type")
        to = text_data_json.get("to")
        from_ = text_data_json.get("from")
        # user_profile = await self.get_user_profile()
        if msgType == "login":
            print(f"[ {from_['id']} logged in. ]")

        elif msgType == "offer":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type' : 'offer',
                    'offer' : text_data_json["offer"],
                    'to' : to,
                    'from' : from_
                }
            )
        
        elif msgType == "answer":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type' : 'answer',
                    'answer' : text_data_json["answer"],
                    'to' : to,
                    'from' : from_
                }
            )
        
        elif msgType == "candidate":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type' : 'candidate',
                    'candidate' : text_data_json["candidate"],
                    'to' : to,
                    'from' : from_
                }
            )
        
        elif msgType == "joiner":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type' : 'joiner',
                    "to" : "all",
                    "from" : from_
                }
            )
        
        elif msgType == "success_join":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type' : 'success_join',
                    "to" : to,
                    "from" : from_
                }
            )
        elif msgType == "chat_message":
            await self.save_message(text_data_json["message"])
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type' : 'chatroom_message',
                    'message' : text_data_json["message"],
                    'to' : from_,
                    'from' : from_,
                    "event" : "chat_message"
                }
            )

        elif msgType == "join_request":
            if self.room.admin.user_profile.unique_id == self.user.id:
                from_ = text_data_json.get("user")
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type' : 'join_request',
                        'to' : self.user,
                        'from' : from_
                    }
                )

    async def chatroom_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type' : event["event"],
            'message': message,
            'to': event["to"],
            'from': event['from']
        }))

    async def offer(self, event):
        await self.send(text_data=json.dumps({
            'type' : 'offer',
            'offer': event['offer'],
            'to': event["to"],
            'from': event['from']
        }))

    async def answer(self, event):
        await self.send(text_data=json.dumps({
            'type' : 'answer',
            'answer': event['answer'],
            'to': event["to"],
            'from': event['from']
        }))

    async def candidate(self, event):
        await self.send(text_data=json.dumps({
            'type' : 'candidate',
            'candidate': event['candidate'],
            'to': event["to"],
            'from': event['from']
        }))
    
    async def joiner(self, event):
        await self.send(text_data=json.dumps({
            'type' : 'joiner',
            'to': event["to"],
            'from': event['from']
        }))

    async def success_join(self, event):
        await self.send(text_data=json.dumps({
            'type' : 'success_join',
            'to': event["to"],
            'from': event['from']
        }))

    
    async def join_request(self, event):
        if event["to"]== self.user["id"]:
            from_ = event.get("user")
            await self.send(text_data=json.dumps({
                'type' : 'join_request',
                'to': self.user,
                'from': from_
            }))


    @database_sync_to_async
    def save_message(self, message):
        msg = Message(user=self.scope['user'], to=self.room, text=message)
        msg.save()