from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.core.mail import send_mail
from django.conf import settings
from .forms import UserParentRegistrationForm

# Create your views here.


def meals(request):
    return HttpResponse("Welcome to the Meals App!")


def register_parent(request):
    if request.method == 'POST':
        form = UserParentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful. You can now log in.')
            return redirect('login')  # Adjust to your login URL name
    else:
        form = UserParentRegistrationForm()
    return render(request, 'meals/register_parent.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('meals')
    else:
        form = AuthenticationForm()
    return render(request, 'meals/login.html', {'form': form})


def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Django's built-in password reset will handle sending email and link
            # This is a placeholder for integration with Django's password reset views
            messages.success(request, 'Password reset instructions have been sent to your email.')
            return redirect('login')
    else:
        form = PasswordResetForm()
    return render(request, 'meals/password_reset.html', {'form': form})
