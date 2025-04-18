from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.urls import reverse

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next')
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            # Если есть next_url, используем его, иначе идем на profile
            return redirect(next_url if next_url else reverse('profile'))
        else:
            messages.error(request, "Неверный email или пароль")
    
    return render(request, 'registration/login.html')

def register_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        name = request.POST['name']
        password = request.POST['password']
        phone = request.POST.get('phone', '')  # phone не обязателен

        if User.objects.filter(email=email).exists():
            messages.error(request, "Этот email уже зарегистрирован")
            return render(request, 'registration/register.html')

        try:
            user = User.objects.create_user(
                email=email,
                name=name,
                password=password,
                phone=phone
            )
            login(request, user)
            messages.success(request, "Регистрация успешна!")
            return redirect('profile')
        except Exception as e:
            messages.error(request, f"Ошибка при регистрации: {str(e)}")
            return render(request, 'registration/register.html')

    return render(request, 'registration/register.html')
