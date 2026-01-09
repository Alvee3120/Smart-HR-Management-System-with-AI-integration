from django.contrib import admin
from django import forms
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Employee, Department, Designation, LeaveRequest, Payroll
from .services import create_employee_user

User = get_user_model()

# ==========================================
# 1. Custom Forms for Employee Management
# ==========================================

class EmployeeCreationForm(forms.ModelForm):
    """Form for CREATING a new employee (creates User + Employee)"""
    full_name = forms.CharField(label="Full Name", required=True)
    email = forms.EmailField(label="Email (Username)", required=True)
    password = forms.CharField(widget=forms.PasswordInput, label="Password", required=True)

    class Meta:
        model = Employee
        # Exclude 'user' because we create it manually in save()
        exclude = ('user', 'is_active') 

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        # Atomic transaction ensures we don't get a User without an Employee profile if something fails
        with transaction.atomic():
            email = self.cleaned_data['email']
            password = self.cleaned_data['password']
            full_name = self.cleaned_data['full_name']

            # 1. Create the User
            user, password = create_employee_user(email, full_name, role="Employee", password=password)

            # 2. Link User to Employee
            employee = super().save(commit=False)
            employee.user = user
            
            if commit:
                employee.save()

            # 3. Send Email
            self.send_welcome_email(user, password)

        return employee

    # def send_welcome_email(self, user, raw_password):
    #     subject = 'Welcome to Smart Hire - Your Login Credentials'
    #     message = (
    #         f"Dear {user.full_name},\n\n"
    #         f"Your employee account has been created.\n\n"
    #         f"Email: {user.email}\n"
    #         f"Password: {raw_password}\n\n"
    #         f"Please log in and change your password."
    #     )
    #     try:
    #         send_mail(
    #             subject, message, settings.EMAIL_HOST_USER, [user.email], fail_silently=False
    #         )
    #     except Exception as e:
    #         print(f"Error sending email: {e}")


class EmployeeChangeForm(forms.ModelForm):
    """Form for EDITING an existing employee"""
    full_name = forms.CharField(label="Full Name", required=True)
    email = forms.EmailField(label="Email", required=True)

    class Meta:
        model = Employee
        exclude = ('user',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill data from the linked User object
        if self.instance and self.instance.user:
            self.fields['full_name'].initial = self.instance.user.full_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        employee = super().save(commit=False)
        # Update User fields if they were changed
        if employee.user:
            employee.user.full_name = self.cleaned_data['full_name']
            employee.user.email = self.cleaned_data['email']
            employee.user.save()
        
        if commit:
            employee.save()
        return employee


# ==========================================
# 2. Admin Classes
# ==========================================

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'get_email', 'department', 'designation', 'is_active', 'date_of_joining')
    list_filter = ('department', 'designation', 'is_active')
    search_fields = ('user__full_name', 'user__email')
    list_select_related = ('user', 'department', 'designation') # Optimization

    def get_name(self, obj):
        return obj.user.full_name
    get_name.short_description = 'Full Name'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

    def get_form(self, request, obj=None, **kwargs):
        # Switch forms based on whether we are adding or editing
        if obj is None:
            kwargs['form'] = EmployeeCreationForm
        else:
            kwargs['form'] = EmployeeChangeForm
        return super().get_form(request, obj, **kwargs)


class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('get_employee', 'leave_type', 'start_date', 'end_date', 'status', 'days_count')
    list_filter = ('status', 'leave_type')
    search_fields = ('employee__user__full_name', 'reason')
    list_editable = ('status',) # HR can approve/reject directly from list
    date_hierarchy = 'start_date'

    def get_employee(self, obj):
        return obj.employee.user.full_name
    get_employee.short_description = 'Employee'

    def days_count(self, obj):
        delta = obj.end_date - obj.start_date
        return delta.days + 1
    days_count.short_description = 'Days'


class PayrollAdmin(admin.ModelAdmin):
    # Updated to match your exact models.py fields
    list_display = ('get_employee', 'month', 'basic_salary', 'net_salary', 'is_paid', 'payment_date')
    list_filter = ('is_paid', 'month')
    search_fields = ('employee__user__full_name',)
    readonly_fields = ('net_salary',) # Because it's calculated automatically
    date_hierarchy = 'month'

    def get_employee(self, obj):
        return obj.employee.user.full_name
    get_employee.short_description = 'Employee'


class DesignationAdmin(admin.ModelAdmin):
    list_display = ('title', 'department')
    list_filter = ('department',)


# ==========================================
# 3. Registration
# ==========================================
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Department)
admin.site.register(Designation, DesignationAdmin)
admin.site.register(LeaveRequest, LeaveRequestAdmin)
admin.site.register(Payroll, PayrollAdmin)