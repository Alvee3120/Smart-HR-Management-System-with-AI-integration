from rest_framework import generics, permissions
from .models import Job
from .serializers import JobSerializer
from .utils import run_ai_pipeline
from .permissions import IsHR # Assuming you created this from previous response

class JobListCreateView(generics.ListCreateAPIView):
    queryset = Job.objects.all().order_by('-created_at')
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated] # Add IsHR if you want strict control

    def perform_create(self, serializer):
        # Save the job first
        job = serializer.save(posted_by=self.request.user)
        
        # Run AI Pipeline (Extract -> GLiNER -> Jina)
        run_ai_pipeline(job)

class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        job = serializer.save()
        
        # Rerun AI if text/file changed
        if 'description_text' in self.request.data or 'description_file' in self.request.data:
            run_ai_pipeline(job)