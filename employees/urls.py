#employee/urls.py

from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [

    # Employees
    path('', views.employee_list, name='list'),

    # Leaves
    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/apply/', views.apply_leave, name='apply_leave'),
    path('leaves/my/', views.my_leaves, name='my_leaves'),
    path('leaves/<int:pk>/<str:action>/', views.leave_action, name='leave_action'),

    # Payroll
    path('payroll/', views.payroll_list, name='payroll_list'),
    path('payroll/create/', views.payroll_create, name='payroll_create'),
    path('payroll/my/', views.my_payrolls, name='my_payrolls'),
    path('payroll/<int:pk>/toggle/', views.payroll_toggle_status, name='payroll_toggle'),

    # Department
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_form, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_form, name='department_edit'),

    # Designation
    path('designations/', views.designation_list, name='designation_list'),
    path('designations/create/', views.designation_form, name='designation_create'),
    path('designations/<int:pk>/edit/', views.designation_form, name='designation_edit'),

    # Employee
    path('', views.employee_list, name='list'),
    path('create/', views.employee_create, name='create'),
    path('<int:pk>/', views.employee_detail, name='detail'),      # ✅ THIS
    path('<int:pk>/edit/', views.employee_edit, name='edit'),
    path('<int:pk>/toggle/', views.employee_toggle, name='toggle'),


]
