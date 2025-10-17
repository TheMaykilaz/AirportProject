from django.urls import path
from . import views

app_name = 'ai_chat'

urlpatterns = [
    path('chat/', views.ai_chat_window, name='chat_window'),
    path('api/ai-chat/api/chat/', views.ai_chat_api, name='chat_api'),
    path('api/chat-completion/', views.ai_chat_completion, name='chat_completion'),
    path('settings/', views.ai_chat_settings, name='settings'),
    path('health/', views.health_check, name='health_check'),
]