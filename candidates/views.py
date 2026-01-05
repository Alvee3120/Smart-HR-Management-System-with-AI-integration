from django.core.mail import send_mail
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Application
from .serializers import ApplicationCreateSerializer, ApplicationDetailSerializer
from .utils import process_application
from .permissions import IsCandidate, IsHR, IsReviewer
from .serializers import (
    ApplicationCreateSerializer, 
    ApplicationDetailSerializer, 
    HRApplicationCreateSerializer, # New
    InterviewInviteSerializer      # New
)

class ApplyJobView(generics.CreateAPIView):
    """
    Candidate uploads CV here.
    """
    serializer_class = ApplicationCreateSerializer
    permission_classes = [IsCandidate]

    def perform_create(self, serializer):
        # Save application
        application = serializer.save(candidate=self.request.user)
        # Trigger AI (Extract -> Embed -> Score)
        process_application(application)

class CandidateMyApplicationsView(generics.ListAPIView):
    """
    Candidate sees their own history.
    """
    serializer_class = ApplicationDetailSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return Application.objects.filter(candidate=self.request.user).order_by('-created_at')

class JobApplicationsListView(generics.ListAPIView):
    """
    HR/Reviewer sees ALL candidates for a specific Job, RANKED BY SCORE.
    """
    serializer_class = ApplicationDetailSerializer
    permission_classes = [permissions.IsAuthenticated] # Or IsHR | IsReviewer

    def get_queryset(self):
        job_id = self.kwargs.get('job_id')
        # Order by Match Score (Highest first)
        return Application.objects.filter(job_id=job_id).order_by('-match_score')
    
class HRAddReferenceView(generics.CreateAPIView):
    """
    HR uploads a CV directly. The candidate is tagged as having a reference.
    """
    serializer_class = HRApplicationCreateSerializer
    permission_classes = [IsHR]

    def perform_create(self, serializer):
        application = serializer.save()
        # Trigger the same AI scoring pipeline
        process_application(application)

class JobApplicationsListView(generics.ListAPIView):
    """
    HR/Reviewer sees ALL candidates.
    Supports filtering by reference: ?has_reference=true
    """
    serializer_class = ApplicationDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        job_id = self.kwargs.get('job_id')
        queryset = Application.objects.filter(job_id=job_id)

        # --- NEW FILTERING LOGIC ---
        has_reference = self.request.query_params.get('has_reference')
        if has_reference is not None:
            # Convert string 'true'/'false' to boolean
            is_ref = has_reference.lower() == 'true'
            queryset = queryset.filter(has_reference=is_ref)

        # Order by Score
        return queryset.order_by('-match_score')
    
class SendInterviewInviteView(APIView):
    """
    HR selects a candidate and sends an interview email.
    """
    permission_classes = [IsHR]

    def post(self, request, pk):
        application = generics.get_object_or_404(Application, pk=pk)
        serializer = InterviewInviteSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data
            
            # 1. Update Status
            application.status = 'INTERVIEW'
            application.interview_date = f"{data['date']} {data['time']}" # Store loosely or parse to datetime
            application.save()

            # 2. Construct Email
            subject = f"Interview Invitation: {application.job.title}"
            message = (
                f"Dear {application.candidate.full_name},\n\n"
                f"We are pleased to invite you for an interview.\n\n"
                f"Date: {data['date']}\n"
                f"Time: {data['time']}\n"
                f"Location: {data['location']}\n\n"
                f"Additional Notes: {data.get('message', '')}\n\n"
                f"Best regards,\nSmart Hire Solutions Team"
            )

            # 3. Send Email
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER or 'noreply@smarthire.com',
                [application.candidate.email],
                fail_silently=False,
            )

            return Response({"detail": "Interview invite sent successfully!"})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)