from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Parent, Child, Meal, MealRegistration, MealChoice


class MealAppFlowsTest(TestCase):
    def setUp(self):
        # user / parent
        self.user = User.objects.create_user(username='parent1', password='pass1234')
        self.parent = Parent.objects.create(user=self.user, full_name='Parent One')

        # children
        self.child1 = Child.objects.create(parent=self.parent, first_name='Alice', last_name='Smith', year_group=3)
        self.child2 = Child.objects.create(parent=self.parent, first_name='Bob', last_name='Jones', year_group=4)

        # meals
        self.meal_a = Meal.objects.create(name='Meal A', description='A')
        self.meal_b = Meal.objects.create(name='Meal B', description='B')

        # two consecutive dates with meal registrations
        today = timezone.now().date()
        self.date1 = today + timedelta(days=1)
        self.date2 = today + timedelta(days=2)

        self.reg1 = MealRegistration.objects.create(date=self.date1)
        self.reg1.meals.add(self.meal_a, self.meal_b)

        self.reg2 = MealRegistration.objects.create(date=self.date2)
        self.reg2.meals.add(self.meal_a, self.meal_b)

        # url names
        self.order_url = reverse('meal_ordering')
        self.add_child_url = reverse('add_child')
        self.history_url = reverse('meal_choice_history')

    def test_login_redirects_to_ordering(self):
        login = self.client.login(username='parent1', password='pass1234')
        self.assertTrue(login)
        resp = self.client.get(self.order_url)
        self.assertEqual(resp.status_code, 200)
        # page includes the first available date in Y-m-d format
        self.assertContains(resp, self.date1.strftime('%Y-%m-%d'))

    def test_add_child_creates_record(self):
        self.client.login(username='parent1', password='pass1234')
        resp = self.client.post(self.add_child_url, {
            'first_name': 'Charlie',
            'last_name': 'Brown',
            'year_group': 2
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Child.objects.filter(first_name='Charlie', last_name='Brown', parent=self.parent).exists())

    def test_meal_ordering_post_creates_choices_and_redirects_to_next_date(self):
        self.client.login(username='parent1', password='pass1234')

        # Submit choices for reg1 (first available). Use form prefixes equal to child.id
        post_data = {
            f'{self.child1.id}-meal': str(self.meal_a.id),
            f'{self.child2.id}-meal': str(self.meal_b.id),
        }
        resp = self.client.post(f"{self.order_url}?date={self.date1.strftime('%Y-%m-%d')}", post_data)
        # after successful post, view should redirect (302) to next available date
        self.assertIn(resp.status_code, (302, 303))
        redirect_location = resp['Location']
        self.assertIn('date=', redirect_location)
        # ensure MealChoice objects were created for date1
        self.assertTrue(MealChoice.objects.filter(child=self.child1, meal_registration__date=self.date1, meal=self.meal_a).exists())
        self.assertTrue(MealChoice.objects.filter(child=self.child2, meal_registration__date=self.date1, meal=self.meal_b).exists())

    def test_history_shows_created_choices(self):
        # create a choice directly then view history
        MealChoice.objects.create(child=self.child1, meal_registration=self.reg1, meal=self.meal_a)
        self.client.login(username='parent1', password='pass1234')
        resp = self.client.get(self.history_url)
        self.assertEqual(resp.status_code, 200)
        # history page should show child name and meal
        self.assertContains(resp, 'Alice')
        self.assertContains(resp, 'Meal A')

    def test_delete_account_removes_user_and_related_data(self):
        MealChoice.objects.create(child=self.child1, meal_registration=self.reg1, meal=self.meal_a)
        self.client.login(username='parent1', password='pass1234')

        resp = self.client.post(reverse('delete_account'), follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        self.assertFalse(Parent.objects.filter(pk=self.parent.pk).exists())
        self.assertFalse(Child.objects.filter(parent=self.parent).exists())
        self.assertFalse(MealChoice.objects.filter(child=self.child1).exists())

        redirect_resp = self.client.get(self.order_url)
        self.assertEqual(redirect_resp.status_code, 302)
        self.assertIn(reverse('login'), redirect_resp.url)
