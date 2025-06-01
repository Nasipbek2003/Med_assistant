from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Message
from accounts.models import User

@login_required
def chat_view(request):
    # Получаем список чатов пользователя
    user_chats = Chat.objects.filter(user=request.user).order_by('-created_at')
    active_chat_id = request.GET.get('chat_id')
    messages = []
    if active_chat_id:
        messages = Message.objects.filter(chat_id=active_chat_id).order_by('created_at')

    # Проверяем, подтвердил ли врач запись
    chat_with_doctor = False
    doctor_messages = []
    if active_chat_id:
        chat = Chat.objects.filter(id=active_chat_id, user=request.user).first()
        if chat and chat.doctor_confirmed:
            chat_with_doctor = True
            doctor_messages = Message.objects.filter(chat_id=active_chat_id, sender__in=['user', 'doctor']).order_by('created_at')

    # Получаем всех врачей
    doctors = User.objects.filter(role='doctor', is_active=True)

    context = {
        'user_chats': user_chats,
        'active_chat_id': active_chat_id,
        'messages': messages,
        'chat_with_doctor': chat_with_doctor,
        'doctor_messages': doctor_messages,
        'doctors': doctors,
    }
    return render(request, 'chat.html', context)

@login_required
@require_http_methods(["POST"])
def doctor_send_message(request):
    message_text = request.POST.get('message')
    chat_id = request.GET.get('chat_id')
    if not message_text or not chat_id:
        return JsonResponse({'status': 'error', 'message': 'Missing message or chat_id'}, status=400)
    
    chat = Chat.objects.filter(id=chat_id, user=request.user).first()
    if not chat or not chat.doctor_confirmed:
        return JsonResponse({'status': 'error', 'message': 'Invalid chat or doctor not confirmed'}, status=400)
    
    message = Message.objects.create(
        chat_id=chat_id,
        content=message_text,
        sender='user'
    )
    
    return JsonResponse({
        'status': 'success',
        'message': {
            'id': message.id,
            'content': message.content,
            'created_at': message.created_at.strftime('%H:%M')
        }
    }) 