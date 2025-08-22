from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_parent, name='register_parent'),
    path('login/', views.user_login, name='login'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
]
