from django.contrib import admin
from .models import Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    # Columns shown in the list view
    list_display = (
        'candidate_name', 
        'job_title', 
        'match_score_display', 
        'status', 
        'has_reference', 
        'created_at'
    )
    
    # Sidebar filters
    list_filter = ('job', 'status', 'has_reference', 'created_at')
    
    # Search by candidate name, email, or job title
    search_fields = (
        'candidate__full_name', 
        'candidate__email', 
        'job__title', 
        'reference_name'
    )
    
    # Read-only AI data
    readonly_fields = (
        'cv_text_content', 
        'extracted_data', 
        'cv_embedding', 
        'match_score', 
        'created_at'
    )

    fieldsets = (
        ('Application Info', {
            'fields': ('job', 'candidate', 'status', 'cv_file')
        }),
        ('Reference Info', {
            'fields': ('has_reference', 'reference_name')
        }),
        ('Interview Details', {
            'fields': ('interview_date',)
        }),
        ('AI Analysis', {
            'classes': ('collapse',),
            'fields': ('match_score', 'extracted_data', 'cv_text_content', 'cv_embedding')
        }),
    )

    # Custom helpers for the list view
    def candidate_name(self, obj):
        return obj.candidate.full_name
    candidate_name.short_description = 'Candidate'

    def job_title(self, obj):
        return obj.job.title
    job_title.short_description = 'Job Applied For'

    def match_score_display(self, obj):
        return f"{obj.match_score}%"
    match_score_display.short_description = 'AI Score'