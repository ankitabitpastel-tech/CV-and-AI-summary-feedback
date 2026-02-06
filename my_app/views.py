from django.http import Http404, JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.conf import settings
from .models import *

# from openai import OpenAI
from google import genai

# import google.generativeai as genai
from .forms import *
from django.shortcuts import render, get_object_or_404
from django.http import Http404
import csv
import json
# from .models import User, UserAdditionals
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from .decorators import *
import traceback
from django.views.decorators.cache import never_cache
from django.views.decorators.cache import cache_control



@logout_required
def welcome(request):
    return render(request, "auth/welcome.html")

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@logout_required
def signup(request):

    if request.method == "POST":

        try:
            data = json.loads(request.body)
            form = SignupForm(data)

            if form.is_valid():
                form.save()

                return JsonResponse({
                    "success": True,
                    "redirect": "/login"
                })

            return JsonResponse({
                "success": False,
                "errors": form.errors.get_json_data()
            })

        except Exception as e:
            print("SIGNUP ERROR:", str(e))
            traceback.print_exc()

            return JsonResponse({
                "success": False,
                "error": "Server error"
            })

    return render(request, "auth/signup.html")


def validate_signup_field(request):

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"errors": {}})

    form = SignupForm(data)
    form.is_valid()

    return JsonResponse({
        "errors": form.errors.get_json_data()
    })

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@logout_required
def login(request):

    if request.method == "POST":

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid request"})
        form = LoginForm(data)

        if not form.is_valid():
            return JsonResponse({
                "success": False,
                 "errors": form.errors.get_json_data()
            })

        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        try:
            user = User.objects.get(
                Q(username=username) | Q(email=username)
            )

            if not check_password(password, user.password_hash):
                return JsonResponse({
                    "success": False,
                    "message": "Wrong password"
                })

            request.session["user_id"] = user.id
            request.session.set_expiry(60 * 60 * 24)

            return JsonResponse({
                "success": True,
                "redirect": "/dashboard"
            })

        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "User not found"
            })

    return render(request, "auth/login.html")
def validate_login_field(request):

    if request.method == "POST":
        data = json.loads(request.body)

        form = LoginForm(data)

        form.is_valid()

        return JsonResponse({
            "errors": form.errors.get_json_data()
        })
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def dashboard(request):

    user_id = request.session.get("user_id")
    

    if not user_id:
        return redirect("/login")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("/login")
    usage = user.usage_count or {}

    return render(request, "auth/dashboard.html", {
        "user": user, "user_id": user_id, 
        "summary_count": usage.get("summary", 0),
        "skills_count": usage.get("skills", 0),})

@never_cache
@login_required
def logout(request):
    request.session.flush()
    return redirect("/login")

@login_required
def user_resume_view(request, id):
    try:

        user = get_object_or_404(User, id=id)
        profile = UserAdditionals.objects.filter(user_id=user.id).first()

        return render(
            request,
            "resume.html",
            {
                "user": user,
                "profile": profile,
            }
        )

    except Exception as e:
        print("Resume error:", e)
        raise Http404("Resume not found")

# @login_required
def increment_usage(user: User, feedback_type: str):
    usage = user.usage_count or {}
    usage[feedback_type] = usage.get(feedback_type, 0) + 1
    # usage[feedback_type] += 1

    user.usage_count = usage
    user.save(update_fields=['usage_count'])
    user.refresh_from_db()

    return usage[feedback_type]

# client = OpenAI(api_key=settings.OPENAI_API_KEY)  
# genai.configure(api_key=settings.API_KEY)
client = genai.Client(api_key=settings.API_KEY)
# genai.configure(api_key=settings.API_KEY)

# @login_required
def generate_summary_suggestion(text_input, mode="rating"):
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        if mode == "rating":
            prompt = f"""
                You are a professional resume reviewer.

                ONLY do this:
                1. Rate the resume summary out of 10.
                Return output strictly like:
                Rating: X/10 and generate a 1 line feedback.

                Resume summary:
                {text_input}
                """
        else:
            prompt = f"""
                You are a professional resume reviewer.
        
                Strict rules:
                - Output ONLY bullet points
                - Each line MUST start with: • (bullet symbol)
                - Do NOT use *, -, numbers, or headings
                - No extra text before or after bullets


                Do ONLY these:
                2. Say if the summary is generic
                3. Suggest improvements (bullet points)
                
                Output format:
                    • sentence
                    • sentence
                    • sentence
                Resume summary:
                {text_input}
                give me without any subheading instade provide bulets
                """

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print("Error generating feedback:", e)
        return None

