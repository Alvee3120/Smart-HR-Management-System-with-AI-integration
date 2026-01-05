from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView  

from .views import (
    MyTokenView,
    RequestMagicLinkView,
    MagicLoginView,
    RegisterView,  
)
app_name = "users"

urlpatterns = [
    # --- Registration ---
    path("register/", RegisterView.as_view(), name="register"),  

    # --- Standard Login (Email + Pass) ---
    path("login/", MyTokenView.as_view(), name="jwt-login"),

    # --- Magic Link Login (Passwordless) ---
    path("magic/request/", RequestMagicLinkView.as_view(), name="magic-request"),
    path("magic/login/", MagicLoginView.as_view(), name="magic-login"),

    # --- JWT Token Refresh ---
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"), 
]