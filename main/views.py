from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from dokans.models import Store
from .utils.email_service import is_real_email
from .utils.domain_validator import is_valid_subdomain
import re


User = get_user_model()
PHONE_PATTERN = r"^1\d{9}$"

def validate_field(request):
    field = request.GET.get("field", "").strip()
    value = request.GET.get("value", "").strip()

    if not field or not value:
        return JsonResponse({"valid": False, "msg": "Invalid request"})

    # ✅ Email validation
    if field == "email":
        valid, msg = is_real_email(value)
        if not valid:
            return JsonResponse({"valid": False, "msg": msg})

        if User.objects.filter(username=value).exists():
            return JsonResponse({"valid": False, "msg": "Email already registered"})

        return JsonResponse({"valid": True})


    # ✅ Phone validation
    if field == "phone":
        if not re.match(PHONE_PATTERN, value):
            return JsonResponse({"valid": False, "msg": "Enter a valid Bangladeshi phone number"})

        if User.objects.filter(phone=value).exists():
            return JsonResponse({"valid": False, "msg": "Phone number already registered"})

        return JsonResponse({"valid": True})


    # ✅ Subdomain validation
    if field == "subdomain":
        valid, msg = is_valid_subdomain(value)
        if not valid:
            return JsonResponse({"valid": False, "msg": msg})

        if Store.objects.filter(subdomain=value).exists():
            return JsonResponse({"valid": False, "msg": "Subdomain already taken"})

        return JsonResponse({"valid": True})


    # Unknown field
    return JsonResponse({"valid": False, "msg": "Invalid validation field"})



# Create your views here.
def home(request):
    lang = request.GET.get('lang', 'bn')
    context = {
        'lang': lang
    }
    return render(request, 'home.html', context)


def signup(request):
    if request.method == "POST":
        print("pass")


    return render(request, 'registration_template.html', )


