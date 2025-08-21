from django.db import models
from django.contrib.auth.models import User


class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class Child(models.Model):
    parent = models.ForeignKey(
        Parent,
        on_delete=models.CASCADE,
        related_name='children'
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Meal(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class MealRegistration(models.Model):
    date = models.DateField()
    meals = models.ManyToManyField(Meal, related_name='registrations')

    def __str__(self):
        return f"Meal Registration for {self.date}"

