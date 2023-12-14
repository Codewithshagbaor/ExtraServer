from django.urls import path
from . import views

app_name = "Program"

urlpatterns = [
    path('', views.home, name='home'),
    path('start/chat/', views.startRoom, name='startRoom'),
    path('chat/<str:room_id>', views.enterRoom, name='enterRoom'),
    path('join/<str:room_id>/', views.addMeToRoom, name='add_me_to_room'),
    path('save_meeting_duration/<str:room_id>/<int:duration_minutes>/', views.save_meeting_duration, name='save_meeting_duration'),
    path('manage/online/', views.manageOnlineUsers, name="manageOnlineUsers"),
    path('<slug:competition_slug>/', views.competition_details, name='competition_details'),
]
