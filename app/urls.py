from django.urls import path
from . import views

urlpatterns = [
    # ... existing urls ...
    path('chat/', views.chat_view, name='chat'),
    path('chat/api/', views.chat_api, name='chat_api'),
    path('doctors/<str:specialty>/', views.doctors_by_specialty, name='doctors_by_specialty'),
    path('doctors/', views.doctors_by_specialty, {'specialty': 'all'}, name='doctors_all'),
    path('appointment/<int:doctor_id>/', views.appointment_create, name='appointment_create'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('doctor/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/appointment/<int:appointment_id>/update/', views.appointment_update, name='appointment_update'),
] 