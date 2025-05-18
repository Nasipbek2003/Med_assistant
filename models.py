from django.db import models
from django.contrib.auth.models import User

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    doctor_confirmed = models.BooleanField(default=False)
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='doctor_chats')

    class Meta:
        ordering = ['-created_at']

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    content = models.TextField()
    sender = models.CharField(max_length=10)  # 'user' или 'doctor'
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at'] 