@login_required
def summary_suggestion_view(request):
    # suggestion = None
    # text_input = ""
    user_id = request.session.get("user_id")
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        text_input = request.POST.get("summary_text", "").strip()
        mode= request.POST.get("mode", "rating")

        if not text_input:
            return JsonResponse({"error": "Empty input"}, status=400)
        count= increment_usage(user, "summary")
        print('sammary',count)
        
            # suggestion = generate_summary_suggestion(text_input)
        try:
            result = generate_summary_suggestion(text_input, mode)
        except Exception as e:
            print("AI ERROR:", e)
            result = "AI service failed"
        # result = generate_summary_suggestion(text_input, mode)
        return JsonResponse({
            'result':result,
            "summary_count": count
        })
    return render(
        request,
        "summary_suggestion.html"
    )

# @login_required
def generate_skills_suggestion(skills_input, mode="rating"):
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        if mode == "rating":
            prompt = f"""
            You are a global career advisor and hiring expert.
            
            ONLY do this:
            1. Evaluate the given skills based on current global job market trends.
            3. Provide ONE motivating feedback line with relivant positions they can apply.

            Output format (strict):
             sort feedback


            Skills:
            {skills_input}
            """
        else:
            prompt = f"""
            You are a global career advisor and hiring expert.

            Do ONLY these:
            - Analyze skills based on current global job trends
            - Identify gaps or outdated skills
            - Suggest high-impact skills to add
            - Give motivating, career-oriented guidance
            Strict rules:
            - Output ONLY bullet points
            - Each line MUST start with: • (bullet symbol)
            - Do NOT use *, -, numbers, or headings
            - No extra text before or after bullets

            Rules:
            - NO subheadings
            - Be concise but impactful

            Skills:
            {skills_input}
            """

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print("Error generating skills feedback:", e)
        return None

@login_required
def skills_suggestion_view(request):
    user_id = request.session.get("user_id")
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        skills_input = request.POST.get("skills_text", "").strip()
        mode = request.POST.get("mode", "rating")

        if not skills_input:
            return JsonResponse({"error": "Empty input"}, status=400)
        count = increment_usage(user, "skills")
        print('skill',count)
        try:
            result = generate_skills_suggestion(skills_input, mode)
        except Exception as e:
            print("AI ERROR:", e)
            result = "AI service failed" 
        return JsonResponse({
            "result": result,
            "skills_count": count
        })

    return render(
        request,
        "skill_suggestion.html"
    )

@login_required
def user_list(request):
    users = User.objects.all()
    additionals_map = {
        int(ua.user_id) :ua
        for ua in UserAdditionals.objects.all()

    }
    user_data = []
    for user in users:
        user_data.append({
            'user': user,
            'additionals': additionals_map.get(user.id)
        })
    return render(request, 'user_list.html' ,{
        'user_data':user_data
    })

@login_required
def export_users_csv(request):
    TABLE_COLUMNS = [
    "name",
    "email",
    "location",
    "gender",
    "college",
    "cgpa",
    "skills",
    "additional_skills",
]


    export_type = request.POST.get("export_type", "selected")
    
    selected_columns = request.POST.getlist("columns")
    if export_type == "all":
            selected_columns = TABLE_COLUMNS
            users = User.objects.all()
            additionals = UserAdditionals.objects.all()
    else:
        selected_user_ids = request.POST.getlist("user_ids")
        users = User.objects.filter(id__in=selected_user_ids)
        additionals = UserAdditionals.objects.filter(user_id__in=selected_user_ids)

    additionals_map = {
        ua.user_id: ua for ua in additionals
    }

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="users.csv"'

    writer = csv.writer(response)


    writer.writerow([col.upper() for col in selected_columns])

    for user in users:
        ua = additionals_map.get(user.id)
        row = []

        for col in selected_columns:
            if col == "name":
                row.append(f"{user.first_name} {user.last_name}")
            elif col == "email":
                row.append(user.email)
            elif col == "location":
                row.append(ua.location if ua else "-")
            elif col == "gender":
                row.append(ua.gender if ua else "-")
            elif col == "college":
                row.append(ua.college if ua else "-")
            elif col == "cgpa":
                row.append(ua.cgpa if ua else "-")
            elif col == "skills":
                row.append(ua.skills if ua and ua.skills else "-")
            elif col == "additional_skills":
                row.append(ua.additional_skills if ua and ua.additional_skills else "-")

        writer.writerow(row)

    return response
