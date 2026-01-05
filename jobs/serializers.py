from rest_framework import serializers
from .models import Job

class JobSerializer(serializers.ModelSerializer):
    # This helps the frontend show "John Doe" instead of just user ID 5
    posted_by_name = serializers.ReadOnlyField(source='posted_by.full_name') 

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'description_text', 'description_file', 
            'processed_text', 'gliner_entities', 'jina_embedding', 
            'posted_by', 'posted_by_name', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['posted_by', 'processed_text', 'gliner_entities', 'jina_embedding', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Check that the user supplied either text OR a file. 
        We don't want empty jobs.
        """
        if not data.get('description_text') and not data.get('description_file'):
            raise serializers.ValidationError("You must provide either a description text or upload a PDF file.")
        return data