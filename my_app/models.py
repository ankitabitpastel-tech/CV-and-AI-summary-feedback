from django.db import models
from django.utils import timezone


class User(models.Model):
    id = models.BigAutoField(primary_key=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)

    password_hash = models.TextField()  

    profile_image = models.URLField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    # is_verified = models.BooleanField(default=False)
    usage_count = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "users"
        managed = True

    def __str__(self):
        return self.email


class UserAdditionals(models.Model):
    id = models.BigAutoField(primary_key=True)

    # Keep it loose (no FK dependency)
    user_id = models.BigIntegerField()

    location = models.TextField(null=True, blank=True)
    dob = models.DateField(null=True, blank=True)

    gender = models.CharField(max_length=100, null=True, blank=True)

    college_degree = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    college = models.TextField(null=True, blank=True)

    study_field = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    start_year = models.TextField(null=True, blank=True)
    end_year = models.TextField(null=True, blank=True)

    cgpa = models.CharField(max_length=10, null=True, blank=True)

    skills = models.JSONField(null=True, blank=True)

    # certificate_url = models.TextField(null=True, blank=True)

    additional_skills = models.JSONField(null=True, blank=True)

    about = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_additionals"
        managed = True

    def __str__(self):
        return f"UserAdditionals (user_id={self.user_id})"
