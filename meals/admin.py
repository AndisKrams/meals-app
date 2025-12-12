from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import Count
from django.urls import path
from django.template.response import TemplateResponse
from datetime import datetime
from .models import Meal, MealRegistration, MealChoice, Parent, Child


class MealsAdminSite(AdminSite):
    site_header = 'School Meals Administration'
    site_title = 'Meals Admin'
    index_title = 'Welcome to School Meals Admin'

    def get_urls(self):
        from django.urls import path
        from django.contrib.auth import views as auth_views
        urls = super().get_urls()
        # Override the logout URL to redirect to admin login
        custom_urls = [
            path('logout/', auth_views.LogoutView.as_view(next_page='/admin/login/'), name='logout'),
        ]
        # Put custom URL before default ones so it takes precedence
        return custom_urls + urls


# Create the custom admin site instance
admin_site = MealsAdminSite(name='admin')


class MealAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


class MealRegistrationAdmin(admin.ModelAdmin):
    list_display = ('date',)
    filter_horizontal = ('meals',)


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


class ParentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user')
    search_fields = ('full_name', 'user__username')


class ChildAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'year_group', 'parent')
    list_filter = ('year_group',)
    search_fields = ('first_name', 'last_name', 'parent__full_name')


# Register models with the custom admin site
admin_site.register(Meal, MealAdmin)
admin_site.register(MealRegistration, MealRegistrationAdmin)
admin_site.register(MealChoice, MealChoiceAdmin)
admin_site.register(Parent, ParentAdmin)
admin_site.register(Child, ChildAdmin)
