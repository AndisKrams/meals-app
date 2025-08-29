from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),  # Show login page at /meals/
    path('register/', views.register_parent, name='register_parent'),
    path('login/', views.user_login, name='login'),
    path('order/', views.meal_ordering, name='meal_ordering'),
]
