from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('name', 'email', 'phone', 'password1', 'password2')

from django import forms
from django.contrib.auth import authenticate

class LoginForm(forms.Form):
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        user = authenticate(email=email, password=password)
        if not user:
            raise forms.ValidationError("Неверный email или пароль")
        cleaned_data['user'] = user
        return cleaned_data

from django import forms
from .models import User

class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['specialization', 'experience_years', 'biography', 'education', 
                 'achievements', 'office_address', 'consultation_price', 'profile_photo']
        widgets = {
            'specialization': forms.Select(attrs={
                'class': 'form-control',
                'required': 'required'
            }),
            'experience_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'required': 'required'
            }),
            'biography': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'required': 'required'
            }),
            'education': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'required': 'required'
            }),
            'achievements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'office_address': forms.TextInput(attrs={
                'class': 'form-control',
                'required': 'required'
            }),
            'consultation_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'required': 'required'
            }),
            'profile_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        labels = {
            'specialization': 'Специализация',
            'experience_years': 'Опыт работы (лет)',
            'biography': 'О себе',
            'education': 'Образование',
            'achievements': 'Достижения',
            'office_address': 'Адрес кабинета',
            'consultation_price': 'Стоимость консультации (сом)',
            'profile_photo': 'Фото профиля'
        }

    def clean_consultation_price(self):
        price = self.cleaned_data.get('consultation_price')
        if price is not None and price < 0:
            raise forms.ValidationError('Стоимость консультации не может быть отрицательной')
        return price

    def clean_experience_years(self):
        years = self.cleaned_data.get('experience_years')
        if years is not None and years < 0:
            raise forms.ValidationError('Опыт работы не может быть отрицательным')
        return years

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            print(f"Сохранено: {user.specialization}, {user.experience_years}, {user.biography}")
        return user

