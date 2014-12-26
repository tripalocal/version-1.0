"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from app.models import Subscription
from bootstrap3_datetime.widgets import DateTimePicker

class BootstrapAuthenticationForm(AuthenticationForm):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control',
                                   'placeholder': 'User name'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({
                                   'class': 'form-control',
                                   'placeholder':'Password'}))

class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['email']

Location = (('Melbourne', 'Melbourne'),('Sydney', 'Sydney'),)
class HomepageSearchForm(forms.Form):
    city = forms.ChoiceField(choices=Location)
    start_date = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))
    end_date = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))

