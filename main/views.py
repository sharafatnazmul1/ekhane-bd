from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from dokans.models import Store
from .utils.email_service import is_real_email, send_otp_email
from .utils.domain_validator import is_valid_subdomain
from .utils.otp_service import generate_otp, verify_otp, can_resend_otp
import re
import json


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
        # Extract form data
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()
        store_name = request.POST.get("store_name", "").strip()
        subdomain = request.POST.get("subdomain", "").strip().lower()
        phone = request.POST.get("phone", "").strip()

        # Validate all fields
        errors = []

        if not all([name, email, password, store_name, subdomain, phone]):
            errors.append("All fields are required")

        # Email validation
        if email:
            valid, msg = is_real_email(email)
            if not valid:
                errors.append(msg)
            elif User.objects.filter(username=email).exists():
                errors.append("Email already registered")

        # Phone validation
        if phone and not re.match(PHONE_PATTERN, phone):
            errors.append("Invalid Bangladeshi phone number")
        elif phone and User.objects.filter(phone=phone).exists():
            errors.append("Phone number already registered")

        # Subdomain validation
        if subdomain:
            valid, msg = is_valid_subdomain(subdomain)
            if not valid:
                errors.append(msg)
            elif Store.objects.filter(subdomain=subdomain).exists():
                errors.append("Subdomain already taken")

        # Password validation
        if password and len(password) < 8:
            errors.append("Password must be at least 8 characters")

        # If validation errors, return to form
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'registration_template.html')

        # Store registration data in cache (temporary storage until OTP verification)
        registration_data = {
            'name': name,
            'email': email,
            'password': password,
            'store_name': store_name,
            'subdomain': subdomain,
            'phone': phone
        }

        # Store for 10 minutes (600 seconds)
        cache.set(f'registration_data_{email}', registration_data, timeout=600)

        # Generate and send OTP
        otp = generate_otp(email)

        try:
            send_otp_email(email, otp)
        except Exception as e:
            messages.error(request, f"Failed to send verification email: {str(e)}")
            return render(request, 'registration_template.html')

        # Redirect to OTP verification page
        return redirect(f'/verify-otp/?email={email}')

    return render(request, 'registration_template.html')


def verify_otp_view(request):
    email = request.GET.get('email', '').strip().lower()

    if not email:
        messages.error(request, "Invalid verification link")
        return redirect('/registration/')

    # Check if registration data exists
    registration_data = cache.get(f'registration_data_{email}')
    if not registration_data:
        messages.error(request, "Registration session expired. Please register again.")
        return redirect('/registration/')

    if request.method == "POST":
        otp = request.POST.get('otp', '').strip()

        if not otp:
            messages.error(request, "Please enter the OTP code")
            return render(request, 'verify_otp.html', {'email': email})

        # Verify OTP
        valid, msg = verify_otp(email, otp)

        if not valid:
            messages.error(request, msg)
            return render(request, 'verify_otp.html', {'email': email})

        # OTP verified successfully - create user and store
        try:
            # Create user
            user = User.objects.create_user(
                username=registration_data['email'],
                email=registration_data['email'],
                password=registration_data['password'],
                phone=registration_data['phone']
            )
            user.first_name = registration_data['name']
            user.save()

            # Create store
            store = Store.objects.create(
                owner=user,
                store_name=registration_data['store_name'],
                subdomain=registration_data['subdomain'],
                status='active'  # Activate immediately after email verification
            )

            # Clear registration data from cache
            cache.delete(f'registration_data_{email}')

            # Log the user in
            login(request, user)

            messages.success(request, f"Welcome! Your store {store.store_name} has been created successfully!")
            return redirect('/dashboard/')

        except Exception as e:
            messages.error(request, f"Registration error: {str(e)}")
            return render(request, 'verify_otp.html', {'email': email})

    return render(request, 'verify_otp.html', {'email': email})


def resend_otp_view(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip().lower()

        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'})

        # Check if user can resend
        can_resend, remaining = can_resend_otp(email)

        if not can_resend:
            return JsonResponse({
                'success': False,
                'message': f'Please wait {remaining} seconds before requesting another code'
            })

        # Check if registration data still exists
        registration_data = cache.get(f'registration_data_{email}')
        if not registration_data:
            return JsonResponse({
                'success': False,
                'message': 'Registration session expired. Please register again.'
            })

        # Generate and send new OTP
        otp = generate_otp(email)

        try:
            send_otp_email(email, otp)
            return JsonResponse({
                'success': True,
                'message': 'New verification code sent to your email'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Failed to send email: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def login_view(request):
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    if request.method == "POST":
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('remember_me') == 'on'

        if not email or not password:
            messages.error(request, "Please enter both email and password")
            return render(request, 'login.html')

        # Authenticate user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)

            # Set session expiry based on remember me
            if not remember_me:
                request.session.set_expiry(0)  # Session expires when browser closes
            else:
                request.session.set_expiry(1209600)  # 2 weeks

            messages.success(request, f"Welcome back, {user.first_name}!")

            # Redirect to next or dashboard
            next_url = request.GET.get('next', '/dashboard/')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid email or password")
            return render(request, 'login.html')

    return render(request, 'login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully")
    return redirect('/')


@login_required
def dashboard(request):
    try:
        store = request.user.store
    except Store.DoesNotExist:
        messages.error(request, "No store found for your account")
        return redirect('/')

    # Get statistics (will be populated when models are created)
    # For now, using defaults
    total_orders = 0
    total_revenue = 0
    total_products = 0
    total_customers = 0
    recent_orders = []
    low_stock_products = []

    context = {
        'store': store,
        'user': request.user,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_products': total_products,
        'total_customers': total_customers,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'dashboard/index.html', context)


