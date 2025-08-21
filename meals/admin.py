

from django.contrib import admin
from .models import Meal, MealRegistration


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
	list_display = ('name', 'description')


@admin.register(MealRegistration)
class MealRegistrationAdmin(admin.ModelAdmin):
    list_display = ('date',)
    filter_horizontal = ('meals',)
