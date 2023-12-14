from django.contrib.auth import login
from django.http.response import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404

# Create your views here.
import uuid
from django.core.cache import cache

from Program.models import Program, ChatRoom, Message
from .utils import Response
from .constants import *
from .service import add_remove_online_user, updateLocationList
from django.contrib.auth.decorators import login_required
import uuid
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse
from Base.models import Profile
from .email import emailSend
import os
from django.contrib.auth import get_user_model
User = get_user_model()
from django.db.models import Count

channel_layer = get_channel_layer()

def home(request):
    if request.method == "GET":
        context = {}
        if request.user.is_authenticated:
            rooms = ChatRoom.objects.filter(members__in=[request.user]).order_by("-last_active")
            context={
                "rooms": rooms
            }
        return render(request, "home.html", context)
    else:
        room_id = request.POST.get("room_id")
        try:
            room = ChatRoom.objects.get(room_id=room_id)
            return redirect("Competetion:enterRoom", room_id=room_id)
        except Exception as err:
            print(str(err)+ " home "+room_id)
            context = {}
            if request.user.is_authenticated:
                rooms = ChatRoom.objects.filter(members__in=[request.user]).order_by("-last_active")[:3]
                context={
                    "rooms": rooms
                }
            return render(request, "home.html", context)

@login_required
def startRoom(request):
    room_id = str(uuid.uuid4().hex)[:8]
    room = ChatRoom(admin=request.user, room_id=room_id)
    room.save()
    room.members.add(request.user)
    room.save()
    print("[ Chatroom created ]")
    return redirect("Program:enterRoom", room_id=room_id)



@login_required
def roomResponse(request):
    print("hello", request.GET)
    room_id = request.GET.get("roomid")
    userid = request.GET.get("userid")
    resp = request.GET.get("resp")
    try:
        room = ChatRoom.objects.get(room_id=room_id)
        if request.user == room.admin:
            msg = {
                "response": resp,
                "type": "room_request",
                "room_id": room.room_id
            }
            if resp == "accept":
                user = Profile.objects.get(unique_id=userid)
                room.members.add(user.user)
                room.save()
            async_to_sync(channel_layer.group_send)(userid ,msg)
    except Exception as err:
        print(str(err))
    return JsonResponse({})

@login_required
def enterRoom(request, room_id):
    try:
        print(f"room_id : {room_id}")
        room = ChatRoom.objects.get(room_id=room_id)
        if request.user not in room.members.all():
            room.members.add(request.user)
            room.last_active = datetime.now()
            room.save()
            
        context = {
            "room": room,
            "messages": room.message_room.all()
        }
        
        if request.user in room.members.all():
            return render(request, "sender2.html", context=context)
        else:
            return render(request, "user.html")
            
    except ChatRoom.DoesNotExist as err:
        print(str(err))
        return JsonResponse({})
@login_required
def addMeToRoom(request, room_id):
    try:
        print(f"room_id : {room_id}")
        room = ChatRoom.objects.get(room_id=room_id)
        if request.user not in room.members.all():
            room.members.add(request.user)
            room.last_active = datetime.now()
            room.save()
            
        return render(request, "adding_user.html", {"room": room})
            
    except ChatRoom.DoesNotExist as err:
        print(str(err))
        return JsonResponse({})
    
def manageOnlineUsers(request):
    if request.method == "POST":
        print("[ manageOnlineUsers ]")
        action = request.POST.get("action")
        username = request.POST.get("username")

        online_users = add_remove_online_user(action, username)
        if not online_users:
            return Response(FAILED, "Invalid action provided", status=400)
        
        return Response(SUCCESS, action+" action performed for "+username, data=online_users)
    
@login_required
def deleteRoom(request, room_id):
    try:
        room = ChatRoom.objects.get(room_id=room_id)
        room.delete()
        return JsonResponse({"result": True})
    except Exception as err:
        print(str(err))
        return JsonResponse({"result": False})


from datetime import timedelta

from django.utils import timezone

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def save_meeting_duration(request, room_id, duration_minutes):
    if request.method == 'POST':
        try:
            chatroom = ChatRoom.objects.get(room_id=room_id)
            
            # Convert duration_minutes to a timedelta object
            duration_seconds = duration_minutes * 60
            duration_timedelta = timedelta(seconds=duration_seconds)
            
            # Get the duration from the JSON payload
            data = json.loads(request.body)
            duration_iso = data.get('duration')
            
            # Update meeting_duration and last_active fields
            chatroom.meeting_duration = duration_timedelta
            chatroom.last_active = timezone.now()
            chatroom.save()
            
            return JsonResponse({"message": "Meeting duration saved successfully."})
        except ChatRoom.DoesNotExist:
            return JsonResponse({"message": "Chat room not found."}, status=404)
    else:
        return JsonResponse({"message": "Invalid request method."}, status=400)

@login_required
def competition_details(request, program_slug):
    program = get_object_or_404(Program, slug=program_slug)
    host_chat_room = ChatRoom.objects.get(admin=program.host.user, program=program)
        # Retrieve the admin's chat room
    admin = User.objects.get(username='Dxtwurld')  # Replace 'admin' with your actual admin username
    admin_chat_room = ChatRoom.objects.get(admin=admin, program=program)
    context = {
        'program': program,
        'host_chat_room': host_chat_room,
        'admin_chat_room': admin_chat_room,
    }

    return render(request, 'competition_details.html', context)