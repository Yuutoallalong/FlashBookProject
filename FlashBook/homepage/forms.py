from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

class RegisterForm(UserCreationForm):
    fname = forms.CharField(max_length=30, required=True, label="First Name")
    lname = forms.CharField(max_length=30, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email")
    birthdate = forms.DateField(
    required=True,
    widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'DD/MM/YYYY'}),
    label="Date of Birth"
    )
    password2 = forms.CharField(
        label="Confirm password", 
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['username', 'fname', 'lname', 'email', 'birthdate', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.fname = self.cleaned_data['fname']
        user.lname = self.cleaned_data['lname']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=255, label="Username")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")