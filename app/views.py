from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
import json

def chat_view(request):
    return render(request, 'chat.html')

@csrf_protect
def chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # Здесь будет ваша логика обработки сообщения и получения ответа от ИИ
            # Пока возвращаем заглушку
            response = "Спасибо за ваше сообщение. Я обрабатываю ваш запрос..."
            
            return JsonResponse({
                'status': 'success',
                'response': response
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405) 