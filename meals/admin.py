

from django.contrib import admin
from django.db.models import Count
from django.urls import path
from django.template.response import TemplateResponse
from datetime import datetime
from .models import Meal, MealRegistration, MealChoice


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(MealRegistration)
class MealRegistrationAdmin(admin.ModelAdmin):
    list_display = ('date',)
    filter_horizontal = ('meals',)


@admin.register(MealChoice)
class MealChoiceAdmin(admin.ModelAdmin):
    list_display = ('child', 'meal', 'meal_registration')
    list_filter = ('child__year_group', 'meal', 'meal_registration__date')
    search_fields = ('child__first_name', 'child__last_name')

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('meals-for-day/', self.admin_site.admin_view(self.meals_for_day), name='meals-for-day'),
        ]
        return my_urls + urls

    def meals_for_day(self, request):
        # Get the available dates that have meal choices
        available_dates = MealChoice.objects.order_by('meal_registration__date').values_list('meal_registration__date', flat=True).distinct()

        date_str = request.GET.get('date')
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                date = None
        else:
            date = available_dates.first() if available_dates else None

        if date:
            meal_registrations = MealRegistration.objects.filter(date=date)
            meals = MealChoice.objects.filter(meal_registration__in=meal_registrations).order_by('child__year_group', 'child__last_name')
            meal_totals = meals.values('meal__name').annotate(total=Count('id')).order_by('-total')
        else:
            meals = []
            meal_totals = []

        context = {
            'title': f'Meals for {date}' if date else 'Meals for Day',
            'meals': meals,
            'meal_totals': meal_totals,
            'date': date,
            'available_dates': available_dates,
        }

        return TemplateResponse(request, 'admin/meals_for_day.html', context)
