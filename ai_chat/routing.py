from django.urls import re_path

from .ws_consumers import ChatConsumer


websocket_urlpatterns = [
    re_path(r"^ws/ai-chat/$", ChatConsumer.as_asgi()),
]


