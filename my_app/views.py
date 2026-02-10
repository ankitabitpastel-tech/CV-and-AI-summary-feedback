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
from django.core.mail import send_mail
from django.db.models import OuterRef, Subquery

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.views.decorators.csrf import csrf_exempt
from .utils.encryption import EncryptionService

encryption_service = EncryptionService()


def send_welcome_email(user):

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{
            "email": user.email,
            "name": user.first_name
        }],
        sender={
            "email": settings.DEFAULT_FROM_EMAIL,
            "name": "Job Finder"
        },
        subject="Welcome to Job Finder 🎉",
        html_content=f"""
            <h2>Welcome {user.first_name} 👋</h2>
            <p>Thanks for joining <b>Job Finder</b>.</p>
            <p>We are happy to have you onboard.</p>
            <br>
            <p>Regards,</p>
            <p><b>Team Job Finder</b></p>
        """
    )

    try:
        api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        print("Brevo API Error:", e)


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
                user=form.save()
                print("FROM EMAIL:", settings.DEFAULT_FROM_EMAIL)
                try:
                    send_welcome_email(user)
                except Exception as e:
                    print("Email failed:", e)

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


# def validate_signup_field(request):

#     try:
#         data = json.loads(request.body)
#     except:
#         return JsonResponse({"errors": {}})

#     form = SignupForm(data)
#     form.is_valid()

#     return JsonResponse({
#         "errors": form.errors.get_json_data()
#     })

def validate_signup_field(request):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"errors": {}})

    field_name = data.get("field")
    field_value = data.get("value")

    form = SignupForm({field_name: field_value})
    form.is_valid()

    field_errors = form.errors.get_json_data().get(field_name, [])

    return JsonResponse({
        "errors": {
            field_name: field_errors
        }
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
# @login_required
# def dashboard(request):

#     user_id = request.session.get("user_id")
    

#     if not user_id:
#         return redirect("/login")

#     try:
#         user = User.objects.get(id=user_id)
#     except User.DoesNotExist:
#         request.session.flush()
#         return redirect("/login")
#     usage = user.usage_count or {}

#     return render(request, "auth/dashboard.html", {
#         "user": user, "user_id": user_id, 
#         "summary_count": usage.get("summary", 0),
#         "skills_count": usage.get("skills", 0),})

@login_required
def dashboard(request):

    user_id = request.session.get("user_id")

    user = get_object_or_404(User, id=user_id)

    user.hash_id = encryption_service.encrypt_id(user.id)

    usage = user.usage_count or {}

    return render(request, "auth/dashboard.html", {
        "user": user,
        "summary_count": usage.get("summary", 0),
        "skills_count": usage.get("skills", 0),
    })


@never_cache
@login_required
def logout(request):
    request.session.flush()
    return redirect("/login")

# @login_required
# def user_resume_view(request, id):
#     try:

#         user = get_object_or_404(User, id=id)
#         profile = UserAdditionals.objects.filter(user_id=user.id).first()

#         return render(
#             request,
#             "resume.html",
#             {
#                 "user": user,
#                 "profile": profile,
#             }
#         )

#     except Exception as e:
#         print("Resume error:", e)
#         raise Http404("Resume not found")
@login_required
def user_resume_view(request, hash_id):

    try:
        original_id = encryption_service.decrypt_id(hash_id)

        user = get_object_or_404(User, id=original_id)
        profile = UserAdditionals.objects.filter(user_id=user.id).first()

        return render(request, "resume.html", {
            "user": user,
            "profile": profile,
        })

    except Exception:
        raise Http404("Invalid user")


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
        
        
            # suggestion = generate_summary_suggestion(text_input)
        try:
            result = generate_summary_suggestion(text_input, mode)
            if result :
                count= increment_usage(user, "summary")
                print('sammary',count)
        except Exception as e:
            print("AI ERROR:", e)

            return JsonResponse({
                "error": "AI service is currently unavailable. Please try again later."
            }, status=503)
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
        
        try:
            result = generate_skills_suggestion(skills_input, mode)
            if result :
                count = increment_usage(user, "skills")
                print('skill',count)
        except Exception as e:
            
            print("AI ERROR:", e)
            # result = "AI service failed" 
            return JsonResponse({
                "error": "AI service is currently unavailable. Please try again later."
            }, status=503)
        return JsonResponse({
            "result": result,
            "skills_count": count
        })

    return render(
        request,
        "skill_suggestion.html"
    )

# @login_required
# def user_list(request):
#     current_user=request.session.get('user_id')
#     users = User.objects.exclude(id=current_user)
#     additionals_map = {
#         int(ua.user_id) :ua
#         for ua in UserAdditionals.objects.all()

#     }
#     user_data = []
#     for user in users:
#         user_data.append({
#             'user': user,
#             'additionals': additionals_map.get(user.id)
#         })
#     return render(request, 'user_list.html' ,{
#         'user_data':user_data
#     })



@login_required
def user_list(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            
        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
        search_value = request.GET.get("search[value]", "")

        order_column_index = request.GET.get("order[0][column]", "1")
        order_dir = request.GET.get("order[0][dir]", "asc")

        current_user = request.session.get("user_id")

        additionals = UserAdditionals.objects.filter(
            user_id=OuterRef("id")
        )

        queryset = User.objects.exclude(id=current_user).annotate(

            location=Subquery(additionals.values("location")[:1]),
            gender=Subquery(additionals.values("gender")[:1]),
            college=Subquery(additionals.values("college")[:1]),
            cgpa=Subquery(additionals.values("cgpa")[:1]),
            skills=Subquery(additionals.values("skills")[:1]),
            additional_skills=Subquery(additionals.values("additional_skills")[:1]),

        )

        if search_value:
            queryset = queryset.filter(
                Q(first_name__icontains=search_value) |
                Q(last_name__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(location__icontains=search_value) |
                Q(college__icontains=search_value)|
                Q(skills__icontains=search_value)|
                Q(additional_skills__icontains=search_value)
            )

        total_filtered = queryset.count()

        columns = [
            None,      
            # "id",
            "first_name",
            "email",
            "location",
            "gender",
            "college",
            "cgpa",
            "skills",
            "additional_skills"
        ]

        order_column = columns[int(order_column_index)]

        if order_column:
            if order_dir == "desc":
                order_column = "-" + order_column

            queryset = queryset.order_by(order_column)
        queryset = queryset[start:start + length]

        data = []

        for user in queryset:
            
            # queryset = queryset[start:start + length]

            data.append({
                # "checkbox": f'<input type="checkbox" name="user_ids" value="{user.id}">',
                "checkbox": f'<input type="checkbox" name="user_ids" value="{encryption_service.encrypt_id(user.id)}">',

                # "id": user.id,
                "name": f"{user.first_name} {user.last_name or ''}",
                "email": user.email,
                "location": user.location or "-",
                "gender": user.gender or "-",
                "college": user.college or "-",
                "cgpa": user.cgpa or "-",
                "skills": ", ".join(user.skills) if user.skills else "-",
                "additional_skills": ", ".join(user.additional_skills) if user.additional_skills else "-"
            })

        return JsonResponse({
            "draw": draw,
            "recordsTotal": User.objects.exclude(id=current_user).count(),
            "recordsFiltered": total_filtered,
            "data": data
        })
    return render(request, "user_list.html")



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
