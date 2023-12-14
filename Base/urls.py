from django.urls import path,re_path
from . import views
from .views import UploadFileView

urlpatterns = [
  path('', views.index, name="index"),
  path('contact_us/', views.contact, name="contact_us"),
  path('upload_video', views.upload_view, name="upload_video"),
  path('upload/', UploadFileView.as_view(), name='upload_file'),
  path('login/', views.loginView, name="loginView"),
  path("api/login/", views.user_login, name="login"),
  path("dashboard/", views.dashboard, name="dashboard"),
  path("create_program/", views.create_program, name="create_program"),
  path("programs/", views.program_all, name="program_all"),
  path("all_programs/", views.program_list, name="program_list"),
  path('video_list/', views.video_list, name="video_list"),
  path('stream/<str:room_id>/', views.enterRoom, name='enterRoom'),
  path('join/<str:room_id>/', views.addMeToRoom, name='add_me_to_room'),
  path('path/to/your/endpoint/', views.get_active_users_count, name='get_active_users_count'),
  path('save_meeting_duration/<str:room_id>/<int:duration_minutes>/', views.save_meeting_duration, name='save_meeting_duration'),
  path('manage/online/', views.manageOnlineUsers, name="manageOnlineUsers"),
  path('chat/response/', views.roomResponse, name='roomResponse',),
  path('video/<int:video_id>/record-view/', views.record_post_view, name='record_post_view'),
  path('video/<slug:slug>/submit_comment/', views.submit_comment, name='submit_comment'),
  re_path(r'^watch/(?P<slug>[\w-]+)/$', views.video_view,name="video_detail"),
]