from django import forms
from django.contrib.auth.models import User
from .models import Parent, Child

class UserParentRegistrationForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'full_name']

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
