from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.models import User
from .models import Appointment, DoctorSchedule
import json
from django import forms
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseForbidden

def chat_view(request):
    return render(request, 'chat.html')

@csrf_protect
def chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # Пример: если бот рекомендует терапевта
            recommended_specialty = 'therapist'
            specialty_display = 'Терапевт'
            from accounts.models import User
            doctors = User.objects.filter(role='doctor', specialization=recommended_specialty)

            # Генерируем HTML-карточки врачей
            doctor_cards = ''
            for doctor in doctors:
                photo = doctor.profile_photo.url if doctor.profile_photo else ''
                photo_html = f"<img src='{photo}' alt='Фото' class='w-16 h-16 rounded-full object-cover shadow' style='background:#f3f4f6;'>" if photo else f"<span class='w-16 h-16 rounded-full flex items-center justify-center bg-blue-100 text-blue-600 text-2xl font-bold shadow'>{doctor.name[0] if doctor.name else '?'}" + "</span>"
                doctor_cards += f'''
                <div class="bg-white rounded-2xl shadow-lg p-6 flex flex-col justify-between mb-6" style="max-width:370px;display:inline-block;margin:1rem;vertical-align:top;">
                    <div class="flex items-center mb-4">
                        <div class="mr-4">{photo_html}</div>
                        <div>
                            <div class="font-bold text-lg">{doctor.name}</div>
                            <div class="text-gray-500">{doctor.get_specialization_display()}</div>
                        </div>
                    </div>
                    <div class="text-gray-700 text-sm mb-2">
                        {'Опыт: ' + str(doctor.experience_years) + ' лет<br>' if doctor.experience_years else ''}
                        {'Образование: ' + doctor.education[:50] + '<br>' if doctor.education else ''}
                        {'О себе: ' + doctor.biography[:50] if doctor.biography else ''}
                    </div>
                    <a href="/app/appointment/{doctor.id}/" class="mt-4 inline-block bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg text-center transition" style="text-decoration:none;">Записаться</a>
                </div>
                '''

            response = (
                "<div class='recommend-block' style='margin-top: 2rem; padding: 2rem; background: linear-gradient(90deg, #3b82f6 0%, #6366f1 100%); border-radius: 1.5rem; box-shadow: 0 4px 24px rgba(59,130,246,0.10); color: white; text-align: center;'>"
                f"<div style='font-size:1.5rem;font-weight:700;margin-bottom:0.5rem;'>Рекомендуем обратиться к врачу: {specialty_display}</div>"
                f"<div style='font-size:1rem;opacity:0.9;margin-bottom:1.5rem;'>Для вашего случая лучше всего подойдёт {specialty_display}. Вы можете выбрать врача и записаться онлайн.</div>"
                "</div>"
            )
            response += f"<div style='display:flex;flex-wrap:wrap;justify-content:center;align-items:stretch;margin-top:2rem;'>" + doctor_cards + "</div>"
            
            return JsonResponse({
                'status': 'success',
                'response': response,
                'is_html': True  # Добавляем флаг, указывающий что ответ содержит HTML
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

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['date', 'time', 'comment']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Комментарий (необязательно)'}),
        }
        labels = {
            'date': 'Дата',
            'time': 'Время',
            'comment': 'Комментарий',
        }

@login_required
def doctors_by_specialty(request, specialty=None):
    if not specialty or specialty == "all":
        doctors = User.objects.filter(role='doctor')
        specialty_display = "Все"
    else:
        doctors = User.objects.filter(role='doctor', specialization=specialty)
        specialty_display = dict(User.SPECIALIZATION_CHOICES).get(specialty, specialty)
    return render(request, 'doctors_list.html', {'doctors': doctors, 'specialty': specialty_display})

@login_required
def appointment_create(request, doctor_id):
    doctor = get_object_or_404(User, id=doctor_id, role='doctor')
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.doctor = doctor
            appointment.status = 'pending'
            appointment.save()
            return render(request, 'appointment_success.html', {'doctor': doctor})
    else:
        form = AppointmentForm(initial={'date': timezone.now().date()})
    return render(request, 'appointment_form.html', {'form': form, 'doctor': doctor})

@login_required
def my_appointments(request):
    appointments = Appointment.objects.filter(patient=request.user).select_related('doctor').order_by('-created_at')
    return render(request, 'my_appointments.html', {'appointments': appointments})

def is_doctor(user):
    return hasattr(user, 'role') and user.role == 'doctor'

@login_required
@user_passes_test(is_doctor)
def doctor_appointments(request):
    appointments = Appointment.objects.filter(doctor=request.user).select_related('patient').order_by('-created_at')
    return render(request, 'doctor_appointments.html', {'appointments': appointments})

@login_required
@user_passes_test(is_doctor)
def appointment_update(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm':
            appointment.status = 'confirmed'
            appointment.save()
            # Email пациенту о подтверждении
            send_mail(
                subject='Ваша заявка подтверждена',
                message=f'Ваша заявка к врачу {appointment.doctor.name} на {appointment.date} {appointment.time} подтверждена.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.patient.email],
                fail_silently=True,
            )
        elif action == 'reject':
            comment = request.POST.get('doctor_comment', '')
            appointment.status = 'rejected'
            appointment.doctor_comment = comment
            appointment.save()
            # Email пациенту об отклонении
            send_mail(
                subject='Ваша заявка отклонена',
                message=f'Ваша заявка к врачу {appointment.doctor.name} на {appointment.date} {appointment.time} отклонена.\nКомментарий врача: {comment}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.patient.email],
                fail_silently=True,
            )
        return redirect('doctor_appointments')
    return redirect('doctor_appointments')

@login_required
def doctor_slots(request, doctor_id):
    doctor = get_object_or_404(User, id=doctor_id, role='doctor')
    slots = DoctorSchedule.objects.filter(doctor=doctor, is_booked=False, date__gte=timezone.now().date()).order_by('date', 'start_time')
    return render(request, 'doctor_slots.html', {'doctor': doctor, 'slots': slots})

@login_required
def book_slot(request, slot_id):
    slot = get_object_or_404(DoctorSchedule, id=slot_id, is_booked=False)
    if request.method == 'POST':
        # Создаём запись на приём
        Appointment.objects.create(
            patient=request.user,
            doctor=slot.doctor,
            date=slot.date,
            time=slot.start_time,
            schedule_slot=slot,
            status='pending'
        )
        slot.is_booked = True
        slot.save()
        return redirect('my_appointments')
    return render(request, 'book_slot_confirm.html', {'slot': slot})

class DoctorScheduleForm(forms.ModelForm):
    class Meta:
        model = DoctorSchedule
        fields = ['date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
        labels = {
            'date': 'Дата',
            'start_time': 'Время начала',
            'end_time': 'Время конца',
        }

@login_required
@user_passes_test(is_doctor)
def my_slots(request):
    slots = DoctorSchedule.objects.filter(doctor=request.user).order_by('-date', '-start_time')
    return render(request, 'my_slots.html', {'slots': slots})

@login_required
@user_passes_test(is_doctor)
def slot_add(request):
    if request.method == 'POST':
        form = DoctorScheduleForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.doctor = request.user
            slot.save()
            return redirect('my_slots')
    else:
        form = DoctorScheduleForm()
    return render(request, 'slot_form.html', {'form': form, 'action': 'Добавить слот'})

@login_required
@user_passes_test(is_doctor)
def slot_edit(request, slot_id):
    slot = get_object_or_404(DoctorSchedule, id=slot_id, doctor=request.user)
    if request.method == 'POST':
        form = DoctorScheduleForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            return redirect('my_slots')
    else:
        form = DoctorScheduleForm(instance=slot)
    return render(request, 'slot_form.html', {'form': form, 'action': 'Редактировать слот'})

@login_required
@user_passes_test(is_doctor)
def slot_delete(request, slot_id):
    slot = get_object_or_404(DoctorSchedule, id=slot_id, doctor=request.user)
    if request.method == 'POST':
        slot.delete()
        return redirect('my_slots')
    return render(request, 'slot_delete_confirm.html', {'slot': slot})

@login_required
@user_passes_test(is_doctor)
def doctor_dashboard(request):
    # Добавляем подсчет свободных слотов
    free_slots_count = DoctorSchedule.objects.filter(
        doctor=request.user,
        is_booked=False,
        date__gte=timezone.now().date()
    ).count()

    context = {
        'user': request.user,
        'free_slots_count': free_slots_count,
    }
    return render(request, 'doctor_dashboard.html', context) 