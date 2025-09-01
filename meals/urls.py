from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),  # Show login page at /meals/
    path('register/', views.register_parent, name='register_parent'),
    path('login/', views.user_login, name='login'),
    path('order/', views.meal_ordering, name='meal_ordering'),
    path('add-child/', views.add_child, name='add_child'),
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
]
