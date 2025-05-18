from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import DoctorProfileForm

def login_view(request):
    print('=== КАСТОМНЫЙ LOGIN_VIEW СРАБОТАЛ ===')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            if hasattr(user, 'is_doctor') and user.is_doctor():
                return redirect('doctor_dashboard')
            elif hasattr(user, 'is_patient') and user.is_patient():
                return redirect('patient_dashboard')
            return redirect('profile')
        else:
            messages.error(request, 'Неверный email или пароль')
            return render(request, 'registration/login.html')
    return render(request, 'registration/login.html')

def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        role = request.POST.get('role')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
            return redirect('register')

            user = User.objects.create_user(
                email=email,
            password=password,
                name=name,
            phone=phone,
            role=role
            )
        
            login(request, user)
        
        if user.is_doctor():
            messages.info(request, 'Пожалуйста, заполните информацию о себе для завершения регистрации')
            return redirect('doctor_dashboard')
        else:
            return redirect('patient_dashboard')

    return render(request, 'registration/register.html')

def is_doctor(user):
    return user.is_doctor()

def is_patient(user):
    return user.is_patient()

@login_required
@user_passes_test(is_doctor)
def doctor_dashboard(request):
    user = request.user

    # Если отправлена только форма с фото
    if request.method == 'POST' and 'profile_photo' in request.FILES:
        user.profile_photo = request.FILES['profile_photo']
        user.save()
        messages.success(request, 'Фото профиля обновлено!')
        return redirect('doctor_dashboard')

    if request.method == 'POST':
        print("\nПолучены POST-данные:", request.POST)
        form = DoctorProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            try:
                # Отладочная информация перед сохранением
                print("Данные формы перед сохранением:")
                for field in form.cleaned_data:
                    print(f"{field}: {form.cleaned_data[field]}")
                user = form.save(commit=False)
                user.role = 'doctor'  # Подтверждаем, что это врач
                user.save()
                print("\nДанные пользователя после сохранения:")
                print(f"Специализация: {user.specialization}")
                print(f"Опыт работы: {user.experience_years}")
                print(f"Биография: {user.biography}")
                print(f"Образование: {user.education}")
                print(f"Достижения: {user.achievements}")
                print(f"Адрес: {user.office_address}")
                print(f"Цена консультации: {user.consultation_price}")
                messages.success(request, 'Профиль успешно обновлен')
                return redirect('doctor_dashboard')
            except Exception as e:
                print(f"Ошибка при сохранении: {e}")
                messages.error(request, f'Ошибка при сохранении данных: {str(e)}')
        else:
            print("Ошибки формы:", form.errors)
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = DoctorProfileForm(instance=request.user)

    # Отладочная информация о текущем пользователе
    print("\nТекущие данные пользователя:")
    print(f"ID: {request.user.id}")
    print(f"Email: {request.user.email}")
    print(f"Имя: {request.user.name}")
    print(f"Роль: {request.user.role}")
    print(f"Специализация: {request.user.specialization}")
    print(f"Опыт работы: {request.user.experience_years}")
    print(f"Биография: {request.user.biography}")
    print(f"Образование: {request.user.education}")
    print(f"Достижения: {request.user.achievements}")
    print(f"Адрес: {request.user.office_address}")
    print(f"Цена консультации: {request.user.consultation_price}")

    is_profile_complete = all([
        request.user.specialization,
        request.user.experience_years,
        request.user.biography,
        request.user.education,
        request.user.office_address,
        request.user.consultation_price
    ])

    context = {
        'form': form,
        'user': request.user,
        'is_profile_complete': is_profile_complete,
        'debug_info': {
            'specialization': request.user.get_specialization_display() if request.user.specialization else 'Не указана',
            'experience_years': request.user.experience_years or 'Не указан',
            'biography': request.user.biography or 'Не указана',
            'education': request.user.education or 'Не указано',
            'achievements': request.user.achievements or 'Не указаны',
            'office_address': request.user.office_address or 'Не указан',
            'consultation_price': request.user.consultation_price or 'Не указана'
        }
    }

    return render(request, 'doctor_dashboard.html', context)

@login_required
@user_passes_test(is_patient)
def patient_dashboard(request):
    user = request.user

    if request.method == 'POST' and 'profile_photo' in request.FILES:
        user.profile_photo = request.FILES['profile_photo']
        user.save()
        messages.success(request, 'Фото профиля обновлено!')
        return redirect('patient_dashboard')

    return render(request, 'patient_dashboard.html')

def logout_view(request):
    logout(request)
    return redirect('home')
