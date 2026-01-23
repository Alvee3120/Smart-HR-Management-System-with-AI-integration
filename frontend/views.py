from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from jobs.models import Job
from jobs.utils import run_ai_pipeline  # Import your AI logic
from candidates.models import Application
from candidates.utils import process_application # Import your AI logic
from .forms import JobForm, ApplicationForm, UserLoginForm, UserRegistrationForm,HRUploadCVForm,InterviewInviteForm
from django.http import HttpResponseForbidden
from django.core.mail import send_mail
from django.conf import settings
from employees.models import Employee, Payroll, LeaveRequest
from .forms import LeaveRequestForm
from django.contrib.auth.backends import ModelBackend

User = get_user_model()

@login_required
def dashboard(request):
    """Landing page showing buttons based on Role."""
    return render(request, 'dashboard.html')


@login_required
def reviewer_dashboard(request):
    """Reviewer dashboard - shows all jobs with edit access"""
    if request.user.role != 'Reviewer':
        return redirect('web_test:dashboard')
    
    jobs = Job.objects.select_related('posted_by').order_by('-created_at')
    return render(request, 'frontend/reviewer_dashboard.html', {'jobs': jobs})

@login_required
def job_list(request):
    """Show all jobs. Candidates can apply here."""
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'job_list.html', {'jobs': jobs})




@login_required(login_url='web_test:login')
def apply_for_job(request, job_id):

    # ROLE PROTECTION
    if request.user.role != 'Candidate':
        return HttpResponseForbidden("Only candidates can apply for jobs.")

    job = get_object_or_404(Job, pk=job_id)

    # Check if already applied
    if Application.objects.filter(candidate=request.user, job=job).exists():
        messages.warning(request, "You have already applied!")
        return redirect('web_test:job_list')

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.candidate = request.user
            app.job = job
            app.save()

            # AI pipeline
            process_application(app)

            messages.success(request, f"Applied to {job.title}. AI Score Calculated!")
            return redirect('web_test:job_list')
    else:
        form = ApplicationForm()

    return render(request, 'apply_job.html', {'form': form, 'job': job})

@login_required
def job_ranking(request, job_id):
    """HR Only: See ranked candidates."""
    job = get_object_or_404(Job, pk=job_id)
    
    # Filter by Reference if query param exists (?ref=true)
    apps = Application.objects.filter(job=job)
    if request.GET.get('ref'):
        apps = apps.filter(has_reference=True)
        
    # Order by Match Score
    apps = apps.order_by('-match_score')
    
    return render(request, 'ranking.html', {'job': job, 'applications': apps})


