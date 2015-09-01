from django.utils.translation import ugettext as _
from django import forms
from django.forms.extras.widgets import SelectDateWidget

RATE_CHOICES = [('1','1'), ('2','2'), ('3','3'), ('4','4'), ('5','5')]
EXPERIENCE_STATUS_CHOICES = {'Listed':True, 'Unlisted':True, 'Submitted':True, 'Draft': True }
BOOKING_STATUS_CHOICES = {'requested':True, 'accepted':True, 'rejected':True, 'no_show': True, 'paid': True, 'deleted':True, 'archived':True, 'unarchived':True}
Suburbs = (('Melbourne', _('Melbourne, VIC')),('Sydney', _('Sydney, NSW')),('Brisbane', _('Brisbane, QLD')),('Cairns',_('Cairns, QLD')),
            ('Goldcoast',_('Gold coast, QLD')),('Hobart',_('Hobart, TAS')), ('Adelaide', _('Adelaide, SA')),('GRSA', _('Greater South Australia')),
            ('GRVIC', _('Greater Victoria')),('GRNSW', _('Greater New South Wales')),('GRQLD', _('Greater Queensland')),
            ('Darwin',_('Darwin, NT')),('Alicesprings',_('Alice Springs, NT')),('GRNT', _('Greater Northern Territory')),
            ('Christchurch',_('Christchurch, NZ')),('Queenstown',_('Queenstown, NZ')),('Auckland', _('Auckland, NZ')),('Wellington', _('Wellington, NZ')),)
Duration = (('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),('6', '6'),('7', '7'),('8', '8'),('9', '9'),('10', '10'),
('11', '11'),('12', '12'),('13', '13'),('14', '14'),('15', '15'),('16', '16'),('17', '17'),('18', '18'),('19', '19'),('20', '20'),
('21', '21'),('22', '22'),('23', '23'),('24', '24'),('36', '36'),('48', '48'),('60', '60'),('72', '72'),('84', '84'),('96', '96'),
('108', '108'),('120', '120'),('144', '144'),('168', '168'),('192', '192'),('216', '216'),('240', '240'),('264', '264'),('288', '288'),)

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
        if data and data not in EXPERIENCE_STATUS_CHOICES:
            raise forms.ValidationError("You have wrong choice!")
        return data

class CreateExperienceForm(forms.Form):
    id = forms.CharField(max_length=10, required=False)
    title = forms.CharField(max_length=100, required=False)
    duration = forms.ChoiceField(choices=Duration, required=False)
    location = forms.ChoiceField(choices=Suburbs, required=False)
    changed_steps = forms.CharField(max_length=100, required=False)
    user_id = forms.IntegerField(required=True)

    def __init__(self, *args, **kwargs):
        super(CreateExperienceForm, self).__init__(*args, **kwargs)
        self.fields['id'].widget.attrs['readonly'] = True
        self.fields['id'].widget = forms.HiddenInput()
        self.fields['changed_steps'].widget.attrs['readonly'] = True
        self.fields['changed_steps'].widget = forms.HiddenInput()