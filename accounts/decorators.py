from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def user_login_required(view_func):
    """
    Decorator for views that checks if a user is logged in via the session dictionary.
    If 'user_id' is not present in the session, redirects to the login page.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'user_id' not in request.session:
            messages.warning(request, "Please log in to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
