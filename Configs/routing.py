from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import Base.routing
import Program.routing

print(Program.routing.websocket_urlpatterns + Base.routing.websocket_urlpatterns)

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            Program.routing.websocket_urlpatterns+ Base.routing.websocket_urlpatterns
        )

    ),

})