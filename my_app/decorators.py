from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse

def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("user_id"):
            if request.method == "POST":
                return JsonResponse({"error": "Not logged in"}, status=403)
            return redirect("/login")
        return view_func(request, *args, **kwargs)
    return wrapper

def logout_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.session.get("user_id"):
            return redirect("/dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper