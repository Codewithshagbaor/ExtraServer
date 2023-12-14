import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Configs.settings')

django_asgi_app = get_asgi_application()


from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

import Program.routing
import Base.routing

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,

    # WebSocket chat handler
    'websocket': AuthMiddlewareStack(
        URLRouter(
            Program.routing.websocket_urlpatterns + Base.routing.websocket_urlpatterns
        )
    ),


})
