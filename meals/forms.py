from django import forms
from django.contrib.auth.models import User
from .models import Parent, Child, MealChoice, MealRegistration, Meal


class UserParentRegistrationForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'password', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        if password and password2 and password != password2:
            self.add_error('password2', 'Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            Parent.objects.create(user=user, full_name=self.cleaned_data['full_name'])
        return user


class ChildRegistrationForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['first_name', 'last_name', 'year_group', 'class_name']


class MealChoiceForm(forms.ModelForm):
    class Meta:
        model = MealChoice
        fields = ['meal']
        widgets = {
            'meal': forms.RadioSelect
        }

    def __init__(self, *args, **kwargs):
        meal_registration = kwargs.pop('meal_registration', None)
        super().__init__(*args, **kwargs)
        if meal_registration:
            self.fields['meal'].queryset = meal_registration.meals.all()
