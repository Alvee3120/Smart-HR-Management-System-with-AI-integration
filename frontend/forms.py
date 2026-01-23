from django import forms
from jobs.models import Job
from candidates.models import Application
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from employees.models import LeaveRequest 


User = get_user_model()


# =========================
# Common Tailwind classes
# =========================
INPUT = "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
TEXTAREA = "w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
FILE = "w-full text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700"
SELECT = "w-full px-3 py-2 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"


# =========================
# Job Form
# =========================
# class JobForm(forms.ModelForm):
#     class Meta:
#         model = Job
#         fields = ['title', 'description_text', 'description_file']
#         widgets = {
#             'title': forms.TextInput(attrs={
#                 'class': INPUT,
#                 'placeholder': 'Job title'
#             }),
#             'description_text': forms.Textarea(attrs={
#                 'class': TEXTAREA,
#                 'rows': 4,
#                 'placeholder': 'Write job description...'
#             }),
#             'description_file': forms.FileInput(attrs={
#                 'class': FILE
#             }),
#         }

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description_text', 'description_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full rounded border-gray-300'}),
            'description_text': forms.Textarea(attrs={'rows': 6, 'class': 'w-full rounded border-gray-300'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get('description_text', '').strip()
        file = cleaned_data.get('description_file')
        
        # Require title
        if not cleaned_data.get('title', '').strip():
            raise forms.ValidationError("Job title is required.")
        
        # Exactly one of text or file
        if not text and not file:
            raise forms.ValidationError("Provide either description text or upload a PDF file.")
        if text and file:
            raise forms.ValidationError("Provide only one: either description text OR file upload.")
        
        return cleaned_data

# =========================
# Application Form
# =========================
class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cv_file']
        widgets = {
            'cv_file': forms.FileInput(attrs={
                'class': FILE
            }),
        }


# =========================
# Login Form
# =========================
class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': INPUT,
            'placeholder': 'Email address'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT,
            'placeholder': 'Password'
        })
    )


# =========================
# Registration Form
# =========================
class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': INPUT,
            'placeholder': 'Full name'
        })
    )

    class Meta:
        model = User
        fields = ('email', 'full_name')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': INPUT,
                'placeholder': 'Email address'
            }),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Roles.CANDIDATE
        if commit:
            user.save()
        return user


# =========================
# HR Upload CV Form
# =========================
class HRUploadCVForm(forms.Form):
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': INPUT,
            'placeholder': 'Candidate name'
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': INPUT,
            'placeholder': 'Candidate email'
        })
    )

    cv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': FILE
        })
    )

    reference_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT,
            'placeholder': 'Referrer name (optional)'
        })
    )


# =========================
# Interview Invite Form
# =========================
class InterviewInviteForm(forms.Form):
    application_ids = forms.CharField(widget=forms.HiddenInput())

    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': INPUT
        }),
        label="Interview Date"
    )

    time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': INPUT
        }),
        label="Interview Time"
    )

    location = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': INPUT,
            'placeholder': 'Google Meet link or office address'
        }),
        label="Location / Link"
    )

    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': TEXTAREA,
            'rows': 3,
            'placeholder': 'Any specific instructions...'
        }),
        label="Additional Message"
    )

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={'class': SELECT}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': INPUT}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': INPUT}),
            'reason': forms.Textarea(attrs={'class': TEXTAREA, 'rows': 3, 'placeholder': 'Reason for leave...'}),
        }