from django.db import models
from django.conf import settings

class Job(models.Model):
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description_text = models.TextField(blank=True)
    description_file = models.FileField(upload_to='job_descriptions/', blank=True, null=True)
    
    # AI Fields
    processed_text = models.TextField(blank=True)
    gliner_entities = models.JSONField(blank=True, null=True)
    jina_embedding = models.JSONField(blank=True, null=True)
    
    # NEW FIELD: Status
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title