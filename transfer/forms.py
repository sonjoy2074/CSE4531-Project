from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
class SignUpForm(UserCreationForm):
    full_name = forms.CharField(max_length=150)
    user_type = forms.ChoiceField(choices=Profile.USER_TYPE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'password1', 'password2', 'user_type']


class ImageUploadForm(forms.Form):
    image = forms.ImageField()
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.profile.user_type == 'patient':
            self.fields['receiver'] = forms.ModelChoiceField(
                queryset=User.objects.filter(profile__user_type='doctor'),
                to_field_name='username',
                label='Select a Doctor'
            )
        else:
            self.fields['receiver'] = forms.CharField(max_length=150, label='Receiver Username')

def clean_receiver(self):
    receiver = self.cleaned_data.get('receiver')
    
    # Get receiver user instance
    if isinstance(receiver, User):
        receiver_user = receiver
    else:
        try:
            receiver_user = User.objects.get(username=receiver)
        except User.DoesNotExist:
            raise forms.ValidationError("Receiver not found.")
    
    # Check if receiver has a profile
    if not hasattr(receiver_user, 'profile') or receiver_user.profile is None:
        raise forms.ValidationError("The selected receiver does not have a profile.")
    
    # Validate permissions based on user type
    if self.user.profile.user_type == 'patient' and receiver_user.profile.user_type != 'doctor':
        raise forms.ValidationError("Patients can only send images to doctors.")
    
    return receiver_user.username
