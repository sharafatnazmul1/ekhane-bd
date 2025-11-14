from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Store


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'phone', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'phone')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'subdomain', 'owner', 'status', 'trial_end', 'is_trial_active', 'created_at')
    list_filter = ('status', 'created_at', 'trial_end')
    search_fields = ('store_name', 'subdomain', 'owner__email', 'owner__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    fieldsets = (
        ('Store Information', {
            'fields': ('store_name', 'subdomain', 'owner')
        }),
        ('Status & Trial', {
            'fields': ('status', 'trial_end', 'created_at')
        }),
    )

    def is_trial_active(self, obj):
        return obj.is_trial_active()
    is_trial_active.boolean = True
    is_trial_active.short_description = 'Trial Active'
