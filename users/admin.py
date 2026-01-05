from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm  # <--- Import your new forms

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm 
    form = CustomUserChangeForm
    model = User
    ordering = ['email']
    list_display = ['email', 'full_name', 'role', 'is_staff', 'is_active']
    
    # Used for the "Edit User" page
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Used for the "Add User" page
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'role', 'password_1', 'password_2'),
        }),
    )

admin.site.register(User, CustomUserAdmin)