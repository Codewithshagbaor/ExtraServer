from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views import View
from .models import Video,VideoView, Comment, Profile, Contact
from Program.models import Program, ChatRoom, Message
from django.contrib import messages
import random
import string
import uuid
from Program.constants import *
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from ipware import get_client_ip
import requests
from user_agents import parse  # Import the parse function from the user_agents library
from django.contrib.auth import authenticate, login, logout
from datetime import datetime
import datetime
from django.shortcuts import HttpResponse
from .utils import Response
from django.http import JsonResponse
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
channel_layer = get_channel_layer()
from django.core.cache import cache
from Program.service import add_remove_online_user, updateLocationList
from django.views.decorators.csrf import csrf_exempt
from .utils import Response
from datetime import timedelta


from django.utils import timezone
# Create your views here.
from django.contrib.auth.decorators import user_passes_test

def superuser_required(user):
    return user.is_superuser

def index(request):
  program_list = Program.objects.all()[:3]
  context = {
      'program_list':program_list
  }
  return render(request, "index.html", context)
def loginView(request):
    return render(request, "user_login.html")
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user=authenticate(username=username,password=password)
        print(user)
        if user:
            user_profile = user.user_profile
            user_profile.last_login = datetime.datetime.now()
            user_profile.save()
            login(request, user)
            print(user.username + " logged in")
            return Response("success", "successfully logged in", status=200)
        else:
            print("Wrong credentials")
            return Response("failed", "login failed", status=400)
@user_passes_test(superuser_required, login_url='/', redirect_field_name=None)
def dashboard(request):
    program = Program.objects.all().count()
    videos = Video.objects.all().count()
    views = VideoView.objects.all().count()
    comment = Comment.objects.all().count()

    all_comments = Comment.objects.all()
    comments_per_page = 10
    page = request.GET.get('page', 1)
    paginator = Paginator(all_comments, comments_per_page)
    try:
        # Get the specified page from the paginator
        comments = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page
        comments = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver the last page of results
        comments = paginator.page(paginator.num_pages)

    # Calculate the range of comments being displayed
    comment_range_start = (comments.number - 1) * comments_per_page + 1
    comment_range_end = comment_range_start + comments_per_page - 1

    context = {
        'program':program,
        'videos':videos,
        'views':views,
        'comment':comment,
        'comment_range_start': comment_range_start,
        'comment_range_end': comment_range_end,
        'total_comments': all_comments.count(),
        'comments': comments,
    }
    return render(request, "admin/dashboard.html", context)

@user_passes_test(superuser_required, login_url='/', redirect_field_name=None)
def create_program(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        event_date = request.POST['event_date']

        program = Program.objects.create(
            title=title,
            description=description,
            event_date=event_date
        )
        program.save()
        room_id = str(uuid.uuid4().hex)[:8]
        room = ChatRoom(admin=request.user, title=title, program=program, room_id=room_id,)
        room.save()
        room.members.add(request.user)
        room.save()
        print("[ Chatroom created ]")
        messages.success(request, f"Competition created successfully. Your session has been created: {room.title}")
    return render(request, "admin/create_program.html")

@user_passes_test(superuser_required, login_url='/', redirect_field_name=None)
def program_list(request):
    all_programs = Program.objects.all()
    programs_per_page = 10
    page = request.GET.get('page', 1)
    paginator = Paginator(all_programs, programs_per_page)
    try:
        # Get the specified page from the paginator
        programs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page
        programs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver the last page of results
        programs = paginator.page(paginator.num_pages)

    # Calculate the range of comments being displayed
    program_range_start = (programs.number - 1) * programs_per_page + 1
    program_range_end = program_range_start + programs_per_page - 1
    context = {
        'program_range_start': program_range_start,
        'program_range_end': program_range_end,
        'programs': programs,
        'total_programs': all_programs.count(),
    }
    return render(request, "admin/program_view.html", context)

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

def enterRoom(request, room_id):
    room = ChatRoom.objects.get(room_id=room_id)
    if request.user.is_authenticated:
        try:
            print(f"room_id : {room_id}")
            room = ChatRoom.objects.get(room_id=room_id)
            if request.user not in room.members.all():
                room.members.add(request.user)
                room.last_active = datetime.datetime.now()
                room.save()
                
            context = {
                "room": room,
                "messages": room.message_room.all()
            }
            
            if request.user in room.members.all():
                return render(request, "stream/sender2.html", context=context)
            else:
                return render(request, "stream/sender2.html")
                
        except ChatRoom.DoesNotExist as err:
            print(str(err))
            return JsonResponse({})
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        username = 'UID' + ''.join(random.choice(string.digits) for _ in range(10))
        password = generate_random_password()
        user = User.objects.create_user(username=username, password=password, email=email, first_name=name)
        profile = Profile.objects.create(user=user)
        login(request,user)
        print(username + " registered")
        return redirect('add_me_to_room', room.room_id)
    context = {
        'room':room
    }
    return render(request, "stream/sender2.html", context)
    
def manageOnlineUsers(request):
    if request.method == "POST":
        print("[ manageOnlineUsers ]")
        action = request.POST.get("action")
        username = request.POST.get("username")

        online_users = add_remove_online_user(action, username)
        if not online_users:
            return Response(FAILED, "Invalid action provided", status=400)
        
        return Response(SUCCESS, action+" action performed for "+username, data=online_users)
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
    
# In your Django views.py
from django.http import JsonResponse
from Program.models import ChatRoom

def get_active_users_count(request):
    room_id = request.GET.get('room_id', None)

    if room_id is not None:
        try:
            room = ChatRoom.objects.get(room_id=room_id)
            active_users_count = room.online.count()
            return JsonResponse({'count': active_users_count})
        except ChatRoom.DoesNotExist:
            return JsonResponse({'count': 0})
    else:
        return JsonResponse({'count': 0})
def program_all(request):
    all_programs = Program.objects.all()
    programs_per_page = 10
    page = request.GET.get('page', 1)
    paginator = Paginator(all_programs, programs_per_page)
    try:
        # Get the specified page from the paginator
        programs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page
        programs = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver the last page of results
        programs = paginator.page(paginator.num_pages)

    # Calculate the range of comments being displayed
    program_range_start = (programs.number - 1) * programs_per_page + 1
    program_range_end = program_range_start + programs_per_page - 1
    context = {
        'program_range_start': program_range_start,
        'program_range_end': program_range_end,
        'programs': programs,
        'total_programs': all_programs.count(),
    }
    return render(request, "program_all.html", context)
def video_view(request, slug):
    video= get_object_or_404(Video, slug=slug)
    comments = Comment.objects.filter(video=video)
    context = {
        'video':video,
        'comments': comments
    }
    return render(request, 'video/video_view.html', context)

def get_country_from_ip(ip_address):
    # You can replace this with a more accurate GeoIP database or a third-party API
    response = requests.get(f'http://ip-api.com/json/{ip_address}')
    data = response.json()
    return data.get('country', None)

def record_post_view(request, video_id):
    video = get_object_or_404(Video, pk=video_id)
    user_ip, is_routable = get_client_ip(request)
    print(user_ip)
    
    if not VideoView.objects.filter(video=video, user_ip=user_ip).exists():
        # If the user hasn't viewed the post, create a VideoView entry
        video_view = VideoView.objects.create(video=video, user_ip=user_ip)
        user_agent = parse(request.META.get('HTTP_USER_AGENT', ''))
        video_view.device_os = user_agent.os.family

        # Get country information
        video_view.country = get_country_from_ip(user_ip)

        video_view.save()

    return JsonResponse({'message': 'View recorded'})
@require_POST
def submit_comment(request, slug):
    video = get_object_or_404(Video, slug=slug)
    username = request.POST.get('username')
    comment_text = request.POST.get('comment_text')
    
    if username and comment_text:
        comment = Comment(video=video, username=username, comment_text=comment_text)
        comment.save()
        
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Username and comment text are required.'})

def generate_random_password(length=8):
    import random
    import string

    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))
