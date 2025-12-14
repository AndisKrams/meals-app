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
    site_url = '/meals/'

    def get_urls(self):
        from django.urls import path
        from django.contrib.auth import views as auth_views
        urls = super().get_urls()
        # Override the logout URL to redirect to admin login
        custom_urls = [
            path('logout/', auth_views.LogoutView.as_view(next_page='/admin/login/'), name='logout'),
            path('meals-for-day/', self.admin_view(self.meals_for_day_view), name='meals-for-day'),
        ]
        # Put custom URL before default ones so it takes precedence
        return custom_urls + urls

    def meals_for_day_view(self, request):
        """View for displaying meal orders by date"""
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
            'site_title': self.site_title,
            'site_header': self.site_header,
            'has_permission': True,
        }

        return TemplateResponse(request, 'admin/meals_for_day.html', context)

    def index(self, request, extra_context=None):
        """Override admin index to add custom links"""
        extra_context = extra_context or {}
        extra_context['custom_links'] = [
            {
                'title': 'View Meal Orders by Date',
                'url': '/admin/meals-for-day/',
                'description': 'See all meal orders organized by date'
            }
        ]
        return super().index(request, extra_context)


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
