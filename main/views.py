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

    # Import Product model
    from products.models import Product

    # Get statistics
    total_orders = 0  # Will be populated when Order model is created
    total_revenue = 0  # Will be populated when Order model is created
    total_products = Product.objects.filter(store=store).count()
    total_customers = 0  # Will be populated when Customer model is created
    recent_orders = []  # Will be populated when Order model is created
    low_stock_products = [p for p in Product.objects.filter(store=store, track_inventory=True)[:5] if p.is_low_stock]

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


# ============================================================================
# STOREFRONT VIEWS (Customer-Facing Shop)
# ============================================================================

def shop_home(request):
    """Storefront homepage - shows featured/all products"""
    store = request.store  # Set by SubdomainMiddleware

    if not store:
        return redirect('/')

    from products.models import Product

    # Get products
    featured_products = Product.objects.filter(store=store, is_active=True, is_featured=True)[:8]
    all_products = Product.objects.filter(store=store, is_active=True)[:12]

    # Get cart count
    cart_count = get_cart_count(request, store)

    context = {
        'store': store,
        'featured_products': featured_products,
        'all_products': all_products,
        'cart_count': cart_count,
    }
    return render(request, 'shop/home.html', context)


def shop_products(request):
    """Product listing page"""
    store = request.store

    if not store:
        return redirect('/')

    from products.models import Product, Category

    # Get filters
    category_slug = request.GET.get('category')
    search = request.GET.get('search', '')

    # Base queryset
    products = Product.objects.filter(store=store, is_active=True)

    # Apply filters
    if category_slug:
        products = products.filter(category__slug=category_slug)

    if search:
        from django.db.models import Q
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    # Get categories
    categories = Category.objects.filter(store=store, is_active=True)
    cart_count = get_cart_count(request, store)

    context = {
        'store': store,
        'products': products,
        'categories': categories,
        'search': search,
        'cart_count': cart_count,
    }
    return render(request, 'shop/products.html', context)


def shop_product_detail(request, slug):
    """Product detail page"""
    store = request.store

    if not store:
        return redirect('/')

    from products.models import Product
    from django.shortcuts import get_object_or_404

    product = get_object_or_404(Product, store=store, slug=slug, is_active=True)
    cart_count = get_cart_count(request, store)

    context = {
        'store': store,
        'product': product,
        'cart_count': cart_count,
    }
    return render(request, 'shop/product_detail.html', context)


# ============================================================================
# CART FUNCTIONS
# ============================================================================

def get_or_create_cart(request, store):
    """Get or create cart for current session/customer"""
    from orders.models import Cart

    # Get session key
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    # Try to get existing cart
    cart, created = Cart.objects.get_or_create(
        store=store,
        session_key=session_key,
        defaults={'store': store}
    )

    return cart


def get_cart_count(request, store):
    """Get total items in cart"""
    from orders.models import Cart

    if not request.session.session_key:
        return 0

    try:
        cart = Cart.objects.get(store=store, session_key=request.session.session_key)
        return cart.total_items
    except Cart.DoesNotExist:
        return 0


# ============================================================================
# CART VIEWS
# ============================================================================

def cart_view(request):
    """View cart"""
    store = request.store

    if not store:
        return redirect('/')

    cart = get_or_create_cart(request, store)

    context = {
        'store': store,
        'cart': cart,
        'cart_count': cart.total_items,
    }
    return render(request, 'shop/cart.html', context)