def register_view(request):
    """Handles User Registration"""
    if request.user.is_authenticated:
        return redirect('web_test:home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            backend = ModelBackend()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Welcome, {user.full_name}!")
            return redirect('web_test:home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    """Handles User Login"""
    if request.user.is_authenticated:
        return redirect('web_test:home')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('web_test:home')
    else:
        form = UserLoginForm()

    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('web_test:login')


@login_required(login_url='web_test:login')
def job_detail(request, pk):
    """
    Shows full job info AND the AI 'Brain' (Extracted Entities).
    """
    
    job = get_object_or_404(Job, pk=pk)
    return render(request, 'job_detail.html', {'job': job})

#Create job

@login_required(login_url='web_test:login')
def create_job(request):
    if request.user.role != 'HR':
        messages.error(request, 'Only HR can post jobs.')
        return redirect('web_test:job_list')
    
    if request.method == 'POST':
        form = JobForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            run_ai_pipeline(job)
            messages.success(request, 'Job posted and AI processed!')
            return redirect('web_test:job_list')
        else:
            messages.error(request, 'Please enter either Job Description or pdf.')
    else:
        form = JobForm()
    
    return render(request, 'create_job.html', {'form': form})

#Edit Job

def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk)

    if request.method == 'POST':
        # 'request.FILES' is crucial for PDF updates
        form = JobForm(request.POST, request.FILES, instance=job)
        
        if form.is_valid():
            # 1. Save the basic data (text/file)
            job = form.save()

            # 2. --- FIX: Force AI to re-analyze the new data ---
            try:
                print("Regenerating AI Vectors for updated job...") # Optional debug
                run_ai_pipeline(job) 
                messages.success(request, "Job updated and AI analysis regenerated!")
            except Exception as e:
                # Log error but don't crash the page
                messages.warning(request, f"Job saved, but AI update failed: {e}")
            # ---------------------------------------------------

            return redirect('web_test:job_detail', pk=job.pk)
    else:
        form = JobForm(instance=job)

    return render(request, 'edit_job.html', {'form': form, 'job': job})



#Delete Job

@login_required
def delete_job(request, pk):
    """
    Permanently deletes a job.
    """
    job = get_object_or_404(Job, pk=pk)
    
    if request.user.role != 'HR':
        messages.error(request, "Access Denied.")
        return redirect('web_test:job_list')
        
    if request.method == 'POST':
        title = job.title
        job.delete()
        messages.success(request, f"Job '{title}' has been deleted.")
        return redirect('web_test:job_list')
    
    # If accessed via GET, ask for confirmation
    return render(request, 'delete_job_confirm.html', {'job': job})


@login_required
def toggle_job_status(request, pk):
    """
    Switches job between OPEN and CLOSED.
    """
    job = get_object_or_404(Job, pk=pk)
    
    if request.user.role != 'HR':
        messages.error(request, "Access Denied.")
        return redirect('web_test:job_list')

    if job.status == 'OPEN':
        job.status = 'CLOSED'
        messages.info(request, "Job marked as CLOSED. No new applicants allowed.")
    else:
        job.status = 'OPEN'
        messages.success(request, "Job Re-Opened!")
    
    job.save()
    return redirect('web_test:job_detail', pk=job.pk)


@login_required
def application_detail(request, pk):
    """
    Shows a deep-dive comparison between the Job Requirements and the Candidate's CV.
    Includes:
    1. Fuzzy Matching for Skills (e.g. 'React' matches 'React.js')
    2. Logic Comparison for Experience (e.g. 4.2 Years >= 4 Years)
    """
    application = get_object_or_404(Application, pk=pk)
    
    if request.user.role != 'HR' and request.user != application.candidate:
        messages.error(request, "Access Denied.")
        return redirect('web_test:dashboard')

    # --- GAP ANALYSIS LOGIC ---
    
    # UPDATE: Added 'Skill (Detected)' to include regex-found skills in analysis
    tech_labels = [
        'Skill', 'Technology', 'Framework', 'Programming Language', 
        'Database', 'Tool', 'Platform', 'Cloud', 'Service',
        'Skill (Detected)' 
    ]

    # 1. PREPARE SKILL DATA
    job_skills_map = {}
    if application.job.gliner_entities:
        for item in application.job.gliner_entities:
            if item['label'] in tech_labels:
                job_skills_map[item['text'].strip().lower()] = item['text'].strip()

    cv_skills_map = {}
    if application.extracted_data:
        for item in application.extracted_data:
            if item['label'] in tech_labels:
                cv_skills_map[item['text'].strip().lower()] = item['text'].strip()

    matches = []
    misses = []
    extras = []
    
    # 2. EXPERIENCE LOGIC
    req_years = 0
    cand_years = 0.0

    # Get Job Requirement
    if application.job.gliner_entities:
        for item in application.job.gliner_entities:
            if item.get('label') == 'Min_Years_Req':
                try:
                    req_years = int(item['text'])
                except ValueError:
                    req_years = 0
                break

    # Get Candidate Actual
    if application.extracted_data:
        for item in application.extracted_data:
            if item.get('label') == 'Total_Years_Calc':
                try:
                    cand_years = float(item['text'])
                except ValueError:
                    cand_years = 0.0
                break

    # Compare Years
    if req_years > 0:
        if cand_years >= req_years:
            matches.insert(0, f"✅ {cand_years} Years Experience (Matches {req_years}+ Req)")
        else:
            misses.insert(0, f"❌ Requires {req_years}+ Years (Has {cand_years})")
    elif cand_years > 0:
        extras.insert(0, f"{cand_years} Years Total Experience")

    # 3. SKILLS MATCHING LOGIC
    synonyms = {
        "drf": "django rest framework",
        "reactjs": "react",
        "js": "javascript",
        "aws": "amazon web services",
        "postgres": "postgresql",
        "k8s": "kubernetes",
    }

    # CHECK JOB SKILLS
    for j_key, j_text in job_skills_map.items():
        matched = False
        
        # Strategy A: Exact Match
        if j_key in cv_skills_map:
            matches.append(j_text) 
            matched = True
            
        # Strategy B: Substring & Synonyms
        else:
            for c_key, c_text in cv_skills_map.items():
                if len(c_key) > 2 and len(j_key) > 2:
                    if c_key in j_key: 
                        matches.append(f"{c_text} (matches {j_text})")
                        matched = True
                        break
                    if j_key in c_key:
                        matches.append(c_text)
                        matched = True
                        break
                
                std_j = synonyms.get(j_key, j_key)
                std_c = synonyms.get(c_key, c_key)
                if std_j == std_c or std_c in std_j:
                    matches.append(f"{c_text} (matches {j_text})")
                    matched = True
                    break

        if not matched:
            misses.append(j_text)

    # CHECK EXTRAS
    match_strings = " ".join(matches).lower()
    
    for c_key, c_text in cv_skills_map.items():
        if c_key not in match_strings and c_key not in job_skills_map:
            extras.append(c_text)

    context = {
        'app': application,
        'matches': matches,
        'misses': misses,
        'extras': extras,
    }
        
    return render(request, 'application_detail.html', context)

@login_required
def hr_upload_cv(request, job_id):
    """
    Allows HR to manually upload a CV for a candidate.
    Creates a User account for the candidate if one doesn't exist.
    """
    job = get_object_or_404(Job, pk=job_id)

    # Security: Only HR can access this
    if request.user.role != 'HR':
        messages.error(request, "Access Denied.")
        return redirect('web_test:job_list')

    if request.method == 'POST':
        form = HRUploadCVForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data['email']
            name = form.cleaned_data['full_name']
            cv_file = form.cleaned_data['cv_file']
            ref_name = form.cleaned_data['reference_name']

            # 1. Get or Create Candidate User
            candidate, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'full_name': name,
                    'role': 'Candidate',
                    
                }
            )
            if created:
                candidate.set_unusable_password() # They can reset it later
                candidate.save()

            # 2. Check if already applied
            if Application.objects.filter(job=job, candidate=candidate).exists():
                messages.warning(request, f"{name} has already applied for this job.")
                return redirect('web_test:job_ranking', job_id=job.id)

            # 3. Create Application
            application = Application.objects.create(
                job=job,
                candidate=candidate,
                cv_file=cv_file,
                has_reference=bool(ref_name),
                reference_name=ref_name
            )

            # 4. Trigger AI
            process_application(application)

            messages.success(request, f"CV uploaded for {name}. AI Scoring started!")
            return redirect('web_test:job_ranking', job_id=job.id)
    else:
        form = HRUploadCVForm()

    return render(request, 'hr_upload_cv.html', {'form': form, 'job': job})


