"""
URL configuration for ekhanebd project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from main import views as public_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Main site URLs
    path('', public_views.home, name='home'),
    path('registration/', public_views.signup, name="signup"),
    path("validate/", public_views.validate_field, name="validate-field"),
    path('verify-otp/', public_views.verify_otp_view, name='verify-otp'),
    path('resend-otp/', public_views.resend_otp_view, name='resend-otp'),
    path('login/', public_views.login_view, name='login'),
    path('logout/', public_views.logout_view, name='logout'),

    # Dashboard URLs
    path('dashboard/', public_views.dashboard, name='dashboard'),
    path('dashboard/products/', include('products.urls')),
    path('dashboard/orders/', public_views.order_list, name='order_list'),
    path('dashboard/orders/<int:order_id>/', public_views.order_detail, name='order_detail'),
    path('dashboard/customers/', public_views.customer_list, name='customer_list'),
    path('dashboard/settings/', public_views.store_settings, name='store_settings'),

    # Storefront URLs (work on subdomains via middleware)
    path('shop/', public_views.shop_home, name='shop_home'),
    path('shop/products/', public_views.shop_products, name='shop_products'),
    path('shop/product/<slug:slug>/', public_views.shop_product_detail, name='shop_product_detail'),

    # Cart URLs
    path('cart/', public_views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', public_views.cart_add, name='cart_add'),
    path('cart/update/<int:item_id>/', public_views.cart_update, name='cart_update'),
    path('cart/remove/<int:item_id>/', public_views.cart_remove, name='cart_remove'),

    # Checkout URLs
    path('checkout/', public_views.checkout, name='checkout'),
    path('order/<str:order_number>/', public_views.order_confirmation, name='order_confirmation'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
