from django import forms
from .models import User

class CustomUserCreationForm(forms.ModelForm):
    # Explicitly define the password fields
    password_1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        strip=False,
    )
    password_2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        strip=False,
        help_text="Enter the same password as before, for verification.",
    )

    class Meta:
        model = User
        fields = ('email', 'full_name', 'role')

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password_1")
        p2 = cleaned_data.get("password_2")
        if p1 and p2 and p1 != p2:
            self.add_error("password_2", "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password_1"])
        if commit:
            user.save()
        return user

class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'full_name', 'role', 'is_active', 'is_staff', 'is_superuser')