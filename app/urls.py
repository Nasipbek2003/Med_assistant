from django.urls import path
from . import views

urlpatterns = [
    # ... existing urls ...
    path('my-slots/', views.my_slots, name='my_slots'),
    path('my-slots/add/', views.slot_add, name='slot_add'),
    path('my-slots/<int:slot_id>/edit/', views.slot_edit, name='slot_edit'),
    path('my-slots/<int:slot_id>/delete/', views.slot_delete, name='slot_delete'),
    path('chat/', views.chat_view, name='chat'),
    path('chat/api/', views.chat_api, name='chat_api'),
    path('doctors/<str:specialty>/', views.doctors_by_specialty, name='doctors_by_specialty'),
    path('doctors/', views.doctors_by_specialty, {'specialty': 'all'}, name='doctors_all'),
    path('appointment/<int:doctor_id>/', views.appointment_create, name='appointment_create'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('doctor/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/appointment/<int:appointment_id>/update/', views.appointment_update, name='appointment_update'),
    path('doctor/<int:doctor_id>/slots/', views.doctor_slots, name='doctor_slots'),
    path('slot/<int:slot_id>/book/', views.book_slot, name='book_slot'),
] 