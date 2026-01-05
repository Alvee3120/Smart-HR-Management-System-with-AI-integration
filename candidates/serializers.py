from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from .models import Application


User = get_user_model()


class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['job', 'cv_file']
    
    def validate(self, data):
        # Check if user already applied
        user = self.context['request'].user
        job = data['job']
        if Application.objects.filter(candidate=user, job=job).exists():
            raise serializers.ValidationError("You have already applied for this job.")
        return data

class ApplicationDetailSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    candidate_email = serializers.CharField(source='candidate.email', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'job_title', 'candidate_name', 'candidate_email', 
            'cv_file', 'extracted_data', 'match_score', 
            'status', 'created_at'
        ]


class HRApplicationCreateSerializer(serializers.ModelSerializer):
    """
    Allows HR to upload a CV for a candidate. 
    If the candidate User doesn't exist, we create one automatically.
    """
    candidate_email = serializers.EmailField(write_only=True)
    candidate_name = serializers.CharField(write_only=True)
    reference_name = serializers.CharField(required=True)  # Mandatory for this specific view

    class Meta:
        model = Application
        fields = ['job', 'cv_file', 'candidate_email', 'candidate_name', 'reference_name']

    def create(self, validated_data):
        email = validated_data.pop('candidate_email')
        name = validated_data.pop('candidate_name')
        
        # 1. Find or Create the Candidate User
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': name,
                'role': 'Candidate',
                'username': email,  # Assuming username=email based on your User model
            }
        )
        
        # If we created a new user, give them a random password so it doesn't crash
        if created:
            user.set_password(get_random_string(10))
            user.save()

        # 2. Create the Application with the reference tag
        application = Application.objects.create(
            candidate=user,
            has_reference=True,  # Auto-tag as referred
            **validated_data
        )
        return application

class InterviewInviteSerializer(serializers.Serializer):
    date = serializers.DateField()
    time = serializers.TimeField()
    location = serializers.CharField(max_length=255)
    message = serializers.CharField(required=False, allow_blank=True)