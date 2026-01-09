from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils.crypto import get_random_string

User = get_user_model()


def create_employee_user(email, full_name, role="Employee", password=None):
    if not password:
        password = get_random_string(8)

    with transaction.atomic():
        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            role=role
        )

        send_employee_credentials(user.email, password, user.full_name)

    return user, password


def send_employee_credentials(email, password, name):
    subject = "Welcome to Smart Hire - Your Login Credentials"
    message = f"""
Dear {name},

Your employee account has been created.

Login URL: http://127.0.0.1:8000/login/

Email: {email}
Password: {password}

Please login and change your password.

- Smart Hire System
"""
    send_mail(subject, message, settings.EMAIL_HOST_USER, [email])
