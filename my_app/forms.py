import re
from django import forms
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from .models import *
from django.contrib.auth.hashers import make_password, check_password

class SignupForm(forms.ModelForm):

    first_name = forms.CharField(required=True, error_messages={"required": "First name cannot be empty"})

    last_name = forms.CharField(required=False,)
    username = forms.CharField(required=True, error_messages={"required": "Username cannot be empty"})

    email = forms.EmailField(
        required=True,
        validators=[validate_email],
        error_messages={
        "required": "Email is required",
        "invalid": "Enter valid email address"
    }
    )

    # password = forms.CharField(
    #     widget=forms.PasswordInput(attrs={"placeholder": "Enter password"}),
    #     required=True,
    #     validators=[validate_password],
    #     error_messages={"required": "Password cannot be empty"}
    # )
    password = forms.CharField(
    widget=forms.PasswordInput(),
    required=True,
    error_messages={"required": "Password cannot be empty"}
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password"}),
        required=True,
        error_messages={"required": "Confirm Password cannot be empty"}
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username"]

    def clean_email(self):
        email = self.cleaned_data.get("email")

        validate_email(email)

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered")

        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already taken")

        return username
    
    def clean_password(self):
        password = self.cleaned_data.get("password")

        if len(password) < 6:
            raise forms.ValidationError(
                "Password must be at least 6 characters long"
            )

        if not re.search(r"[A-Za-z]", password):
            raise forms.ValidationError(
                "Password must contain at least one letter"
            )

        if not re.search(r"[0-9]", password):
            raise forms.ValidationError(
                "Password must contain at least one number"
            )

        return password

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match")

        return cleaned_data
    
    def save(self, commit=True):

        user = super().save(commit=False)

        user.password_hash = make_password(
            self.cleaned_data["password"]
        )

        if commit:
            user.save()

        return user


class LoginForm(forms.Form):

    username = forms.CharField(
        required=True,
        error_messages={"required": "Username or Email required"}
    )

    password = forms.CharField(
        widget=forms.PasswordInput(),
        required=True,
        error_messages={"required": "Password required"}
    )

