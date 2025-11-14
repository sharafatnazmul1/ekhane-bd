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
    path('', public_views.home, name='home'),
    path('registration/', public_views.signup, name="signup"),
    path("validate/", public_views.validate_field, name="validate-field"),
    path('verify-otp/', public_views.verify_otp_view, name='verify-otp'),
    path('resend-otp/', public_views.resend_otp_view, name='resend-otp'),
    path('login/', public_views.login_view, name='login'),
    path('logout/', public_views.logout_view, name='logout'),
    path('dashboard/', public_views.dashboard, name='dashboard'),
    path('dashboard/products/', include('products.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
