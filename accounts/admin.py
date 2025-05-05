from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'role', 'specialization', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {
            'fields': (
                'name', 'role', 'specialization', 'experience_years', 'biography',
                'education', 'achievements', 'office_address', 'consultation_price', 'profile_photo'
            )
        }),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    search_fields = ('email', 'name')
    ordering = ('email',)