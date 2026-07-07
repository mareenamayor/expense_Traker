from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime
from config.db_connection import db
from .forms import RegisterForm, LoginForm
from .decorators import user_login_required

def register_view(request):
    """
    Handles user registration.
    If GET, renders the signup page with a clean form.
    If POST, validates form data, hashes the password, inserts a new user document
    into MongoDB 'users' collection, and redirects to login.
    """
    # Redirect logged-in users away from signup page
    if 'user_id' in request.session:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Clean data is returned as standard Python types after validation
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Hash the password securely using Django's default pbkdf2 algorithm
            hashed_password = make_password(password)

            # Construct the MongoDB document
            user_document = {
                'username': username,
                'email': email,
                'password_hash': hashed_password,
                'created_at': datetime.utcnow()
            }

            # Insert into MongoDB 'users' collection
            # Native MongoDB operation: insert_one()
            db.users.insert_one(user_document)

            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    Handles user login.
    If GET, renders the login page.
    If POST, queries MongoDB by email, checks the hashed password,
    creates session cookies, and redirects to dashboard.
    """
    if 'user_id' in request.session:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Query MongoDB 'users' collection for this email
            # Native MongoDB operation: find_one()
            user = db.users.find_one({'email': email})

            # Check if user exists and password is correct
            # check_password compares raw string with securely salted PBKDF2 hash
            if user and check_password(password, user['password_hash']):
                # Set session variables to log the user in
                # We convert ObjectId to string since sessions require serializable JSON data
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
    """
    Logs the user out by clearing their session data and redirects to login.
    """
    # flush() clears the session data and deletes the session cookie from the database
    request.session.flush()
    messages.info(request, "You have been successfully logged out.")
    return redirect('login')


@user_login_required
def temp_dashboard_view(request):
    """
    A temporary dashboard landing page to verify successful login and session storage.
    """
    return render(request, 'accounts/temp_dashboard.html')
