from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен для регистрации")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('patient', 'Пациент'),
        ('doctor', 'Врач'),
    )

    SPECIALIZATION_CHOICES = (
        ('therapist', 'Терапевт'),
        ('neurologist', 'Невролог'),
        ('cardiologist', 'Кардиолог'),
        ('surgeon', 'Хирург'),
        ('pediatrician', 'Педиатр'),
        ('ophthalmologist', 'Офтальмолог'),
        ('dentist', 'Стоматолог'),
        ('psychiatrist', 'Психиатр'),
        ('dermatologist', 'Дерматолог'),
        ('other', 'Другое'),
    )

    email = models.EmailField(unique=True, verbose_name='Email')
    name = models.CharField(max_length=255, verbose_name='ФИО')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient', verbose_name='Роль')
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True, verbose_name='Фото профиля')
    
    # Дополнительные поля для врачей
    specialization = models.CharField(
        max_length=20, 
        choices=SPECIALIZATION_CHOICES, 
        blank=True, 
        null=True, 
        verbose_name='Специализация'
    )
    experience_years = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        verbose_name='Опыт работы (лет)'
    )
    biography = models.TextField(
        blank=True, 
        verbose_name='О себе'
    )
    education = models.TextField(
        blank=True, 
        verbose_name='Образование'
    )
    achievements = models.TextField(
        blank=True, 
        verbose_name='Достижения'
    )
    office_address = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name='Адрес кабинета'
    )
    consultation_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        verbose_name='Стоимость консультации'
    )
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

    def is_patient(self):
        return self.role == 'patient'

    def is_doctor(self):
        return self.role == 'doctor'

    def get_full_doctor_info(self):
        if self.is_doctor():
            return {
                'name': self.name,
                'specialization': self.get_specialization_display(),
                'experience_years': self.experience_years,
                'biography': self.biography,
                'education': self.education,
                'achievements': self.achievements,
                'office_address': self.office_address,
                'consultation_price': self.consultation_price,
                'phone': self.phone,
                'email': self.email,
            }
        return None

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
