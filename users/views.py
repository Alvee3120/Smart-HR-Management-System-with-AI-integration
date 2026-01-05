from django.shortcuts import render

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlencode

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer, RegisterSerializer

User = get_user_model()

MAGIC_SALT = "magic-login"
MAGIC_EXPIRY = 900  # 15 minutes

def magic_serializer():
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt=MAGIC_SALT)

class RequestMagicLinkView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email required"}, status=400)

        user, created = User.objects.get_or_create(email=email, defaults={"role": "Candidate"})

        token = magic_serializer().dumps({"email": email})
        url = request.build_absolute_uri(
            reverse("users:magic-login") + "?" + urlencode({"token": token})
        )

        send_mail(
            subject="Login to CV Snipping Tool",
            message=f"Click to login: {url}",
            from_email="no-reply@example.com",
            recipient_list=[email],
        )

        return Response({"detail": "Magic login link sent!"})

class MagicLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = request.GET.get("token")
        if not token:
            return Response({"detail": "Token missing"}, status=400)

        try:
            data = magic_serializer().loads(token, max_age=MAGIC_EXPIRY)
        except SignatureExpired:
            return Response({"detail": "Token expired"}, status=400)
        except BadSignature:
            return Response({"detail": "Invalid token"}, status=400)

        email = data["email"]
        user = User.objects.get(email=email)

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })

class MyTokenView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)