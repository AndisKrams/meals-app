from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth import login, logout
from django.utils import timezone
from .forms import UserParentRegistrationForm, MealChoiceForm, ChildRegistrationForm
from .models import Parent, MealRegistration, MealChoice
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from datetime import datetime
import logging

logger = logging.getLogger("meals")


def home(request):
    """Landing page - simple view with no redirects"""
    if request.user.is_authenticated:
        return redirect("meal_ordering")
    # For unauthenticated users, show a simple welcome page
    return render(request, "meals/welcome.html")


def validate_date_string(date_str):
    """Validate and parse date string in YYYY-MM-DD format"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid date format: {date_str} - {str(e)}")
        return None


def register_parent(request):
    if request.method == "POST":
        form = UserParentRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(
                    request, "Registration successful! You can now log in."
                )
                logger.info(f"New parent registered: {user.username}")
                return redirect("login")
            except IntegrityError as e:
                logger.error(f"Database error during registration: {str(e)}")
                messages.error(
                    request,
                    "Registration failed due to a database error. Please try again.",
                )
            except Exception as e:
                logger.error(f"Unexpected error during registration: {str(e)}")
                messages.error(
                    request, "An unexpected error occurred. Please try again."
                )
        else:
            messages.error(request, "Please correct the errors below.")
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
                email_template_name="meals/password_reset_email.html",
                subject_template_name="meals/password_reset_subject.txt",
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
        user=user, defaults={"full_name": user.get_full_name() or user.username}
    )
    return parent


@login_required
def child_list(request):
    parent = get_or_create_parent(request.user)
    children = parent.children.all().order_by("year_group", "last_name")
    return render(request, "meals/child_list.html", {"children": children})


@login_required
@transaction.atomic
def add_child(request):
    parent = get_or_create_parent(request.user)
    if request.method == "POST":
        form = ChildRegistrationForm(request.POST)
        if form.is_valid():
            try:
                child = form.save(commit=False)
                child.parent = parent
                child.full_clean()  # Run model validation
                child.save()
                messages.success(
                    request,
                    f"Child {child.first_name} {child.last_name} added successfully.",
                )
                logger.info(f"Child added: {child.id} for parent: {parent.id}")
                return redirect("child_list")
            except ValidationError as e:
                logger.warning(f"Validation error adding child: {str(e)}")
                messages.error(request, f"Validation error: {str(e)}")
            except IntegrityError as e:
                logger.error(f"Database error adding child: {str(e)}")
                messages.error(request, "A database error occurred. Please try again.")
            except Exception as e:
                logger.error(f"Unexpected error adding child: {str(e)}")
                messages.error(
                    request, "An unexpected error occurred. Please try again."
                )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ChildRegistrationForm()
    return render(request, "meals/add_child.html", {"form": form})


@login_required
@transaction.atomic
def edit_child(request, child_id):
    parent = get_or_create_parent(request.user)
    child = get_object_or_404(parent.children, id=child_id)
    if request.method == "POST":
        form = ChildRegistrationForm(request.POST, instance=child)
        if form.is_valid():
            try:
                updated_child = form.save(commit=False)
                updated_child.full_clean()
                updated_child.save()
                messages.success(
                    request,
                    f"Child {updated_child.first_name} {updated_child.last_name} updated successfully.",
                )
                logger.info(f"Child updated: {child.id}")
                return redirect("child_list")
            except ValidationError as e:
                logger.warning(f"Validation error updating child: {str(e)}")
                messages.error(request, f"Validation error: {str(e)}")
            except IntegrityError as e:
                logger.error(f"Database error updating child: {str(e)}")
                messages.error(request, "A database error occurred. Please try again.")
            except Exception as e:
                logger.error(f"Unexpected error updating child: {str(e)}")
                messages.error(
                    request, "An unexpected error occurred. Please try again."
                )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ChildRegistrationForm(instance=child)
    return render(request, "meals/edit_child.html", {"form": form, "child": child})


@login_required
@transaction.atomic
def delete_child(request, child_id):
    parent = get_or_create_parent(request.user)
    child = get_object_or_404(parent.children, id=child_id)
    if request.method == "POST":
        try:
            child_name = f"{child.first_name} {child.last_name}"
            child.delete()
            messages.success(request, f"{child_name} has been deleted successfully.")
            logger.info(f"Child deleted: {child_id} by parent {parent.id}")
            return redirect("child_list")
        except Exception as e:
            logger.error(f"Error deleting child {child_id}: {str(e)}")
            messages.error(
                request, "An error occurred while deleting the child. Please try again."
            )
    return render(request, "meals/confirm_delete_child.html", {"child": child})


@login_required
def meal_ordering(request):
    parent = get_or_create_parent(request.user)
    children = parent.children.all()
    if not children.exists():
        messages.info(
            request, "You have no registered children. Please add a child first."
        )
        return redirect("add_child")

    try:
        available_dates = MealRegistration.objects.order_by("date").values_list(
            "date", flat=True
        )
        selected_date_str = request.GET.get("date")
        selected_date = None

        if selected_date_str:
            selected_date = validate_date_string(selected_date_str)
            if not selected_date:
                messages.warning(
                    request, "Invalid date format. Showing next available date."
                )

        if not selected_date:
            # Find first available date without choices for any child
            for date in available_dates:
                if not MealChoice.objects.filter(
                    child__in=children, meal_registration__date=date
                ).exists():
                    selected_date = date
                    break
            if not selected_date and available_dates:
                selected_date = available_dates[0]

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
            try:
                with transaction.atomic():
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
                        logger.info(f"Meal choices saved for parent {parent.id}")
                        # Find the next available date without choices for any child
                        next_date = None
                        for date in available_dates:
                            if not MealChoice.objects.filter(
                                child__in=children, meal_registration__date=date
                            ).exists():
                                next_date = date
                                break
                        if next_date:
                            return redirect(f"{request.path}?date={next_date}")
                        else:
                            return redirect("meal_ordering")
            except IntegrityError as e:
                logger.error(f"Database error saving meal choices: {str(e)}")
                messages.error(request, "A database error occurred. Please try again.")
            except Exception as e:
                logger.error(f"Unexpected error saving meal choices: {str(e)}")
                messages.error(
                    request, "An unexpected error occurred. Please try again."
                )
    except Exception as e:
        logger.error(f"Error in meal_ordering view: {str(e)}")
        messages.error(
            request, "An error occurred loading meal options. Please try again."
        )
        return redirect("child_list")
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


@login_required
def meal_choice_history(request):
    try:
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
    except Exception as e:
        logger.error(f"Error loading meal choice history: {str(e)}")
        messages.error(request, "An error occurred loading your meal history.")
        return redirect("meal_ordering")


@login_required
@transaction.atomic
def edit_meal_choice(request, choice_id):
    try:
        choice = get_object_or_404(
            MealChoice, id=choice_id, child__parent__user=request.user
        )
        meal_registration = choice.meal_registration

        # Check if the meal date hasn't passed
        if meal_registration.date < timezone.now().date():
            messages.error(request, "Cannot edit past meal choices.")
            return redirect("meal_choice_history")

        if request.method == "POST":
            form = MealChoiceForm(
                request.POST,
                meal_registration=meal_registration,
                prefix=str(choice.child.id),
            )
            if form.is_valid():
                try:
                    choice.meal = form.cleaned_data["meal"]
                    choice.save()
                    messages.success(request, "Meal choice updated successfully.")
                    logger.info(f"Meal choice {choice_id} updated")
                    return redirect("meal_choice_history")
                except Exception as e:
                    logger.error(f"Error updating meal choice: {str(e)}")
                    messages.error(
                        request, "An error occurred updating the meal choice."
                    )
            else:
                messages.error(request, "Please correct the errors below.")
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
    except Exception as e:
        logger.error(f"Error in edit_meal_choice: {str(e)}")
        messages.error(request, "An error occurred. Please try again.")
        return redirect("meal_choice_history")


@login_required
@transaction.atomic
def delete_meal_choice(request, choice_id):
    try:
        choice = get_object_or_404(
            MealChoice, id=choice_id, child__parent__user=request.user
        )
        if choice.meal_registration.date > timezone.now().date():
            choice.delete()
            messages.success(request, "Meal choice deleted successfully.")
            logger.info(f"Meal choice {choice_id} deleted")
        else:
            messages.error(request, "Cannot delete past meal choices.")
    except Exception as e:
        logger.error(f"Error deleting meal choice: {str(e)}")
        messages.error(request, "An error occurred while deleting the meal choice.")
    return redirect("meal_choice_history")


def admin_meal_orders(request):
    try:
        dates = MealRegistration.objects.order_by("date").values_list("date", flat=True)
        selected_date_str = request.GET.get("date")
        selected_date = None

        if selected_date_str:
            selected_date = validate_date_string(selected_date_str)
            if not selected_date:
                messages.warning(
                    request, "Invalid date format. Showing first available date."
                )

        if not selected_date and dates:
            selected_date = dates[0]

        meal_registration = (
            MealRegistration.objects.filter(date=selected_date).first()
            if selected_date
            else None
        )

        choices = []
        totals = {}
        totals_items = []
        if meal_registration:
            meal_choices = (
                MealChoice.objects.filter(meal_registration=meal_registration)
                .select_related("child", "meal")
                .order_by("child__year_group", "child__last_name")
            )
            choices = list(meal_choices)
            from collections import Counter

            totals = Counter(choice.meal.name for choice in choices)
            # Provide a safe iterable to templates to avoid key collisions like 'items'
            totals_items = list(totals.items())
    except Exception as e:
        logger.error(f"Error in admin_meal_orders: {str(e)}")
        messages.error(request, "An error occurred loading meal orders.")
        dates = []
        selected_date = None
        choices = []
        totals = {}
        totals_items = []
        meal_registration = None

    return render(
        request,
        "meals/admin_meal_orders.html",
        {
            "dates": dates,
            "selected_date": selected_date,
            "choices": choices,
            "totals": totals,
            "totals_items": totals_items,
            "meal_registration": meal_registration,
        },
    )


def user_logout(request):
    """
    Log out the current user and redirect to the login page with a message.
    Staff users are redirected to the admin login page.
    """
    is_staff = request.user.is_staff
    logout(request)
    messages.info(request, "You have been signed out.")
    if is_staff:
        return redirect("admin:login")
    return redirect("login")


@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        username = user.username
        try:
            logout(request)
            user.delete()
            logger.info(f"Account deleted for user: {username}")
        except Exception as e:
            logger.error(f"Error deleting account for {username}: {str(e)}")
            messages.error(
                request,
                "An error occurred while deleting your account. Please contact support.",
            )
            return redirect("meal_ordering")
        return render(
            request,
            "meals/account_deleted.html",
            {"username": username},
        )
    return render(request, "meals/confirm_delete_account.html")


# Custom error handlers
def custom_404(request, exception):
    """Custom 404 error handler"""
    logger.warning(f"404 error: {request.path}")
    return render(request, "404.html", status=404)


def custom_500(request):
    """Custom 500 error handler"""
    logger.error(f"500 error on path: {request.path}")
    return render(request, "500.html", status=500)


def custom_403(request, exception):
    """Custom 403 error handler"""
    logger.warning(f"403 error: {request.path}")
    return render(request, "403.html", status=403)
