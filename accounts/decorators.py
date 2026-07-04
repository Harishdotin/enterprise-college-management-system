from django.shortcuts import redirect
from django.contrib.auth.mixins import AccessMixin
from django.contrib import messages
from functools import wraps

class RoleRequiredMixin(AccessMixin):
    """
    CBV mixin that restricts access to users with specific roles.
    """
    roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if request.user.is_superuser or request.user.role in self.roles:
            return super().dispatch(request, *args, **kwargs)
            
        messages.error(request, "Access denied. You do not have permission to view that resource.")
        return redirect('access_denied')

def role_required(*roles):
    """
    Function-based view decorator that restricts access to specific roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.is_superuser or request.user.role in roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, "Access denied. You do not have permission to view that resource.")
            return redirect('access_denied')
        return _wrapped_view
    return decorator
