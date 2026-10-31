from functools import wraps
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(*roles):
    """
    Decorator for views that checks if the user is authenticated and has
    at least one of the specified roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.role in roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator


class BaseRoleRequiredMixin(AccessMixin):
    """
    Base mixin for role-based view permissions.
    """
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role in self.allowed_roles or request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied


class AdminRequiredMixin(BaseRoleRequiredMixin):
    allowed_roles = ("ADMIN",)


class TeacherRequiredMixin(BaseRoleRequiredMixin):
    allowed_roles = ("TEACHER",)


class StudentRequiredMixin(BaseRoleRequiredMixin):
    allowed_roles = ("STUDENT",)