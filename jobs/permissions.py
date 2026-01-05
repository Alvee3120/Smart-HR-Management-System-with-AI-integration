from rest_framework import permissions

class IsHR(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'HR'

class IsReviewer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Reviewer'

class IsReviewerOrHR(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # HR can edit their own jobs, Reviewers can edit any job
        if request.user.role == 'Reviewer':
            return True
        if request.user.role == 'HR':
            return obj.posted_by == request.user
        return False