def cart_add(request, product_id):
    """Add product to cart (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})

    store = request.store
    if not store:
        return JsonResponse({'success': False, 'message': 'Store not found'})

    from products.models import Product
    from django.shortcuts import get_object_or_404

    try:
        product = get_object_or_404(Product, id=product_id, store=store, is_active=True)

        # Check stock
        if product.track_inventory and product.stock_quantity < 1:
            return JsonResponse({'success': False, 'message': 'Product out of stock'})

        cart = get_or_create_cart(request, store)
        cart.add_item(product, quantity=1)

        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart',
            'cart_count': cart.total_items
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def cart_update(request, item_id):
    """Update cart item quantity (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})

    store = request.store
    if not store:
        return JsonResponse({'success': False, 'message': 'Store not found'})

    from orders.models import CartItem
    import json

    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))

        cart = get_or_create_cart(request, store)
        cart_item = CartItem.objects.get(id=item_id, cart=cart)

        # Update quantity
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            message = 'Cart updated'
        else:
            cart_item.delete()
            message = 'Item removed from cart'

        cart.refresh_from_db()

        return JsonResponse({
            'success': True,
            'message': message,
            'cart_count': cart.total_items,
            'subtotal': float(cart.subtotal)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def cart_remove(request, item_id):
    """Remove item from cart"""
    store = request.store
    if not store:
        return redirect('/')

    from orders.models import CartItem

    cart = get_or_create_cart(request, store)

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        cart_item.delete()
        messages.success(request, 'Item removed from cart')
    except CartItem.DoesNotExist:
        messages.error(request, 'Item not found')

    return redirect('cart_view')


# ============================================================================
# CHECKOUT & ORDER VIEWS
# ============================================================================

def checkout(request):
    """Checkout page"""
    store = request.store
    if not store:
        return redirect('/')

    cart = get_or_create_cart(request, store)

    if cart.total_items == 0:
        messages.error(request, 'Your cart is empty')
        return redirect('cart_view')

    if request.method == 'POST':
        return process_checkout(request, store, cart)

    context = {
        'store': store,
        'cart': cart,
        'cart_count': cart.total_items,
    }
    return render(request, 'shop/checkout.html', context)


def process_checkout(request, store, cart):
    """Process checkout and create order"""
    from orders.models import Customer, Order, OrderItem, Payment

    # Get form data
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    address = request.POST.get('address', '').strip()
    division = request.POST.get('division', '').strip()
    district = request.POST.get('district', '').strip()
    area = request.POST.get('area', '').strip()
    notes = request.POST.get('notes', '').strip()
    payment_method = request.POST.get('payment_method', 'cod')

    # Validate
    if not all([name, email, phone, address, division, district]):
        messages.error(request, 'Please fill in all required fields')
        return redirect('checkout')

    # Get or create customer
    customer, created = Customer.objects.get_or_create(
        store=store,
        email=email,
        defaults={'name': name, 'phone': phone}
    )

    if not created:
        customer.name = name
        customer.phone = phone
        customer.save()

    # Create order
    subtotal = cart.subtotal
    shipping_cost = 0  # Can be customized based on store settings
    total = subtotal + shipping_cost

    order = Order.objects.create(
        store=store,
        customer=customer,
        status='pending',
        payment_method=payment_method,
        payment_status='pending',
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=total,
        shipping_name=name,
        shipping_email=email,
        shipping_phone=phone,
        shipping_address=address,
        shipping_division=division,
        shipping_district=district,
        shipping_area=area,
        notes=notes
    )

    # Create order items from cart
    for cart_item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            product_name=cart_item.product.name,
            product_sku=cart_item.product.sku,
            quantity=cart_item.quantity,
            price=cart_item.price,
            total=cart_item.total
        )

        # Reduce stock if tracking inventory
        if cart_item.product.track_inventory:
            cart_item.product.stock_quantity -= cart_item.quantity
            cart_item.product.save()

    # Create payment record
    payment = Payment.objects.create(
        order=order,
        payment_method=payment_method,
        amount=total,
        status='pending'
    )

    # Clear cart
    cart.clear()

    # Handle payment method
    if payment_method == 'cod':
        # COD - order is confirmed, payment pending
        order.status = 'confirmed'
        order.save()
        return redirect('order_confirmation', order_number=order.order_number)
    elif payment_method == 'bkash':
        # Redirect to bKash payment (will implement later)
        messages.info(request, 'bKash payment coming soon. Using COD for now.')
        order.status = 'confirmed'
        order.save()
        return redirect('order_confirmation', order_number=order.order_number)

    return redirect('order_confirmation', order_number=order.order_number)


def order_confirmation(request, order_number):
    """Order confirmation page"""
    store = request.store
    if not store:
        return redirect('/')

    from orders.models import Order
    from django.shortcuts import get_object_or_404

    order = get_object_or_404(Order, order_number=order_number, store=store)

    context = {
        'store': store,
        'order': order,
        'cart_count': 0,  # Cart is empty after checkout
    }
    return render(request, 'shop/order_confirmation.html', context)


