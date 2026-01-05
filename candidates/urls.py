from django.urls import path
from .views import (
    ApplyJobView, 
    CandidateMyApplicationsView, 
    JobApplicationsListView,
    HRAddReferenceView,       # New
    SendInterviewInviteView   # New
)
app_name = 'candidates'

urlpatterns = [
    # Candidate
    path('apply/', ApplyJobView.as_view(), name='apply'),
    path('my-applications/', CandidateMyApplicationsView.as_view(), name='my-applications'),

    # HR / Reviewer
    path('job/<int:job_id>/ranking/', JobApplicationsListView.as_view(), name='job-ranking'),
    
    # New: HR Uploads Reference
    path('hr/upload-reference/', HRAddReferenceView.as_view(), name='hr-upload-reference'),
    
    # New: Send Interview Invite (PK is the Application ID)
    path('application/<int:pk>/invite/', SendInterviewInviteView.as_view(), name='send-invite'),
]