from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'role', 'phone_number', 'is_staff', 'is_superuser']
    fieldsets = UserAdmin.fieldsets + (
        ('System Role & Extra Info', {'fields': ('role', 'phone_number', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('System Role & Extra Info', {'fields': ('role', 'phone_number', 'profile_picture')}),
    )

admin.site.register(User, CustomUserAdmin)
