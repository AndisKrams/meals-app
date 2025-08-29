from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .forms import UserParentRegistrationForm, MealChoiceForm, ChildRegistrationForm
from .models import Parent, Child, MealRegistration, MealChoice

# Create your views here.


def register_parent(request):
    if request.method == "POST":
        form = UserParentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. You can now log in.")
            return redirect("login")  # Adjust to your login URL name
    else:
        form = UserParentRegistrationForm()
    return render(request, "meals/register_parent.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("meal_ordering")  # Redirect to meal ordering page
    else:
        form = AuthenticationForm()
    return render(request, "meals/login.html", {"form": form})


def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            # Django's built-in password reset will handle sending email and link
            # This is a placeholder for integration with Django's password reset views
            messages.success(
                request, "Password reset instructions have been sent to your email."
            )
            return redirect("login")
    else:
        form = PasswordResetForm()
    return render(request, "meals/password_reset.html", {"form": form})


def meal_ordering(request):
    if not request.user.is_authenticated:
        return redirect("login")
    parent = Parent.objects.get(user=request.user)
    children = parent.children.all()
    available_dates = MealRegistration.objects.order_by("date").values_list(
        "date", flat=True
    )
    selected_date = request.GET.get("date")
    if not selected_date:
        # Find first available date without choices for any child
        for date in available_dates:
            if not MealChoice.objects.filter(
                child__in=children, meal_registration__date=date
            ).exists():
                selected_date = str(date)
                break
        if not selected_date and available_dates:
            selected_date = str(available_dates[0])
    meal_registration = (
        MealRegistration.objects.filter(date=selected_date).first()
        if selected_date
        else None
    )

    forms = []
    if meal_registration:
        for child in children:
            choice = MealChoice.objects.filter(
                child=child, meal_registration=meal_registration
            ).first()
            initial = {"meal": choice.meal} if choice else {}
            forms.append(
                (
                    child,
                    MealChoiceForm(
                        request.POST if request.method == "POST" else None,
                        initial=initial,
                        meal_registration=meal_registration,
                        prefix=str(child.id),
                    ),
                )
            )

    if request.method == "POST" and meal_registration:
        success_messages = []
        all_valid = True
        for child, form in forms:
            if form.is_valid():
                meal = form.cleaned_data["meal"]
                choice, created = MealChoice.objects.get_or_create(
                    child=child,
                    meal_registration=meal_registration,
                    defaults={"meal": meal},
                )
                if not created:
                    choice.meal = meal
                    choice.save()
                success_messages.append(
                    (
                        (
                            f"Meal choice for {child.first_name} {child.last_name} "
                            f"on {meal_registration.date}: {meal.name}"
                        )
                    )
                )
            else:
                all_valid = False
        if all_valid:
            for msg in success_messages:
                messages.success(request, msg)
            return redirect("meal_ordering")  # Redirect to show messages
    return render(
        request,
        "meals/meal_ordering.html",
        {
            "available_dates": available_dates,
            "selected_date": selected_date,
            "meal_registration": meal_registration,
            "forms": forms,
        },
    )


def meal_choice_history(request):
    if not request.user.is_authenticated:
        return redirect("login")
    parent = get_object_or_404(Parent, user=request.user)
    children = parent.children.all()
    choices = (
        MealChoice.objects.filter(child__in=children)
        .select_related("meal_registration", "meal", "child")
        .order_by("-meal_registration__date")
    )
    today = timezone.now().date()
    return render(
        request,
        "meals/meal_choice_history.html",
        {
            "choices": choices,
            "today": today,
        },
    )


def edit_meal_choice(request, choice_id):
    if not request.user.is_authenticated:
        return redirect("login")
    choice = get_object_or_404(
        MealChoice, id=choice_id, child__parent__user=request.user
    )
    meal_registration = choice.meal_registration
    if request.method == "POST":
        form = MealChoiceForm(
            request.POST,
            meal_registration=meal_registration,
            prefix=str(choice.child.id),
        )
        if form.is_valid():
            choice.meal = form.cleaned_data["meal"]
            choice.save()
            messages.success(request, "Meal choice updated.")
            return redirect("meal_choice_history")
    else:
        form = MealChoiceForm(
            initial={"meal": choice.meal},
            meal_registration=meal_registration,
            prefix=str(choice.child.id),
        )
    return render(
        request,
        "meals/edit_meal_choice.html",
        {
            "form": form,
            "choice": choice,
            "meal_registration": meal_registration,
        },
    )


def delete_meal_choice(request, choice_id):
    if not request.user.is_authenticated:
        return redirect("login")
    choice = get_object_or_404(
        MealChoice, id=choice_id, child__parent__user=request.user
    )
    if choice.meal_registration.date > timezone.now().date():
        choice.delete()
        messages.success(request, "Meal choice deleted.")
    else:
        messages.error(request, "Cannot delete past meal choices.")
    return redirect("meal_choice_history")


def add_child(request):
    if not request.user.is_authenticated:
        return redirect("login")
    parent = Parent.objects.get(user=request.user)
    if request.method == "POST":
        form = ChildRegistrationForm(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.parent = parent
            child.save()
            messages.success(request, "Child added successfully.")
            return redirect("meal_ordering")
    else:
        form = ChildRegistrationForm()
    return render(request, "meals/add_child.html", {"form": form})
