from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
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
