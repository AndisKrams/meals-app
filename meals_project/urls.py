"""
URL configuration for meals_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from meals import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path('register/', views.register_parent, name='register_parent'),
    path('history/', views.meal_choice_history, name='meal_choice_history'),
    path(
        'edit-choice/<int:choice_id>/',
        views.edit_meal_choice,
        name='edit_meal_choice'
    ),
    path(
        'delete-choice/<int:choice_id>/',
        views.delete_meal_choice,
        name='delete_meal_choice'
    ),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='meals/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='meals/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='meals/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='meals/password_reset_complete.html'), name='password_reset_complete'),
    path('meals/', include('meals.urls')),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
