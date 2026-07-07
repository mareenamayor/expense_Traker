from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime
from config.db_connection import db
from .forms import RegisterForm, LoginForm
from .decorators import user_login_required

def register_view(request):
    # Handle user signup
    if 'user_id' in request.session:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Securely hash password
            hashed_password = make_password(password)

            # Create user document
            user_document = {
                'username': username,
                'email': email,
                'password_hash': hashed_password,
                'created_at': datetime.utcnow()
            }

            # Insert into database
            db.users.insert_one(user_document)

            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    # Handle user login
    if 'user_id' in request.session:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Find user in database
            user = db.users.find_one({'email': email})

            # Verify password and set up session
            if user and check_password(password, user['password_hash']):
                request.session['user_id'] = str(user['_id'])
                request.session['username'] = user['username']

                messages.success(request, f"Welcome back, {user['username']}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    # Clear session and redirect to login page
    request.session.flush()
    messages.info(request, "You have been successfully logged out.")
    return redirect('login')
