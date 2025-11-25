from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('register/', views.register_parent, name='register_parent'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('order/', views.meal_ordering, name='meal_ordering'),
    path('add-child/', views.add_child, name='add_child'),
    path('children/', views.child_list, name='child_list'),  # List children
    path('children/<int:child_id>/edit/', views.edit_child, name='edit_child'),  # UPDATE
    path('children/<int:child_id>/delete/', views.delete_child, name='delete_child'),  # DELETE
    path('history/', views.meal_choice_history, name='meal_choice_history'),
    path('edit-choice/<int:choice_id>/', views.edit_meal_choice, name='edit_meal_choice'),
    path('delete-choice/<int:choice_id>/', views.delete_meal_choice, name='delete_meal_choice'),
    path('admin-meal-orders/', views.admin_meal_orders, name='admin_meal_orders'),
]
