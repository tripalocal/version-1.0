from django import forms
from django.forms.extras.widgets import SelectDateWidget
RATE_CHOICES = [('1','1'), ('2','2'), ('3','3'), ('4','4'), ('5','5')]
STATUS_CHOICES = {'Listed':True, 'Unlisted':True, 'Submitted':True, 'Draft': True }

class BookingFrom(forms.Form):
    review = forms.CharField(widget=forms.Textarea, required=False)
    rate = forms.ChoiceField(choices=RATE_CHOICES, required=False)
    new_date = forms.DateField(input_formats=['%Y-%m-%d'], widget = SelectDateWidget(), required=False)
    new_time = forms.TimeField(required=False)

    # def clean_new_time(self):
    #     cleaned_time = self.cleaned_data['new_time'].split(":")
    #     if cleaned_time.__len__() == 2:
    #         hour = cleaned_time[0]
    #         minute = cleaned_time[1]
    #
    #         if not (hour.isdigit() and int(hour) <= 24 and int(hour) >=0 and minute.isdigit() and int(minute) <= 60 and int(minute) >=0):
    #             msg = "Must put 'help' in subject when cc'ing yourself."
    #             self.add_error('new_time', msg)
    #     else:
    #         msg = "Must put 'help' in subject when cc'ing yourself."
    #         self.add_error('new_time', msg)

class ExperienceUploadForm(forms.Form):
    status = forms.CharField(max_length=10, required=False)
    commission = forms.FloatField(required=False)

    def clean_status(self):
        data = self.cleaned_data['status']
        if data not in STATUS_CHOICES:
            raise forms.ValidationError("You have wrong choice!")
        return data