from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.conf import settings
from .models import *
# from openai import OpenAI
# import google.generativeai as genai
from google import genai
import google.generativeai as genai

from django.shortcuts import render, get_object_or_404
from django.http import Http404
# from .models import User, UserAdditionals


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

# client = OpenAI(api_key=settings.OPENAI_API_KEY)  

# genai.configure(api_key=settings.API_KEY)
# client = genai.Client(api_key=settings.API_KEY)
genai.configure(api_key=settings.API_KEY)

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

                Do ONLY these:
                2. Say if the summary is generic
                3. Suggest improvements (bullet points)

                Resume summary:
                {text_input}
                give me without any subheading instade provide bulets
                """

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print("Error generating feedback:", e)
        return None

def summary_suggestion_view(request):
    # suggestion = None
    # text_input = ""

    if request.method == "POST":
        text_input = request.POST.get("summary_text", "").strip()
        mode= request.POST.get("mode", "ratting")

        if not text_input:
            return JsonResponse({"error": "Empty input"}, status=400)
            # suggestion = generate_summary_suggestion(text_input)
        result = generate_summary_suggestion(text_input, mode)

        return JsonResponse({
            'result':result
        })
    return render(
        request,
        "summary_suggestion.html"
    )

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

            Rules:
            - NO subheadings
            - ONLY bullet points
            - Be concise but impactful

            Skills:
            {skills_input}
            """

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print("Error generating skills feedback:", e)
        return None

def skills_suggestion_view(request):
    if request.method == "POST":
        skills_input = request.POST.get("skills_text", "").strip()
        mode = request.POST.get("mode", "rating")

        if not skills_input:
            return JsonResponse({"error": "Empty input"}, status=400)

        result = generate_skills_suggestion(skills_input, mode)

        return JsonResponse({
            "result": result
        })

    return render(
        request,
        "skill_suggestion.html"
    )
