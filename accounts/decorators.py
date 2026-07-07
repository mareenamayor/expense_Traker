from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def user_login_required(view_func):
    # Check if user is logged in, redirect if not
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'user_id' not in request.session:
            messages.warning(request, "Please log in to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
