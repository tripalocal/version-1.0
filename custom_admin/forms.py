from django import forms
from django.forms.extras.widgets import SelectDateWidget
RATE_CHOICES = [('1','1'), ('2','2'), ('3','3'), ('4','4'), ('5','5')]
EXPERIENCE_STATUS_CHOICES = {'Listed':True, 'Unlisted':True, 'Submitted':True, 'Draft': True }
BOOKING_STATUS_CHOICES = {'requested':True, 'accepted':True, 'rejected':True, 'no_show': True, 'paid': True, 'deleted':True, 'archived':True, 'unarchived':True}

class AjaxFormFieldMixin(object):
    object_id = forms.IntegerField(required=False)
    operation = forms.CharField(max_length=30, required=False)

class BookingForm(forms.Form):
    review = forms.CharField(widget=forms.Textarea, required=False)
    rate = forms.ChoiceField(choices=RATE_CHOICES, required=False)
    new_date = forms.DateField(input_formats=['%Y-%m-%d'], widget = SelectDateWidget(), required=False)
    new_time = forms.TimeField(required=False)
    status = forms.CharField(required=False)

    def clean_status(self):
        data = self.cleaned_data['status']
        if data and data not in BOOKING_STATUS_CHOICES:
            raise forms.ValidationError("You have wrong choice!")
        return data

class ExperienceUploadForm(forms.Form):
    status = forms.CharField(max_length=10, required=False)
    commission = forms.FloatField(required=False)

    def clean_status(self):
        data = self.cleaned_data['status']
        if data not in EXPERIENCE_STATUS_CHOICES:
            raise forms.ValidationError("You have wrong choice!")
        return data