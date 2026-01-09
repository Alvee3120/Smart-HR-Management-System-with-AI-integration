from django.urls import path
from . import views

app_name = 'web_test'

urlpatterns = [

    # =========================
    # Public Pages
    # =========================
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('service/', views.service, name='service'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('career/', views.career, name='career'),

    # =========================
    # Authentication
    # =========================
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # =========================
    # Dashboards
    # =========================
    path('dashboard/', views.dashboard, name='dashboard'),                 # role-based
    path('hr/dashboard/', views.hr_dashboard, name='hr_dashboard'),        # ✅ HR PANEL
    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),

    # =========================
    # Job Management
    # =========================
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/create/', views.create_job, name='create_job'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('jobs/<int:pk>/delete/', views.delete_job, name='delete_job'),
    path('jobs/<int:pk>/toggle-status/', views.toggle_job_status, name='toggle_job_status'),

    # =========================
    # Job Application & Ranking
    # =========================
    path('jobs/<int:job_id>/apply/', views.apply_for_job, name='apply_job'),
    path('jobs/<int:job_id>/ranking/', views.job_ranking, name='job_ranking'),
    path('applications/<int:pk>/', views.application_detail, name='application_detail'),
    path('jobs/<int:job_id>/upload-cv/', views.hr_upload_cv, name='hr_upload_cv'),

    # =========================
    # Invites
    # =========================
    path('application/<int:application_id>/invite/', views.send_interview_invite, name='send_interview_invite'),
    path('bulk-invite/', views.bulk_send_invite, name='bulk_send_invite'),
    path('hr/jobs/', views.hr_job_list, name='hr_job_list'),

]
