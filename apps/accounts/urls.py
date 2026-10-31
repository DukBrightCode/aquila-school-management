from django.shortcuts import render
from django.urls import path
from .views import CustomLoginView, custom_logout_view, RoleBasedRedirectView

app_name = "accounts"

def placeholder_dashboard(request, role):
    return render(request, "base.html", {})

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", custom_logout_view, name="logout"),
    path("redirect/", RoleBasedRedirectView.as_view(), name="redirect"),
    # Temporary placeholder route until Stage 10 dashboard app is connected
    path("dashboard/placeholder/<str:role>/", placeholder_dashboard, name="placeholder_dashboard"),
]