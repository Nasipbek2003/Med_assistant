from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('history/', views.chat_history, name='chat_history'),
    path('session/<int:session_id>/', views.view_session, name='view_session'),
    path('send_message/', views.send_message, name='send_message'),
    path('new/', views.new_chat, name='new_chat'),
] 