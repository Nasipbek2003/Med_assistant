from django.urls import path
from . import views
 
urlpatterns = [
    # ... существующие URL ...
    path('chat/doctor/send/', views.doctor_send_message, name='doctor_send_message'),
] 