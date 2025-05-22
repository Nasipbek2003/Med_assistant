from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('doctor/send/', views.doctor_send_message, name='doctor_send_message'),
    path('new/', views.new_chat, name='chat_new'),
    path('session/<int:session_id>/', views.view_session, name='chat_session'),
    path('history/', views.chat_history, name='chat_history'),
    path('send_message/', views.send_message, name='send_message'),
] 