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
import re

DEEPSEEK_API_KEY = "sk-fcb5625eb8af4bc18316cb8330371ce4"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def format_text_to_html(text):
    """
    Преобразует текст с markdown-подобной разметкой в HTML.
    
    Args:
        text (str): Исходный текст с разметкой
        
    Returns:
        str: Отформатированный HTML
    """
    # Сначала обрабатываем жирный текст
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Сначала обрабатываем списки, так как они могут содержать переносы строк
    lines = text.split('\n')
    formatted_lines = []
    in_list = False
    list_type = None
    list_items = []
    
    for line in lines:
        line = line.strip()
        if not line:  # Пустая строка
            if in_list:  # Закрываем список, если он открыт
                if list_type == 'ul':
                    formatted_lines.append('<ul>' + ''.join(list_items) + '</ul>')
                else:
                    formatted_lines.append('<ol>' + ''.join(list_items) + '</ol>')
                in_list = False
                list_items = []
            formatted_lines.append('')
            continue
            
        # Проверяем, является ли строка элементом списка
        if line.startswith(('- ', '* ')):  # Маркированный список
            if not in_list or list_type != 'ul':
                if in_list:  # Закрываем предыдущий список другого типа
                    if list_type == 'ul':
                        formatted_lines.append('<ul>' + ''.join(list_items) + '</ul>')
                    else:
                        formatted_lines.append('<ol>' + ''.join(list_items) + '</ol>')
                    list_items = []
                in_list = True
                list_type = 'ul'
            list_items.append(f'<li>{line[2:]}</li>')
        elif re.match(r'^\d+\.\s', line):  # Нумерованный список
            if not in_list or list_type != 'ol':
                if in_list:  # Закрываем предыдущий список другого типа
                    if list_type == 'ul':
                        formatted_lines.append('<ul>' + ''.join(list_items) + '</ul>')
                    else:
                        formatted_lines.append('<ol>' + ''.join(list_items) + '</ol>')
                    list_items = []
                in_list = True
                list_type = 'ol'
            list_items.append(f'<li>{re.sub(r"^\d+\.\s", "", line)}</li>')
        else:  # Обычный текст
            if in_list:  # Закрываем список, если он был открыт
                if list_type == 'ul':
                    formatted_lines.append('<ul>' + ''.join(list_items) + '</ul>')
                else:
                    formatted_lines.append('<ol>' + ''.join(list_items) + '</ol>')
                in_list = False
                list_items = []
            formatted_lines.append(line)
    
    # Закрываем последний список, если он остался открытым
    if in_list:
        if list_type == 'ul':
            formatted_lines.append('<ul>' + ''.join(list_items) + '</ul>')
        else:
            formatted_lines.append('<ol>' + ''.join(list_items) + '</ol>')
    
    # Объединяем строки и разбиваем на абзацы
    text = '\n'.join(formatted_lines)
    paragraphs = text.split('\n\n')
    formatted_paragraphs = []
    
    for p in paragraphs:
        if p.strip():
            # Если это не список (не начинается с <ul> или <ol>)
            if not (p.startswith('<ul>') or p.startswith('<ol>')):
                # Обрабатываем заголовки
                if p.startswith('### '):
                    p = f'<h3>{p[4:]}</h3>'
                # Оборачиваем в теги параграфа
                elif not p.startswith('<h3>'):
                    p = f'<p>{p}</p>'
            formatted_paragraphs.append(p)
    
    # Объединяем всё в финальный HTML
    html = '\n'.join(formatted_paragraphs)
    
    # Заменяем одиночные переносы строк на <br>
    html = re.sub(r'(?<!>)\n(?!<)', '<br>', html)
    
    return html

