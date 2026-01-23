#employee/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
# 1. Departments & Designations
class Department(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Designation(models.Model):
    title = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title} ({self.department.name})"

# 2. Employee Profile
class Employee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile')
    
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.ForeignKey('Designation', on_delete=models.SET_NULL, null=True, blank=True)
    
    date_of_joining = models.DateField()
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bank_account_number = models.CharField(max_length=50, blank=True)
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.full_name if hasattr(self.user, 'full_name') else self.user.email

    # 3. Add the clean method
    def clean(self):
        # Validation: Date of Joining cannot be in the future
        if self.date_of_joining and self.date_of_joining > timezone.now().date():
            raise ValidationError({
                'date_of_joining': "Date of joining cannot be in the future."
            })

        # Validation: Salary must be greater than 0
        if self.basic_salary <= 0:
            raise ValidationError({
                'basic_salary': "Basic salary must be greater than 0."
            })

    # 4. Ensure validation runs when saving via script/shell (optional but recommended)
    def save(self, *args, **kwargs):
        self.full_clean()  # This calls self.clean() before saving
        super().save(*args, **kwargs)

        
# 3. Leave Management (Benefits)
class LeaveRequest(models.Model):
    LEAVE_TYPES = [('SICK', 'Sick Leave'), ('CASUAL', 'Casual Leave'), ('PAID', 'Paid Leave')]
    STATUS_CHOICES = [('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

# 4. Payroll History
class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    month = models.DateField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # 1. Calculate Net Salary
        self.net_salary = (self.basic_salary + self.bonus) - self.deductions
        
        # 2. Auto-set Payment Date if marked as paid but no date is set
        if self.is_paid and not self.payment_date:
            self.payment_date = timezone.now().date()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payroll: {self.employee.user.full_name} - {self.month}"