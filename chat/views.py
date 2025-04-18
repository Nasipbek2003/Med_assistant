from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from .models import ChatSession, Message
import json
import requests
from django.conf import settings
import os
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'your-api-key-here')
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def get_ai_response(message, session_history):
    """Получение ответа от DeepSeek API"""
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Формируем историю диалога для контекста
    messages = []
    for msg in session_history:
        role = "user" if msg.sender == "user" else "assistant"
        messages.append({"role": role, "content": msg.content})
    
    # Добавляем текущее сообщение
    messages.append({"role": "user", "content": message})
    
    # Добавляем системный промпт для медицинского контекста
    system_message = {
        "role": "system",
        "content": """Вы - медицинский ассистент, который помогает пользователям с вопросами о здоровье. 

Ваши ответы должны быть:
1. Профессиональными, но понятными для обычного человека
2. Основанными на научных данных и современных медицинских рекомендациях
3. Содержать предупреждение о необходимости консультации с врачом при серьезных симптомах
4. Не включать постановку диагнозов
5. Фокусироваться на общих рекомендациях по здоровому образу жизни и профилактике
6. Отвечать на русском языке

При ответе на вопросы:
- Всегда рекомендуйте обратиться к врачу при серьезных симптомах
- Не давайте рекомендаций по лекарствам без рецепта
- Подчеркивайте важность профилактики и здорового образа жизни
- Используйте простой и понятный язык
- Структурируйте ответы для лучшего восприятия
- Используйте маркированные списки и абзацы для лучшей читаемости
- Выделяйте важную информацию жирным шрифтом

Формат ответа:
1. Всегда используйте markdown для форматирования
2. Разделяйте текст на абзацы
3. Используйте списки где это уместно
4. Важную информацию выделяйте **жирным**"""
    }
    messages.insert(0, system_message)
    
    try:
        response = requests.post(
            settings.DEEPSEEK_API_URL,
            headers=headers,
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000,
                "presence_penalty": 0.6,
                "frequency_penalty": 0.5
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        print(f"Error calling DeepSeek API: {str(e)}")
        return """**Извините, произошла ошибка при обработке вашего запроса.**

Пожалуйста:
1. Проверьте ваше интернет-соединение
2. Попробуйте отправить сообщение еще раз
3. Если проблема повторяется, попробуйте позже"""

@login_required
def chat_view(request):
    if not request.user.is_authenticated:
        return redirect(f"{settings.LOGIN_URL}?next={reverse('chat')}")
    
    # Получаем активную сессию или создаем новую
    active_session = ChatSession.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if not active_session:
        active_session = ChatSession.objects.create(
            user=request.user,
            title="Новая консультация"
        )

    # Получаем сообщения для текущей сессии
    messages = Message.objects.filter(
        session=active_session
    ).order_by('created_at')

    return render(request, 'chat.html', {
        'messages': messages,
        'session': active_session
    })

@login_required
@csrf_protect
@require_http_methods(["POST"])
def new_chat(request):
    try:
        print("Creating new chat session") # Отладочный вывод
        
        # Деактивируем текущую активную сессию
        ChatSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
        print("Deactivated old sessions") # Отладочный вывод
        
        # Создаем новую сессию
        session = ChatSession.objects.create(
            user=request.user,
            title="Новая консультация",
            is_active=True  # Явно устанавливаем флаг активности
        )
        print(f"Created new session with ID: {session.id}") # Отладочный вывод
        
        # Создаем приветственное сообщение
        welcome_message = Message.objects.create(
            session=session,
            sender='assistant',
            content='Здравствуйте! Я ваш медицинский ассистент. Как я могу вам помочь?'
        )
        print(f"Created welcome message with ID: {welcome_message.id}") # Отладочный вывод
        
        response_data = {
            'status': 'success',
            'message': welcome_message.content,
            'timestamp': welcome_message.created_at.isoformat(),
            'session_id': session.id
        }
        print("Sending response:", response_data) # Отладочный вывод
        
        return JsonResponse(response_data)
    except Exception as e:
        print(f"Error in new_chat: {str(e)}") # Отладочный вывод
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def send_message(request):
    try:
        data = json.loads(request.body)
        message_text = data.get('message')
        
        if not message_text:
            return JsonResponse({'error': 'Сообщение не может быть пустым'}, status=400)

        # Получаем активную сессию
        try:
            session = ChatSession.objects.get(user=request.user, is_active=True)
        except ChatSession.DoesNotExist:
            # Если активной сессии нет, создаем новую
            session = ChatSession.objects.create(
                user=request.user,
                title="Новая консультация"
            )
            Message.objects.create(
                session=session,
                sender='assistant',
                content='Здравствуйте! Я ваш медицинский ассистент. Как я могу вам помочь?'
            )
        
        # Сохраняем сообщение пользователя
        user_message = Message.objects.create(
            session=session,
            sender='user',
            content=message_text
        )

        # Получаем историю диалога для контекста
        session_history = session.messages.all()
        
        # Получаем ответ от DeepSeek API
        bot_response = get_ai_response(message_text, session_history)

        # Сохраняем ответ бота
        bot_message = Message.objects.create(
            session=session,
            sender='assistant',
            content=bot_response
        )

        # Обновляем время последней активности
        session.last_activity = timezone.now()
        session.save()

        # Если это первое сообщение в сессии, обновляем заголовок
        if session.messages.count() <= 3:  # Учитываем приветственное сообщение
            session.title = message_text[:50] + ('...' if len(message_text) > 50 else '')
            session.save()

        return JsonResponse({
            'response': bot_response,
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        print(f"Error in send_message: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def chat_history(request):
    # Получаем все сессии пользователя
    sessions = ChatSession.objects.filter(user=request.user).order_by('-last_activity')
    return render(request, 'chat_history.html', {'sessions': sessions})

@login_required
def view_session(request, session_id):
    # Просмотр конкретной сессии
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    messages = session.messages.all()
    return render(request, 'chat_session.html', {
        'session': session,
        'messages': messages
    })

@login_required
def profile_view(request):
    # Получаем все сессии пользователя, отсортированные по дате
    chat_sessions = ChatSession.objects.filter(user=request.user).order_by('-last_activity')
    
    context = {
        'user': request.user,
        'chat_sessions': chat_sessions,
    }
    return render(request, 'profile.html', context)

# Обновляем login_view для перенаправления на профиль
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('profile')  # Перенаправляем на профиль после входа
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form}) 