from django.urls import path
from . import views

urlpatterns = [
    # ... existing urls ...
    path('chat/', views.chat_view, name='chat'),
    path('api/chat/', views.chat_api, name='chat_api'),
] 