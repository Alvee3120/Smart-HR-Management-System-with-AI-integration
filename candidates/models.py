from django.db import models
from django.conf import settings
from jobs.models import Job

class Application(models.Model):
    STATUS_CHOICES = [
        ('APPLIED', 'Applied'),
        ('SCREENED', 'Screened'),
        ('SHORTLISTED', 'Shortlisted'),
        ('REJECTED', 'Rejected'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    
    cv_file = models.FileField(upload_to='cvs/')
    cv_text_content = models.TextField(blank=True)
    extracted_data = models.JSONField(default=dict, blank=True)
    cv_embedding = models.JSONField(default=list, blank=True)
    match_score = models.FloatField(default=0.0)
    
    # --- NEW FIELDS FOR REFERENCE FEATURE ---
    has_reference = models.BooleanField(default=False)
    reference_name = models.CharField(max_length=255, blank=True, null=True)
    
    # --- NEW FIELD FOR INTERVIEW (Optional, for record keeping) ---
    interview_date = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPLIED')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'candidate')

    def __str__(self):
        ref_tag = " (Ref)" if self.has_reference else ""
        return f"{self.candidate.full_name}{ref_tag} -> {self.job.title} ({self.match_score}%)"