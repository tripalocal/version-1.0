from django import forms
from django.forms.extras.widgets import SelectDateWidget

class ChangeTimeForm(forms.Form):
    new_date = forms.DateTimeField(widget = SelectDateWidget())
    new_time = forms.CharField(max_length = 5)

    def clean(self):
        cleaned_data = super(ChangeTimeForm, self).clean()
        cleaned_time = self.cleaned_data['new_time'].split(":")
        if cleaned_time.__len__() == 2:
            hour = cleaned_time[0]
            minute = cleaned_time[1]
       
            if not (hour.isdigit() and int(hour) <= 24 and int(hour) >=0 and minute.isdigit() and int(minute) <= 60 and int(minute) >=0):
                msg = "Must put 'help' in subject when cc'ing yourself."
                self.add_error('new_time', msg)
        else:
            msg = "Must put 'help' in subject when cc'ing yourself."
            self.add_error('new_time', msg)
RATE_CHOICES = [('1','1'), ('2','2'), ('3','3'), ('4','4'), ('5','5')]
STATUS_CHOICES = {'Listed':True, 'Unlisted':True, 'Submitted':True, 'Draft': True }

class UploadReviewForm(forms.Form):
    review = forms.CharField(widget=forms.Textarea)  
    rate = forms.ChoiceField(choices=RATE_CHOICES)
    new_date = forms.DateTimeField(widget = SelectDateWidget())
    new_time = forms.CharField(max_length = 5)

    def clean_new_time(self):
        cleaned_time = self.cleaned_data['new_time'].split(":")
        if cleaned_time.__len__() == 2:
            hour = cleaned_time[0]
            minute = cleaned_time[1]

            if not (hour.isdigit() and int(hour) <= 24 and int(hour) >=0 and minute.isdigit() and int(minute) <= 60 and int(minute) >=0):
                msg = "Must put 'help' in subject when cc'ing yourself."
                self.add_error('new_time', msg)
        else:
            msg = "Must put 'help' in subject when cc'ing yourself."
            self.add_error('new_time', msg)

class BookingFrom(forms.Form):
    review = forms.CharField(widget=forms.Textarea)
    rate = forms.ChoiceField(choices=RATE_CHOICES)
    new_date = forms.DateField(widget = SelectDateWidget(), required=False)
    new_time = forms.CharField(max_length = 5, required=False)

    def clean_new_time(self):
        cleaned_time = self.cleaned_data['new_time'].split(":")
        if cleaned_time.__len__() == 2:
            hour = cleaned_time[0]
            minute = cleaned_time[1]

            if not (hour.isdigit() and int(hour) <= 24 and int(hour) >=0 and minute.isdigit() and int(minute) <= 60 and int(minute) >=0):
                msg = "Must put 'help' in subject when cc'ing yourself."
                self.add_error('new_time', msg)
        else:
            msg = "Must put 'help' in subject when cc'ing yourself."
            self.add_error('new_time', msg)

class ExperienceUploadForm(forms.Form):
    status = forms.CharField(max_length=10, required=False)
    commission = forms.FloatField(required=False)

    def clean_status(self):
        data = self.cleaned_data['status']
        if data not in STATUS_CHOICES:
            raise forms.ValidationError("You have wrong choice!")
        return data