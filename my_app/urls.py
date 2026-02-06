from django.urls import path
from . import views


urlpatterns = [
    path('resume/<int:id>', views.user_resume_view, name='user_resume'),
    path("", views.welcome, name="welcome"),
    path("login", views.login, name="login"),
    path("validate-login-field", views.validate_login_field, name="validate_login_field"),
    path("signup", views.signup, name="signup"),
    path("validate-signup-field", views.validate_signup_field, name="validate_signup_field"),

    path("dashboard", views.dashboard, name="dashboard"),
    path("logout", views.logout, name="logout"),
    path('summary', views.summary_suggestion_view, name='summary_suggestion'),
    path('skills', views.skills_suggestion_view, name='skills_suggestion'),
    path('list', views.user_list, name='user_list'),
    path('export/users/csv/', views.export_users_csv, name='export_users_csv'),



]
