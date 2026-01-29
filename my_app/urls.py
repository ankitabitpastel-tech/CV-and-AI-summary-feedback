from django.urls import path
from . import views


urlpatterns = [
    path('resume/<int:id>/', views.user_resume_view, name='user_resume'),

    path('', views.summary_suggestion_view, name='summary_suggestion'),
    
]
