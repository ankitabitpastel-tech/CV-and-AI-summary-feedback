from django.urls import path
from . import views


urlpatterns = [
    path('resume/<int:id>', views.user_resume_view, name='user_resume'),

    path('', views.summary_suggestion_view, name='summary_suggestion'),
    path('skills', views.skills_suggestion_view, name='skills_suggestion'),
    path('list', views.user_list, name='user_list'),
    path('export/users/csv/', views.export_users_csv, name='export_users_csv'),



]
