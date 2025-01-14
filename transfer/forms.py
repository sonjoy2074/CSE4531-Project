from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class SignUpForm(UserCreationForm):
    full_name = forms.CharField(max_length=150)

    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'password1', 'password2']


class ImageUploadForm(forms.Form):
    image = forms.ImageField()
    receiver = forms.CharField(max_length=150)
