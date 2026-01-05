from django.contrib import admin
from .models import Job

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    # Columns shown in the list view
    list_display = ('title', 'posted_by', 'status', 'created_at', 'has_file')
    
    # Sidebar filters
    list_filter = ('status', 'created_at', 'posted_by')
    
    # Search box functionality
    search_fields = ('title', 'description_text', 'posted_by__email')
    
    # Prevent accidental editing of AI-generated data
    readonly_fields = ('processed_text', 'gliner_entities', 'jina_embedding', 'created_at', 'updated_at')

    # Organize the detail view nicely
    fieldsets = (
        ('Job Details', {
            'fields': ('title', 'posted_by', 'status', 'description_text', 'description_file')
        }),
        ('AI Processing', {
            'classes': ('collapse',),  # Collapsible section
            'fields': ('processed_text', 'gliner_entities', 'jina_embedding')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def has_file(self, obj):
        return bool(obj.description_file)
    has_file.boolean = True  # Shows a nice green checkmark icon
    has_file.short_description = "Has PDF?"


    # Helper to check if AI processed the job
    def has_ai_data(self, obj):
        return bool(obj.jina_embedding)
    has_ai_data.boolean = True
    has_ai_data.short_description = "AI Processed"