@login_required
def send_interview_invite(request, application_id):
    """
    HR submits the Interview Form.
    1. Updates Application Status -> 'INTERVIEW'
    2. Sends Email to Candidate.
    """
    application = get_object_or_404(Application, pk=application_id)
    
    # Security Check
    if request.user.role != 'HR':
        messages.error(request, "Access Denied.")
        return redirect('web_test:dashboard')

    if request.method == 'POST':
        form = InterviewInviteForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # 1. Update Application Status
            application.status = 'INTERVIEW'
            # Assuming you have an 'interview_date' field, or we just save it in notes
            # If your model handles datetime, combine data['date'] and data['time']
            application.save()

            # 2. Send Email
            subject = f"Interview Invitation: {application.job.title}"
            message_body = (
                f"Dear {application.candidate.full_name},\n\n"
                f"We are pleased to invite you for an interview for the position of {application.job.title}.\n\n"
                f"📅 Date: {data['date']}\n"
                f"⏰ Time: {data['time']}\n"
                f"📍 Location: {data['location']}\n\n"
                f"Notes: {data['message']}\n\n"
                f"Best regards,\nSmart Hire Solutions Team"
            )

            try:
                send_mail(
                    subject,
                    message_body,
                    settings.EMAIL_HOST_USER or 'noreply@smarthire.com',
                    [application.candidate.email],
                    fail_silently=False,
                )
                messages.success(request, f"Invite sent to {application.candidate.full_name}!")
            except Exception as e:
                messages.error(request, f"Error sending email: {e}")

            return redirect('web_test:job_ranking', job_id=application.job.id)
    
    # If not POST, just redirect back
    return redirect('web_test:job_ranking', job_id=application.job.id)


# In frontend/views.py

@login_required
def bulk_send_invite(request):
    """
    Process the Bulk Interview Invite Form.
    """
    if request.user.role != 'HR':
        messages.error(request, "Access Denied.")
        return redirect('web_test:dashboard')

    if request.method == 'POST':
        form = InterviewInviteForm(request.POST)
        if form.is_valid():
            ids_str = form.cleaned_data['application_ids']
            date = form.cleaned_data['date']
            time = form.cleaned_data['time']
            location = form.cleaned_data['location']
            notes = form.cleaned_data['message']

            # Parse IDs
            app_ids = [int(id) for id in ids_str.split(',') if id.isdigit()]
            
            applications = Application.objects.filter(id__in=app_ids)
            success_count = 0
            errors = []
            
            for app in applications:
                # 1. Update Status
                app.status = 'INTERVIEW'
                app.save()

                # 2. Send Email
                subject = f"Interview Invitation: {app.job.title}"
                message_body = (
                    f"Dear {app.candidate.full_name},\n\n"
                    f"We are pleased to invite you for an interview.\n\n"
                    f"📅 Date: {date}\n"
                    f"⏰ Time: {time}\n"
                    f"📍 Location: {location}\n\n"
                    f"Notes: {notes}\n\n"
                    f"Best regards,\nSmart Hire Solutions Team"
                )
                
                try:
                    send_mail(
                        subject, message_body, 
                        settings.EMAIL_HOST_USER or 'noreply@smarthire.com', 
                        [app.candidate.email], fail_silently=False
                    )
                    success_count += 1
                except Exception as e:
                    # Collect error messages to show the user
                    errors.append(f"{app.candidate.email}: {str(e)}")

            # 3. Show Feedback
            if success_count > 0:
                messages.success(request, f"✅ Sent invites to {success_count} candidates!")
            
            if errors:
                messages.error(request, f"❌ Failed to send {len(errors)} emails. Check console for details.")
                # Print exact errors to the terminal so you can debug
                for err in errors:
                    print(f"EMAIL ERROR: {err}")

            if applications.exists():
                return redirect('web_test:job_ranking', job_id=applications.first().job.id)
            
    return redirect('web_test:job_list')


