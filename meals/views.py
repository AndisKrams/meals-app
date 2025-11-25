from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth import login, logout
from django.utils import timezone
from .forms import UserParentRegistrationForm, MealChoiceForm, ChildRegistrationForm
from .models import Parent, MealRegistration, MealChoice
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.admin.views.decorators import staff_member_required

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
            # Django's built-in password reset will handle sending email and link
            form.save(
                request=request,
                email_template_name='meals/password_reset_email.html',
                subject_template_name='meals/password_reset_subject.txt',
            )
            messages.success(
                request, "Password reset instructions have been sent to your email."
            )
            return redirect("login")
    else:
        form = PasswordResetForm()
    return render(request, "meals/password_reset.html", {"form": form})


def get_or_create_parent(user):
    parent, created = Parent.objects.get_or_create(
        user=user,
        defaults={'full_name': user.get_full_name() or user.username}
    )
    return parent

@login_required
def child_list(request):
    parent = get_or_create_parent(request.user)
    children = parent.children.all().order_by('year_group', 'last_name')
    return render(request, 'meals/child_list.html', {'children': children})

@login_required
def add_child(request):
    parent = get_or_create_parent(request.user)
    if request.method == 'POST':
        form = ChildRegistrationForm(request.POST)
        if form.is_valid():
            try:
                child = form.save(commit=False)
                child.parent = parent
                child.save()
                messages.success(request, f"Child {child.first_name} {child.last_name} added.")
                return redirect('child_list')
            except Exception as e:
                messages.error(request, "Could not save child. Please try again.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ChildRegistrationForm()
    return render(request, 'meals/add_child.html', {'form': form})

@login_required
def edit_child(request, child_id):
    parent = get_or_create_parent(request.user)
    child = get_object_or_404(parent.children, id=child_id)
    if request.method == 'POST':
        form = ChildRegistrationForm(request.POST, instance=child)
        if form.is_valid():
            form.save()
            messages.success(request, "Child updated.")
            return redirect('child_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ChildRegistrationForm(instance=child)
    return render(request, 'meals/edit_child.html', {'form': form, 'child': child})

@login_required
def delete_child(request, child_id):
    parent = get_or_create_parent(request.user)
    child = get_object_or_404(parent.children, id=child_id)
    if request.method == 'POST':
        child.delete()
        messages.success(request, "Child deleted.")
        return redirect('child_list')
    return render(request, 'meals/confirm_delete_child.html', {'child': child})


def meal_ordering(request):
    if not request.user.is_authenticated:
        return redirect("login")
    parent = get_or_create_parent(request.user)
    children = parent.children.all()
    if not children.exists():
        messages.info(request, "You have no registered children. Please add a child first.")
        return redirect("add_child")
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
            # Find the next available date without choices for any child
            next_date = None
            for date in available_dates:
                if not MealChoice.objects.filter(child__in=children, meal_registration__date=date).exists():
                    next_date = str(date)
                    break
            if next_date:
                return redirect(f"{request.path}?date={next_date}")
            else:
                return redirect("meal_ordering")
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


def admin_meal_orders(request):
    dates = MealRegistration.objects.order_by('date').values_list('date', flat=True)
    selected_date = request.GET.get('date')
    if not selected_date and dates:
        selected_date = str(dates[0])
    meal_registration = MealRegistration.objects.filter(date=selected_date).first() if selected_date else None

    choices = []
    totals = {}
    if meal_registration:
        meal_choices = (
            MealChoice.objects
            .filter(meal_registration=meal_registration)
            .select_related('child', 'meal')
            .order_by('child__year_group', 'child__last_name')
        )
        choices = list(meal_choices)
        from collections import Counter
        totals = Counter(choice.meal.name for choice in choices)

    return render(request, 'meals/admin_meal_orders.html', {
        'dates': dates,
        'selected_date': selected_date,
        'choices': choices,
        'totals': totals,
        'meal_registration': meal_registration,
    })

def user_logout(request):
    """
    Log out the current user and redirect to the login page with a message.
    """
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect('login')
