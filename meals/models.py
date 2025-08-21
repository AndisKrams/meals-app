from django.db import models
from django.contrib.auth.models import User


class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150)

    def __str__(self):
        return self.full_name


class Child(models.Model):
    parent = models.ForeignKey(
        Parent,
        on_delete=models.CASCADE,
        related_name='children'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    year_group = models.IntegerField()
    class_name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.class_name})"


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

