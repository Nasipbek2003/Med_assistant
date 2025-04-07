from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import User

def login_view(request):
    if request.method == 'POST':  
        email = request.POST['email']
        password = request.POST['password']

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Неверный пароль")
        except User.DoesNotExist:
            messages.error(request, "Пользователь с таким email не найден")
        
        return render(request, 'login.html')
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        name = request.POST['name']
        password = request.POST['password']
        phone = request.POST.get('phone', '')  # phone не обязателен

        if User.objects.filter(email=email).exists():
            messages.error(request, "Этот email уже зарегистрирован")
            return render(request, 'register.html')

        try:
            user = User.objects.create_user(
                email=email,
                name=name,
                password=password,
                phone=phone
            )
            login(request, user)
            return redirect('home')
        except Exception as e:
            messages.error(request, f"Ошибка при регистрации: {str(e)}")
            return render(request, 'register.html')

    return render(request, 'register.html')
