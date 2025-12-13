from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Parent, Child, MealChoice, Meal, MealRegistration


class UserParentRegistrationForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=150,
        help_text="Enter your full name",
        error_messages={
            'required': 'Full name is required.',
            'max_length': 'Full name cannot exceed 150 characters.'
        }
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Password must be at least 8 characters",
        min_length=8,
        error_messages={
            'required': 'Password is required.',
            'min_length': 'Password must be at least 8 characters long.'
        }
    )
    password2 = forms.CharField(
        label='Repeat password',
        widget=forms.PasswordInput,
        help_text="Enter the same password for verification",
        error_messages={'required': 'Please confirm your password.'}
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'autofocus': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
        }
        help_texts = {
            'username': 'Required. Letters, digits and @/./+/-/_ only.',
            'email': 'Required. Enter a valid email address.'
        }
        error_messages = {
            'username': {
                'required': 'Username is required.',
                'unique': 'This username is already taken.',
            },
            'email': {
                'required': 'Email address is required.',
                'invalid': 'Please enter a valid email address.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['full_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        # Make email required
        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered.')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        if password and password2:
            if password != password2:
                raise ValidationError({
                    'password2': 'The two password fields must match.'
                })
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
        fields = ['first_name', 'last_name', 'year_group']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'autofocus': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'year_group': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '13'}),
        }
        help_texts = {
            'first_name': 'Child\'s first name',
            'last_name': 'Child\'s last name',
            'year_group': 'Enter a year group between 0 and 13'
        }
        error_messages = {
            'first_name': {
                'required': 'First name is required.',
                'max_length': 'First name cannot exceed 30 characters.'
            },
            'last_name': {
                'required': 'Last name is required.',
                'max_length': 'Last name cannot exceed 30 characters.'
            },
            'year_group': {
                'required': 'Year group is required.',
                'invalid': 'Please enter a valid number.'
            },
        }

    def clean_year_group(self):
        year_group = self.cleaned_data.get('year_group')
        if year_group is not None:
            if year_group < 0 or year_group > 13:
                raise ValidationError('Year group must be between 0 and 13.')
        return year_group


class MealChoiceForm(forms.ModelForm):
    class Meta:
        model = MealChoice
        fields = ['meal']
        widgets = {
            'meal': forms.RadioSelect(attrs={'autofocus': True})
        }

    def __init__(self, *args, **kwargs):
        meal_registration = kwargs.pop('meal_registration', None)
        super().__init__(*args, **kwargs)
        if meal_registration:
            self.fields['meal'].queryset = meal_registration.meals.all()