def get_ai_response(request, message):
    try:
        # Формируем запрос к DeepSeek API
        headers = {
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system", 
                    "content": """Вы - профессиональный медицинский ассистент. 
                    Отвечайте на русском языке. Используйте форматирование для улучшения читаемости:
                    - Начинайте с заголовка ### для основной темы
                    - Разделяйте абзацы двойным переносом строки
                    - Используйте **жирный текст** для важных моментов
                    - Используйте списки (- или 1.) для перечисления
                    В конце добавляйте предупреждение о необходимости консультации с врачом."""
                },
                {
                    "role": "user", 
                    "content": message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.95,
            "stream": False
        }
        
        print(f"Отправляем запрос к DeepSeek API: {DEEPSEEK_API_URL}")  # Отладочный вывод
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        print(f"Получен ответ от API. Статус: {response.status_code}")  # Отладочный вывод
        
        if response.status_code != 200:
            print(f"Ошибка API: {response.text}")  # Отладочный вывод
            raise requests.exceptions.RequestException(f"API вернул статус {response.status_code}")
            
        response_data = response.json()
        print(f"Ответ API: {response_data}")  # Отладочный вывод
        
        if 'choices' in response_data and len(response_data['choices']) > 0:
            response_text = response_data['choices'][0]['message']['content'].strip()
            formatted_html = format_text_to_html(response_text)
            
            return {
                'response': formatted_html,
                'status': 'success'
            }
        else:
            raise Exception('Неверный формат ответа от API')
            
    except requests.exceptions.RequestException as e:
        print(f"Ошибка API запроса: {str(e)}")
        return {
            'response': '<p>Извините, произошла ошибка при получении ответа от сервера. Пожалуйста, проверьте подключение к интернету или попробуйте позже. При срочных вопросах обратитесь к врачу.</p>',
            'status': 'error'
        }
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return {
            'response': '<p>Извините, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже. При срочных вопросах обратитесь к врачу.</p>',
            'status': 'error'
        }

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

    # Проверяем, подтвердил ли врач запись
    chat_with_doctor = active_session.doctor_confirmed if active_session else False
    doctor_messages = []
    if chat_with_doctor:
        doctor_messages = Message.objects.filter(
            session=active_session,
            sender__in=['user', 'doctor']
        ).order_by('created_at')

    # Получаем все сессии пользователя для отображения в боковой панели
    user_chats = ChatSession.objects.filter(user=request.user).order_by('-last_activity')

    context = {
        'session': active_session,
        'messages': messages,
        'chat_with_doctor': chat_with_doctor,
        'doctor_messages': doctor_messages,
        'user_chats': user_chats,
        'active_chat_id': active_session.id if active_session else None,
    }
    return render(request, 'chat.html', context)

@login_required
@require_http_methods(["POST", "GET"])
def new_chat(request):
    # Деактивируем текущую активную сессию
    ChatSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
    # Создаем новую сессию
    session = ChatSession.objects.create(
        user=request.user,
        title="Новая консультация",
        is_active=True
    )
    return redirect('chat')

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
            # Ищем активную сессию. Используем first() вместо get() для надежности,
            # если по какой-то причине их несколько, или нет ни одной.
            session = ChatSession.objects.filter(user=request.user, is_active=True).first()

            if not session:
                 return JsonResponse({'error': 'Активная сессия чата не найдена'}, status=404)
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

        # Получаем ответ от DeepSeek API
        bot_response = get_ai_response(request, message_text)

        # Сохраняем ответ бота
        bot_message = Message.objects.create(
            session=session,
            sender='assistant',
            content=bot_response['response']
        )

        # Обновляем время последней активности
        session.last_activity = timezone.now()
        session.save()

        # Если это первое сообщение в сессии, обновляем заголовок
        if session.messages.count() <= 3:  # Учитываем приветственное сообщение
            session.title = message_text[:50] + ('...' if len(message_text) > 50 else '')
            session.save()

        return JsonResponse({
            'response': bot_response['response'],
            'timestamp': timezone.now().isoformat(),
            'status': bot_response['status']
        })

    except Exception as e:
        print(f"Error in send_message: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def chat_history(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by('-last_activity')
    print(f"DEBUG: Found {sessions.count()} chat sessions for user {request.user.username}") # Отладочный вывод
    return render(request, 'chat_history.html', {'sessions': sessions})

@login_required
def view_session(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    messages = session.messages.all().order_by('created_at')

    # Получаем все сессии пользователя для отображения в боковой панели
    user_chats = ChatSession.objects.filter(user=request.user).order_by('-last_activity')

    return render(request, 'chat.html', {
        'session': session,
        'messages': messages,
        'chat_with_doctor': session.doctor_confirmed,
        'doctor_messages': messages.filter(sender__in=['user', 'doctor']),
        'user_chats': user_chats,
        'active_chat_id': session.id,
    })

@login_required
def profile_view(request):
    if hasattr(request.user, 'is_doctor') and request.user.is_doctor():
        return redirect('doctor_dashboard')
    elif hasattr(request.user, 'is_patient') and request.user.is_patient():
        return redirect('patient_dashboard')
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
                if hasattr(user, 'is_doctor') and user.is_doctor():
                    return redirect('doctor_dashboard')
                elif hasattr(user, 'is_patient') and user.is_patient():
                    return redirect('patient_dashboard')
                return redirect('profile')  # fallback
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

@login_required
@require_http_methods(["POST"])
def doctor_send_message(request):
    message_text = request.POST.get('message')
    session_id = request.GET.get('session_id')
    if not message_text or not session_id:
        return JsonResponse({'status': 'error', 'message': 'Missing message or session_id'}, status=400)
    
    session = ChatSession.objects.filter(id=session_id, user=request.user).first()
    if not session or not session.doctor_confirmed:
        return JsonResponse({'status': 'error', 'message': 'Invalid session or doctor not confirmed'}, status=400)
    
    message = Message.objects.create(
        session=session,
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