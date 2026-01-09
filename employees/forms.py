from django import forms
from .models import LeaveRequest, Payroll
from .models import Department, Designation, Employee
from django.contrib.auth import get_user_model
from .services import create_employee_user

User = get_user_model()
# =========================
# Leave Form (Employee)
# =========================
class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full rounded border-gray-300'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full rounded border-gray-300'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'w-full rounded border-gray-300'}),
        }

def save(self, commit=True):
    user, password = create_employee_user(
        self.cleaned_data['email'],
        self.cleaned_data['full_name'],
        role="Employee"
    )

    employee = super().save(commit=False)
    employee.user = user
    if commit:
        employee.save()
    return employee

# =========================
# Payroll Form (HR)
# =========================
class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ['employee', 'month', 'basic_salary', 'bonus', 'deductions', 'is_paid']
        widgets = {
            'month': forms.DateInput(attrs={'type': 'date', 'class': 'w-full rounded border-gray-300'}),
        }




# -----------------
# Department
# -----------------
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']


# -----------------
# Designation
# -----------------
class DesignationForm(forms.ModelForm):
    class Meta:
        model = Designation
        fields = ['title', 'department']


# -----------------
# Employee (HR create/edit)
# -----------------
class EmployeeHRForm(forms.ModelForm):
    full_name = forms.CharField()
    email = forms.EmailField()

    class Meta:
        model = Employee
        fields = [
            'department', 'designation', 'date_of_joining',
            'phone_number', 'address', 'basic_salary', 'bank_account_number'
        ]

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)

        if self.user_instance:
            self.fields['full_name'].initial = self.user_instance.full_name
            self.fields['email'].initial = self.user_instance.email