@login_required
def employee_dashboard(request):
    """
    Employee Dashboard: View Profile, Payroll History, and Apply for Leave.
    """
    # 1. Ensure the user is an Employee
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        messages.error(request, "Access Denied: You do not have an employee profile.")
        return redirect('web_test:dashboard')

    # 2. Handle Leave Request Form Submission
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = employee
            leave.save()
            messages.success(request, "Leave request submitted successfully!")
            return redirect('web_test:employee_dashboard')
    else:
        form = LeaveRequestForm()

    # 3. Fetch Data for Dashboard
    payrolls = Payroll.objects.filter(employee=employee).order_by('-month')
    leave_requests = LeaveRequest.objects.filter(employee=employee).order_by('-start_date')

    context = {
        'employee': employee,
        'payrolls': payrolls,
        'leave_requests': leave_requests,
        'form': form
    }
    return render(request, 'employee_dashboard.html', context)

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def service(request):
    return render(request, 'service.html')

def portfolio(request):
    return render(request, 'portfolio.html')

def career(request):
    return render(request, 'career.html')

def career(request):
    # Fetch only OPEN jobs for the public career page
    jobs = Job.objects.filter(status='OPEN').order_by('-id')
    return render(request, 'career.html', {'jobs': jobs})

@login_required(login_url='web_test:login')
def dashboard(request):
    user = request.user
    role = user.role

    # --- HR DASHBOARD ---
    if role == 'HR':
        # Context data for HR
        active_jobs = Job.objects.filter(posted_by=user, status='OPEN')
        recent_jobs = Job.objects.filter(posted_by=user).order_by('-created_at')[:5]
        
        context = {
            'active_jobs_count': active_jobs.count(),
            'total_applications_count': Application.objects.filter(job__posted_by=user).count(),
            'pending_reviews_count': 0, # Add logic if you have review models
            'recent_jobs': recent_jobs,
            'user': user
        }
        return render(request, 'dashboard/hr_dashboard.html', context)

    # --- ADMIN DASHBOARD ---
    elif role == 'ADMIN' or user.is_superuser:
        context = {
            'total_users': User.objects.count(),
            'total_jobs': Job.objects.count(),
            'total_applications': Application.objects.count(),
            'hired_count': Application.objects.filter(status='Accepted').count(),
            'user': user
        }
        return render(request, 'dashboard/admin_dashboard.html', context)

    # --- CANDIDATE DASHBOARD ---
    elif role == 'Candidate':
        # Fetch applications made by this candidate
        my_applications = Application.objects.filter(candidate=request.user).select_related('job').order_by('-created_at')
        
        context = {
            'applications': my_applications,
            'user': user
        }
        return render(request, 'dashboard/candidate_dashboard.html', context)

    # --- EMPLOYEE DASHBOARD (Redirect or Render) ---
    elif role == 'Employee':
        # Since you already have a separate view for this, we can redirect to it
        return redirect('web_test:employee_dashboard')

    # --- FALLBACK ---
    else:
        return render(request, 'dashboard.html', {'user': user})
    

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from jobs.models import Job
from candidates.models import Application

@login_required
def hr_dashboard(request):
    if request.user.role not in ['HR', 'Admin']:
        return redirect('web_test:dashboard')

    active_jobs_count = Job.objects.filter(status='OPEN').count()
    total_applications_count = Application.objects.count()
    pending_reviews_count = Application.objects.filter(status='PENDING').count()
    recent_jobs = Job.objects.order_by('-created_at')[:5]

    return render(request, 'dashboard/hr_dashboard.html', {
        'active_jobs_count': active_jobs_count,
        'total_applications_count': total_applications_count,
        'pending_reviews_count': pending_reviews_count,
        'recent_jobs': recent_jobs,
    })


@login_required
def hr_job_list(request):
    if request.user.role not in ['HR', 'Admin']:
        return redirect('web_test:dashboard')

    jobs = Job.objects.select_related('posted_by').all().order_by('-id')
    return render(request, 'hr/jobs/job_list.html', {'jobs': jobs})