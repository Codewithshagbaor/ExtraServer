from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/user/<str:user_id>/', consumers.UserConsumer.as_asgi()),
]