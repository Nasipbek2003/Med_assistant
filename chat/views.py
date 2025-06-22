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
from accounts.models import User
import markdown2

DEEPSEEK_API_KEY = "sk-fcb5625eb8af4bc18316cb8330371ce4"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def format_text_to_html(text):
    """
    Преобразует текст с Markdown-подобной разметкой в HTML,
    применяя агрессивную очистку для удаления артефактов форматирования.
    """
    # Шаг 1: Удаляем строки, состоящие только из небуквенных символов (маркеры, знаки препинания)
    # Это решает проблему "блуждающих" маркеров списка.
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Удаляем строку, если после удаления пробелов в ней не остается букв или цифр.
        # Это эффективно убирает строки типа "*", "-", "•", "* * *", "---"
        if not re.search(r'[a-zA-Zа-яА-Я0-9]', line):
            continue
        cleaned_lines.append(line)
    
    cleaned_text = '\n'.join(cleaned_lines)
    
    # Шаг 2: Заменяем множественные переносы строк на один, чтобы убрать лишние пустые пространства.
    processed_text = re.sub(r'\n{2,}', '\n', cleaned_text).strip()
    
    # Шаг 3: Преобразуем очищенный Markdown в HTML
    html = markdown2.markdown(
        processed_text, 
        extras=["fenced-code-blocks", "cuddled-lists", "tables", "strike", "break-on-newline"]
    )
    
    # Шаг 4: Принудительно заменяем нумерованные списки на маркированные, чтобы избежать ошибок форматирования.
    html = html.replace('<ol>', '<ul>').replace('</ol>', '</ul>')
    
    return html

def get_ai_response(request, message, max_tokens=2000):
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
            "max_tokens": max_tokens,
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
    # Передаём список врачей в шаблон
    context['doctors'] = User.objects.filter(role='doctor', is_active=True)
    context['all_users'] = User.objects.all()
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
        is_active=True,
        is_survey_completed=False,
        survey_step=0
    )
    
    # Создаем приветственное сообщение с первым вопросом
    welcome_message = """Здравствуйте! Я ваш медицинский ассистент. 

Для того чтобы я мог лучше вам помочь, мне нужно задать несколько вопросов.

**Вопрос 1:** Сколько вам лет?"""
    
    Message.objects.create(
        session=session,
        sender='assistant',
        content=format_text_to_html(welcome_message)
    )
    
    return redirect('chat')

