from django.urls import path
from .views import JobListCreateView, JobDetailView

app_name = 'jobs'

urlpatterns = [
    path('', JobListCreateView.as_view(), name='job-list-create'),
    path('<int:pk>/', JobDetailView.as_view(), name='job-detail'),
]