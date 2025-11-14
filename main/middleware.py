from django.shortcuts import redirect, render
from django.urls import resolve
from django.conf import settings
from dokans.models import Store


class SubdomainMiddleware:
    """
    Middleware to handle subdomain-based multi-tenancy.

    Routes:
    - www.ekhane.bd or ekhane.bd -> Main landing page
    - shop1.ekhane.bd -> Shop1's storefront
    - shop2.ekhane.bd -> Shop2's storefront
    - dashboard routes always go to store owner dashboard
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Paths that should always go to main site (not store)
        self.main_site_paths = [
            '/registration/',
            '/login/',
            '/logout/',
            '/verify-otp/',
            '/resend-otp/',
            '/validate/',
            '/admin/',
            '/dashboard/',  # Dashboard is separate from storefront
        ]

    def __call__(self, request):
        # Get the full host (e.g., shop1.ekhane.bd or www.ekhane.bd)
        host = request.get_host().split(':')[0]  # Remove port if present

        # Get current path
        path = request.path

        # Check if this is a main site path (login, registration, admin, dashboard)
        is_main_site_path = any(path.startswith(main_path) for main_path in self.main_site_paths)

        if is_main_site_path:
            # Main site paths - don't process subdomain
            request.store = None
            request.is_storefront = False
        else:
            # Check for subdomain
            parts = host.split('.')

            # Determine if this is a subdomain request
            # Examples:
            #   shop1.ekhane.bd -> subdomain = shop1
            #   localhost -> no subdomain
            #   www.ekhane.bd -> no subdomain (www is ignored)
            #   ekhane.bd -> no subdomain

            if len(parts) >= 3:  # Has subdomain
                subdomain = parts[0]

                # Ignore 'www' subdomain
                if subdomain.lower() == 'www':
                    request.store = None
                    request.is_storefront = False
                else:
                    # This is a store subdomain - load the store
                    try:
                        store = Store.objects.select_related('owner').get(
                            subdomain=subdomain,
                            status='active'
                        )
                        request.store = store
                        request.is_storefront = True
                    except Store.DoesNotExist:
                        # Subdomain doesn't exist or store is not active
                        request.store = None
                        request.is_storefront = False

                        # Return a 404 page for invalid store
                        return render(request, 'errors/store_not_found.html', status=404)
            else:
                # No subdomain (main site)
                request.store = None
                request.is_storefront = False

        response = self.get_response(request)
        return response


class StoreAccessMiddleware:
    """
    Middleware to ensure users can only access their own store's dashboard.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only check for dashboard routes
        if request.path.startswith('/dashboard/') and request.user.is_authenticated:
            # Check if user has a store
            if not hasattr(request.user, 'store'):
                from django.contrib import messages
                messages.error(request, "You don't have a store yet.")
                return redirect('/registration/')

        response = self.get_response(request)
        return response