def get_chat_title_from_ai(message_history):
    """
    Генерирует заголовок для чата с помощью AI на основе истории сообщений.
    """
    try:
        history_str = "\n".join([f"{msg.sender}: {msg.content}" for msg in message_history])
        
        prompt = f"""Ниже приведена история сообщений между пользователем и медицинским ассистентом. 
Проанализируй ее и предложи короткий (2-4 слова), емкий заголовок для этого чата на русском языке. 
Заголовок должен отражать основную тему или проблему, обсуждаемую в чате.
Не добавляй кавычки или слово "Заголовок". Просто напиши сам заголовок.

История:
---
{history_str}
---
Заголовок:"""

        headers = {
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 20,
            "stream": False
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            response_data = response.json()
            if 'choices' in response_data and len(response_data['choices']) > 0:
                title = response_data['choices'][0]['message']['content'].strip()
                # Убираем кавычки, если они есть
                title = title.replace('"', '').replace("'", '')
                return title
    except Exception as e:
        print(f"Ошибка при генерации заголовка чата: {e}")
    
    return None

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
                title="Новая консультация",
                is_survey_completed=False,
                survey_step=0
            )
            Message.objects.create(
                session=session,
                sender='assistant',
                content=format_text_to_html('Здравствуйте! Я ваш медицинский ассистент. Как я могу вам помочь?')
            )
        
        # Сохраняем сообщение пользователя
        user_message = Message.objects.create(
            session=session,
            sender='user',
            content=message_text
        )

        # Обработка опроса
        if not session.is_survey_completed:
            bot_response = handle_survey(session, message_text)
            # Форматируем ответ опроса через HTML
            if bot_response['status'] == 'success':
                bot_response['response'] = format_text_to_html(bot_response['response'])
        else:
            # Приветствие
            greetings = [
                'привет', 'здравствуйте', 'добрый день', 'добрый вечер', 'доброе утро',
                'hi', 'hello', 'hey'
            ]
            if message_text.strip().lower() in greetings:
                greet_response = format_text_to_html('Здравствуйте! Чем могу помочь?')
                bot_message = Message.objects.create(
                    session=session,
                    sender='assistant',
                    content=greet_response
                )
                session.last_activity = timezone.now()
                session.save()
                if session.messages.count() <= 3:
                    session.title = message_text[:50] + ('...' if len(message_text) > 50 else '')
                    session.save()
                return JsonResponse({
                    'response': greet_response,
                    'timestamp': timezone.now().isoformat(),
                    'status': 'success'
                })

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

        json_response_data = {
            'response': bot_response['response'],
            'timestamp': timezone.now().isoformat(),
            'status': bot_response.get('status', 'success'),
            'new_title': bot_response.get('new_title')
        }

        return JsonResponse(json_response_data)

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

    # Получаем всех врачей
    doctors = User.objects.filter(role='doctor', is_active=True)

    return render(request, 'chat.html', {
        'session': session,
        'messages': messages,
        'chat_with_doctor': session.doctor_confirmed,
        'doctor_messages': messages.filter(sender__in=['user', 'doctor']),
        'user_chats': user_chats,
        'active_chat_id': session.id,
        'doctors': doctors,
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

def handle_survey(session, user_response):
    """
    Обрабатывает ответы пользователя на вопросы опроса
    """
    current_step = session.survey_step
    
    if current_step == 0:  # Вопрос о возрасте
        try:
            # Пытаемся извлечь возраст из ответа
            import re
            age_match = re.search(r'\b(\d{1,2})\b', user_response)
            if age_match:
                age = int(age_match.group(1))
                if 1 <= age <= 120:
                    session.patient_age = age
                    session.survey_step = 1
                    session.save()
                    
                    next_question = """Спасибо! 

**Вопрос 2:** Укажите пол? (мужской/женский)"""
                    
                    return {
                        'response': next_question,
                        'status': 'success'
                    }
                else:
                    return {
                        'response': 'Пожалуйста, укажите корректный возраст (от 1 до 120 лет).',
                        'status': 'success'
                    }
            else:
                return {
                    'response': 'Пожалуйста, укажите ваш возраст числом (например: 25).',
                    'status': 'success'
                }
        except:
            return {
                'response': 'Пожалуйста, укажите ваш возраст числом (например: 25).',
                'status': 'success'
            }
    
    elif current_step == 1:  # Вопрос о поле
        gender_response = user_response.strip().lower()
        if any(word in gender_response for word in ['мужской', 'муж', 'м', 'male', 'm', 'мужчина']):
            session.patient_gender = 'мужской'
            session.survey_step = 2
            session.save()
            
            next_question = """Спасибо! 

**Вопрос 3:** Что вас беспокоит? Опишите ваши симптомы или проблему."""
            
            return {
                'response': next_question,
                'status': 'success'
            }
        elif any(word in gender_response for word in ['женский', 'жен', 'ж', 'female', 'f', 'женщина']):
            session.patient_gender = 'женский'
            session.survey_step = 2
            session.save()
            
            next_question = """Спасибо! 

**Вопрос 3:** Что вас беспокоит? Опишите ваши симптомы или проблему."""
            
            return {
                'response': next_question,
                'status': 'success'
            }
        else:
            return {
                'response': 'Пожалуйста, укажите пол: мужской или женский.',
                'status': 'success'
            }
    
    elif current_step == 2:  # Вопрос о симптомах
        session.patient_symptoms = user_response
        
        # Устанавливаем заголовок чата, используя ответ пользователя и обрезая его
        new_title = user_response.strip()
        if len(new_title) > 80:
            new_title = new_title[:77] + "..."
        session.title = new_title

        session.survey_step = 3
        session.is_survey_completed = True
        session.save()
        
        # Формируем итоговый анализ
        summary = create_medical_summary(session)
        
        return {
            'response': summary,
            'status': 'success',
            'new_title': new_title  # Возвращаем новый заголовок для обновления в интерфейсе
        }
    
    else:
        return {
            'response': 'Опрос уже завершен. Чем еще могу помочь?',
            'status': 'success'
        }

def create_medical_summary(session):
    """
    Создает итоговый медицинский анализ на основе данных опроса
    """
    age = session.patient_age
    gender = session.patient_gender
    symptoms = session.patient_symptoms
    
    # Формируем запрос для AI с контекстом пациента
    context_message = f"""Пациент: {age} лет, {gender}
Симптомы: {symptoms}

Пожалуйста, проанализируйте симптомы и предоставьте подробный развернутый ответ по пунктам:
1. Возможные причины
2. Рекомендации по самопомощи
3. Когда необходимо обратиться к врачу
4. Общие рекомендации по профилактике

Ответ должен быть подробным, не только заголовок! Используйте форматирование для лучшей читаемости."""
    
    # Получаем анализ от AI
    ai_response = get_ai_response(None, context_message, max_tokens=1000)
    
    if ai_response['status'] == 'success':
        return ai_response['response']
    else:
        # Fallback если AI недоступен
        return f"""### Анализ симптомов

**Данные пациента:**
- Возраст: {age} лет
- Пол: {gender}
- Симптомы: {symptoms}

**Рекомендации:**
- Обратитесь к врачу для точной диагностики
- Не занимайтесь самолечением
- При острых симптомах вызовите скорую помощь

**Важно:** Данная информация носит ознакомительный характер и не заменяет консультацию специалиста.""" 

@login_required
@require_http_methods(["POST"])
def delete_chat(request, session_id):
    """
    Удаляет чат и все его сообщения
    """
    try:
        # Получаем сессию чата, принадлежащую пользователю
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        
        # Удаляем все сообщения сессии
        session.messages.all().delete()
        
        # Удаляем саму сессию
        session.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Чат успешно удален'
        })
        
    except ChatSession.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Чат не найден'
        }, status=404)
    except Exception as e:
        print(f"Error deleting chat: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Ошибка при удалении чата'
        }, status=500) 