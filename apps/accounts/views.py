from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import RedirectView

from .forms import StyledLoginForm


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = StyledLoginForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Ensures successful login routes through the role-based redirect view."""
        return reverse_lazy("accounts:redirect")


def custom_logout_view(request):
    """
    Handles logging out the user via both GET and POST requests,
    redirecting back to the home page.
    """
    logout(request)
    return redirect("core:home")


class RoleBasedRedirectView(RedirectView):
    """
    Redirects authenticated users to the dashboard router,
    which delegates them to their respective role-specific dashboards.
    """
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        if not user.is_authenticated:
            return reverse_lazy("accounts:login")
        
        # Delegate to the dashboard app's central redirect router
        return reverse_lazy("dashboard:redirect")