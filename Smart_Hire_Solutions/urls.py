from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/users/", include("users.urls", namespace="users")),
    path("api/jobs/", include("jobs.urls", namespace="jobs")),
    path('api/candidates/', include('candidates.urls', namespace='candidates')),
    path('', include('frontend.urls')),
]

# This allows you to open the PDF link in your browser during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)