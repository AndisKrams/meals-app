from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .forms import UserParentRegistrationForm, MealChoiceForm
from .models import Parent, Child, MealRegistration, MealChoice

# Create your views here.


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
            return redirect('meal_ordering')  # Redirect to meal ordering page
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


def meal_ordering(request):
    if not request.user.is_authenticated:
        return redirect('login')
    parent = get_object_or_404(Parent, user=request.user)
    children = parent.children.all()
    # Find all dates with meal registrations
    available_dates = MealRegistration.objects.order_by('date').values_list('date', flat=True)
    # Find first available date for which no child has chosen a meal
    chosen_dates = MealChoice.objects.filter(child__in=children).values_list('meal_registration__date', flat=True)
    default_date = None
    for date in available_dates:
        if date not in chosen_dates:
            default_date = date
            break
    if not default_date and available_dates:
        default_date = available_dates[0]
    # Allow user to pick date
    selected_date = request.GET.get('date')
    if selected_date:
        selected_date = timezone.datetime.strptime(selected_date, '%Y-%m-%d').date()
    else:
        selected_date = default_date
    meal_registration = MealRegistration.objects.filter(date=selected_date).first()
    forms = []
    if request.method == 'POST' and meal_registration:
        for child in children:
            form = MealChoiceForm(request.POST, prefix=str(child.id), meal_registration=meal_registration)
            if form.is_valid():
                MealChoice.objects.update_or_create(
                    child=child,
                    meal_registration=meal_registration,
                    defaults={'meal': form.cleaned_data['meal']}
                )
            forms.append(form)
        messages.success(request, f'Meal choices saved for {selected_date}.')
        return redirect('meal_ordering')
    else:
        for child in children:
            initial = {}
            existing_choice = MealChoice.objects.filter(child=child, meal_registration=meal_registration).first()
            if existing_choice:
                initial['meal'] = existing_choice.meal
            form = MealChoiceForm(prefix=str(child.id), initial=initial, meal_registration=meal_registration)
            forms.append((child, form))
    return render(request, 'meals/meal_ordering.html', {
        'forms': forms,
        'meal_registration': meal_registration,
        'selected_date': selected_date,
        'available_dates': available_dates,
        'children': children,
    })


def meal_choice_history(request):
    if not request.user.is_authenticated:
        return redirect('login')
    parent = get_object_or_404(Parent, user=request.user)
    children = parent.children.all()
    choices = (
        MealChoice.objects
        .filter(child__in=children)
        .select_related('meal_registration', 'meal', 'child')
        .order_by('-meal_registration__date')
    )
    today = timezone.now().date()
    return render(request, 'meals/meal_choice_history.html', {
        'choices': choices,
        'today': today,
    })


def edit_meal_choice(request, choice_id):
    if not request.user.is_authenticated:
        return redirect('login')
    choice = get_object_or_404(MealChoice, id=choice_id, child__parent__user=request.user)
    meal_registration = choice.meal_registration
    if request.method == 'POST':
        form = MealChoiceForm(request.POST, meal_registration=meal_registration, prefix=str(choice.child.id))
        if form.is_valid():
            choice.meal = form.cleaned_data['meal']
            choice.save()
            messages.success(request, 'Meal choice updated.')
            return redirect('meal_choice_history')
    else:
        form = MealChoiceForm(
            initial={'meal': choice.meal},
            meal_registration=meal_registration,
            prefix=str(choice.child.id)
        )
    return render(request, 'meals/edit_meal_choice.html', {
        'form': form,
        'choice': choice,
        'meal_registration': meal_registration,
    })


def delete_meal_choice(request, choice_id):
    if not request.user.is_authenticated:
        return redirect('login')
    choice = get_object_or_404(MealChoice, id=choice_id, child__parent__user=request.user)
    if choice.meal_registration.date > timezone.now().date():
        choice.delete()
        messages.success(request, 'Meal choice deleted.')
    else:
        messages.error(request, 'Cannot delete past meal choices.')
    return redirect('meal_choice_history')
