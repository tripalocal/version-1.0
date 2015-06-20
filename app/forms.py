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

Location = (('Melbourne', 'Melbourne, VIC'),('Sydney', 'Sydney, NSW'),('Brisbane', 'Brisbane, QLD'),('Cairns','Cairns, QLD'),
            ('Goldcoast','Gold coast, QLD'),('Hobart','Hobart, TAS'), ('Adelaide', 'Adelaide, SA'),)
class HomepageSearchForm(forms.Form):
    city = forms.ChoiceField(choices=Location)
    start_date = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))
    end_date = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))

class UserProfileForm(forms.Form):
    image = forms.ImageField(required = False)
    first_name=forms.CharField(required = False)
    last_name=forms.CharField(required = False)
    email=forms.EmailField(required = False)
    phone_number = forms.CharField(required = False)
    bio = forms.CharField(widget=forms.Textarea, required = False)

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['readonly'] = True
        self.fields['last_name'].widget.attrs['readonly'] = True
        self.fields['email'].widget.attrs['readonly'] = True

class BookingRequestXLSForm(forms.Form):
    file = forms.FileField()

class ExperienceTagsXLSForm(forms.Form):
    file = forms.FileField()

Repeat_Cycle = (('Daily', 'Daily'), ('Weekly', 'Weekly'), ('Monthly', 'Monthly'),)

Repeat_Frequency = (('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),
    ('6', '6'),('7', '7'),('8', '8'),('9', '9'),('10', '10'),)

class UserCalendarForm(forms.Form):
    blockout_start_datetime_1 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_1 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_1 = forms.BooleanField(required=False)
    blockout_repeat_cycle_1 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    blockout_repeat_frequency_1 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    blockout_repeat_end_date_1 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    blockout_repeat_extra_information_1 = forms.CharField(required=False, max_length=50)

    blockout_start_datetime_2 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_2 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_2 = forms.BooleanField(required=False)
    blockout_repeat_cycle_2 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    blockout_repeat_frequency_2 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    blockout_repeat_end_date_2 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    blockout_repeat_extra_information_2 = forms.CharField(required=False, max_length=50)

    blockout_start_datetime_3 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_3 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_3 = forms.BooleanField(required=False)
    blockout_repeat_cycle_3 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    blockout_repeat_frequency_3 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    blockout_repeat_end_date_3 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    blockout_repeat_extra_information_3 = forms.CharField(required=False, max_length=50)

    blockout_start_datetime_4 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_4 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_4 = forms.BooleanField(required=False)
    blockout_repeat_cycle_4 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    blockout_repeat_frequency_4 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    blockout_repeat_end_date_4 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    blockout_repeat_extra_information_4 = forms.CharField(required=False, max_length=50)

    blockout_start_datetime_5 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_5 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_5 = forms.BooleanField(required=False)
    blockout_repeat_cycle_5 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    blockout_repeat_frequency_5 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    blockout_repeat_end_date_5 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    blockout_repeat_extra_information_5 = forms.CharField(required=False, max_length=50)

    instant_booking_start_datetime_1 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_1 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_1 = forms.BooleanField(required=False)
    instant_booking_repeat_cycle_1 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    instant_booking_repeat_frequency_1 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    instant_booking_repeat_end_date_1 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    instant_booking_repeat_extra_information_1 = forms.CharField(required=False, max_length=50)

    instant_booking_start_datetime_2 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_2 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_2 = forms.BooleanField(required=False)
    instant_booking_repeat_cycle_2 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    instant_booking_repeat_frequency_2 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    instant_booking_repeat_end_date_2 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    instant_booking_repeat_extra_information_2 = forms.CharField(required=False, max_length=50)

    instant_booking_start_datetime_3 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_3 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_3 = forms.BooleanField(required=False)
    instant_booking_repeat_cycle_3 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    instant_booking_repeat_frequency_3 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    instant_booking_repeat_end_date_3 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    instant_booking_repeat_extra_information_3 = forms.CharField(required=False, max_length=50)

    instant_booking_start_datetime_4 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_4 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_4 = forms.BooleanField(required=False)
    instant_booking_repeat_cycle_4 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    instant_booking_repeat_frequency_4 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    instant_booking_repeat_end_date_4 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    instant_booking_repeat_extra_information_4 = forms.CharField(required=False, max_length=50)

    instant_booking_start_datetime_5 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_5 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_5 = forms.BooleanField(required=False)
    instant_booking_repeat_cycle_5 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    instant_booking_repeat_frequency_5 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    instant_booking_repeat_end_date_5 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    instant_booking_repeat_extra_information_5 = forms.CharField(required=False, max_length=50)