def addMeToRoom(request, room_id):
    room = ChatRoom.objects.get(room_id=room_id)
    if request.user.is_authenticated:
        try:
            print(f"room_id : {room_id}")
            room = ChatRoom.objects.get(room_id=room_id)
            if request.user not in room.members.all():
                room.members.add(request.user)
                room.last_active = datetime.datetime.now()
                room.save()
                
            return render(request, "adding_user.html", {"room": room})
                
        except ChatRoom.DoesNotExist as err:
            print(str(err))
            return JsonResponse({})
        
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        username = 'UID' + ''.join(random.choice(string.digits) for _ in range(10))
        password = generate_random_password()
        user = User.objects.create_user(username=username, password=password, email=email, first_name=name)
        profile = Profile.objects.create(user=user)
        login(request,user)
        print(username + " registered")

    return render(request, "adding_user.html", {"room": room})

def contact(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        subject = request.POST['subject']
        message = request.POST['message']
        contact = Contact.objects.create(name=name, email=email, subject=subject, message=message)
        context = {
            'contact':contact
        }
        return render(request, "contact_submitted.html", context)
    return render(request, "contact_page.html")

@user_passes_test(superuser_required, login_url='/', redirect_field_name=None)
def upload_view(request):
    return render(request, "video/upload_view.html")

@user_passes_test(superuser_required, login_url='/', redirect_field_name=None)
def video_list(request):
    all_videos = Video.objects.all()
    videos_per_page = 10
    page = request.GET.get('page', 1)
    paginator = Paginator(all_videos, videos_per_page)
    try:
        # Get the specified page from the paginator
        videos = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page
        videos = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver the last page of results
        videos = paginator.page(paginator.num_pages)

    # Calculate the range of comments being displayed
    video_range_start = (videos.number - 1) * videos_per_page + 1
    video_range_end = video_range_start + videos_per_page - 1
    context = {
        'video_range_start': video_range_start,
        'video_range_end': video_range_end,
        'videos': videos,
        'total_videos': all_videos.count(),
    }
    return render(request, "admin/video_list.html", context)
class UploadFileView(View):
    def post(self, request, *args, **kwargs):
        try:
            uploaded_file = request.FILES['uploaded_file']
        except KeyError:
            return JsonResponse({'error': 'No file was uploaded.'}, status=400)
        
        # Get the title and description from the form data
        title = request.POST.get('title', 'Default Title')
        description = request.POST.get('description', 'Default Description')

        # Create a new Video instance and set the fields
        new_video = Video(
            title=title,
            description=description,
        )
        new_video.video_file.save(uploaded_file.name, uploaded_file, save=True)
        new_video.slug = slugify(title)
        new_video.save()

        return JsonResponse({'message': 'File uploaded successfully.'})
    
def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)