#employee/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Employee, LeaveRequest, Payroll
from .forms import LeaveRequestForm, PayrollForm
from django.utils import timezone
from .forms import DepartmentForm, DesignationForm, EmployeeHRForm
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Employee, LeaveRequest, Payroll, Department, Designation
from .services import create_employee_user

User = get_user_model()

def hr_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ['HR', 'Admin']:
            return redirect('web_test:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# =========================
# EMPLOYEES
# =========================
@login_required
@hr_required
def employee_list(request):
    employees = Employee.objects.select_related('user', 'department', 'designation')
    return render(request, 'hr/employees/employee_list.html', {'employees': employees})

@login_required
@hr_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    leaves = employee.leaves.all().order_by('-id')[:5]
    payrolls = employee.payrolls.all().order_by('-month')[:5]

    return render(request, 'hr/employees/employee_detail.html', {
        'employee': employee,
        'leaves': leaves,
        'payrolls': payrolls
    })


# =========================
# LEAVE MANAGEMENT
# =========================

@login_required
def apply_leave(request):
    employee = get_object_or_404(Employee, user=request.user)

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = employee
            leave.save()
            messages.success(request, "Leave request submitted.")
            return redirect('employees:my_leaves')
    else:
        form = LeaveRequestForm()

    return render(request, 'hr/leaves/apply_leave.html', {'form': form})


@login_required
def my_leaves(request):
    employee = get_object_or_404(Employee, user=request.user)
    leaves = employee.leaves.all().order_by('-id')
    return render(request, 'hr/leaves/my_leaves.html', {'leaves': leaves})


@login_required
@hr_required
def leave_list(request):
    leaves = LeaveRequest.objects.select_related('employee__user').order_by('-id')
    return render(request, 'hr/leaves/leave_list.html', {'leaves': leaves})


@login_required
@hr_required
def leave_action(request, pk, action):
    leave = get_object_or_404(LeaveRequest, pk=pk)

    if action == 'approve':
        leave.status = 'APPROVED'
    elif action == 'reject':
        leave.status = 'REJECTED'

    leave.save()
    messages.success(request, f"Leave {leave.status.lower()} successfully.")
    return redirect('employees:leave_list')


# =========================
# PAYROLL MANAGEMENT
# =========================

@login_required
@hr_required
def payroll_list(request):
    payrolls = Payroll.objects.select_related('employee__user').order_by('-month')
    return render(request, 'hr/payroll/payroll_list.html', {'payrolls': payrolls})


@login_required
@hr_required
def payroll_create(request):
    if request.method == 'POST':
        form = PayrollForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Payroll created successfully.")
            return redirect('employees:payroll_list')
    else:
        form = PayrollForm()

    return render(request, 'hr/payroll/payroll_form.html', {'form': form})


@login_required
def my_payrolls(request):
    employee = get_object_or_404(Employee, user=request.user)
    payrolls = employee.payrolls.all().order_by('-month')
    return render(request, 'hr/payroll/my_payrolls.html', {'payrolls': payrolls})

@login_required
@hr_required
def payroll_toggle_status(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)

    payroll.is_paid = not payroll.is_paid

    if payroll.is_paid:
        payroll.payment_date = timezone.now().date()
    else:
        payroll.payment_date = None

    payroll.save()
    messages.success(request, "Payroll payment status updated.")
    return redirect('employees:payroll_list')



# =========================
# DEPARTMENTS
# =========================

@login_required
@hr_required
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'hr/departments/department_list.html', {'departments': departments})


@login_required
@hr_required
def department_form(request, pk=None):
    dept = Department.objects.get(pk=pk) if pk else None
    form = DepartmentForm(request.POST or None, instance=dept)

    if form.is_valid():
        form.save()
        return redirect('employees:department_list')

    return render(request, 'hr/departments/department_form.html', {'form': form})


# =========================
# DESIGNATIONS
# =========================

@login_required
@hr_required
def designation_list(request):
    designations = Designation.objects.select_related('department')
    return render(request, 'hr/designations/designation_list.html', {'designations': designations})


@login_required
@hr_required
def designation_form(request, pk=None):
    desig = Designation.objects.get(pk=pk) if pk else None
    form = DesignationForm(request.POST or None, instance=desig)

    if form.is_valid():
        form.save()
        return redirect('employees:designation_list')

    return render(request, 'hr/designations/designation_form.html', {'form': form})


# =========================
# EMPLOYEE (HR CRUD)
# =========================

@login_required
@hr_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeHRForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                user, password = create_employee_user(
                    email=form.cleaned_data['email'],
                    full_name=form.cleaned_data['full_name'],
                    role='Employee'
                )

                emp = form.save(commit=False)
                emp.user = user
                emp.save()

            messages.success(request, "Employee created and email sent successfully.")
            return redirect('employees:list')

    else:
        form = EmployeeHRForm()

    return render(request, 'hr/employees/employee_form.html', {'form': form})


@login_required
@hr_required
def employee_edit(request, pk):
    emp = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        form = EmployeeHRForm(request.POST, instance=emp, user_instance=emp.user)
        if form.is_valid():
            emp.user.full_name = form.cleaned_data['full_name']
            emp.user.email = form.cleaned_data['email']
            emp.user.save()
            form.save()
            return redirect('employees:detail', pk=pk)
    else:
        form = EmployeeHRForm(instance=emp, user_instance=emp.user)

    return render(request, 'hr/employees/employee_form.html', {'form': form, 'edit': True})


@login_required
@hr_required
def employee_toggle(request, pk):
    emp = get_object_or_404(Employee, pk=pk)
    emp.is_active = not emp.is_active
    emp.save()
    return redirect('employees:detail', pk=pk)