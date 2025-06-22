from django.db import models
from django.conf import settings
from django.utils import timezone

class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    title = models.CharField(max_length=255, blank=True)
    doctor_confirmed = models.BooleanField(default=False)
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='doctor_chats')
    type = models.CharField(max_length=50, blank=True, null=True)
    
    # Поля для опроса пациента
    is_survey_completed = models.BooleanField(default=False)
    patient_age = models.IntegerField(blank=True, null=True)
    patient_gender = models.CharField(max_length=10, blank=True, null=True)
    patient_symptoms = models.TextField(blank=True, null=True)
    survey_step = models.IntegerField(default=0)

    def __str__(self):
        return f"Сессия {self.id} - {self.user.username}"

    def get_first_message(self):
        return self.messages.first()

    class Meta:
        ordering = ['-last_activity']

class Message(models.Model):
    SENDER_CHOICES = [
        ('user', 'Пользователь'),
        ('assistant', 'Ассистент'),
        ('doctor', 'Врач'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} - {self.created_at.strftime('%d.%m.%Y %H:%M')}"

    class Meta:
        ordering = ['created_at'] 