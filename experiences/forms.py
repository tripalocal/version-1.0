from django import forms
from bootstrap3_datetime.widgets import DateTimePicker
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from datetime import date, datetime
from calendar import monthrange 
from experiences.models import Payment, Booking, Experience, RegisteredUser, Coupon
from Tripalocal_V1 import settings
import pytz, string, subprocess, json, random
from django.core.mail import send_mail
from django.template import loader
from tripalocal_messages.models import Aliases, Users
from allauth.account.signals import user_signed_up
from django.dispatch import receiver

Type = (('SEE', 'See'),('DO', 'Do'),('EAT', 'Eat'),)

Location = (('Melbourne', 'Melbourne'),('Sydney', 'Sydney'),('Brisbane', 'Brisbane'),)

Repeat_Cycle = (('Hourly','Hourly'), ('Daily', 'Daily'),
    ('Weekly', 'Weekly'),)

Repeat_Frequency = (('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),
    ('6', '6'),('7', '7'),('8', '8'),('9', '9'),('10', '10'),)

Guest_Number_Min = (('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),)

Guest_Number_Max = (('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),
    ('6', '6'),('7', '7'),('8', '8'),('9', '9'),('10', '10'),)

Duration = (('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),
    ('6', '6'),('7', '7'),('8', '8'),('9', '9'),('10', '10'),)

Included = (('Yes', 'Yes'),('No', 'No'),)

Suburbs = (('Melbourne', 'Melbourne'),('Sydney', 'Sydney'),)

Country = (('Australia', 'Australia'),('China', 'China'),('Afghanistan', 'Afghanistan'),('Albania', 'Albania'),('Algeria', 'Algeria'),('Andorra', 'Andorra'),('Angola', 'Angola'),('Antigua and Barbuda', 'Antigua and Barbuda'),('Argentina', 'Argentina'),('Armenia', 'Armenia'),('Aruba', 'Aruba'),('Austria', 'Austria'),('Azerbaijan', 'Azerbaijan'),('Bahamas', 'Bahamas'),('Bahrain', 'Bahrain'),('Bangladesh', 'Bangladesh'),('Barbados', 'Barbados'),('Belarus', 'Belarus'),('Belgium', 'Belgium'),('Belize', 'Belize'),('Benin', 'Benin'),('Bhutan', 'Bhutan'),('Bolivia', 'Bolivia'),('Bosnia and Herzegovina', 'Bosnia and Herzegovina'),('Botswana', 'Botswana'),('Brazil', 'Brazil'),('Brunei ', 'Brunei '),('Bulgaria', 'Bulgaria'),('Burkina Faso', 'Burkina Faso'),
('Burma', 'Burma'),('Burundi', 'Burundi'),('Cambodia', 'Cambodia'),('Cameroon', 'Cameroon'),('Canada', 'Canada'),('Cape Verde', 'Cape Verde'),('Central African Republic', 'Central African Republic'),('Chad', 'Chad'),('Chile', 'Chile'),('Colombia', 'Colombia'),('Comoros', 'Comoros'),('Congo, Democratic Republic of the', 'Congo, Democratic Republic of the'),('Congo, Republic of the', 'Congo, Republic of the'),('Costa Rica', 'Costa Rica'),('Cote dIvoire', 'Cote dIvoire'),('Croatia', 'Croatia'),('Cuba', 'Cuba'),('Curacao', 'Curacao'),('Cyprus', 'Cyprus'),('Czech Republic', 'Czech Republic'),('Denmark', 'Denmark'),('Djibouti', 'Djibouti'),('Dominica', 'Dominica'),('Dominican Republic', 'Dominican Republic'),
('East Timor', 'East Timor'),('Ecuador', 'Ecuador'),('Egypt', 'Egypt'),('El Salvador', 'El Salvador'),('Equatorial Guinea', 'Equatorial Guinea'),('Eritrea', 'Eritrea'),('Estonia', 'Estonia'),('Ethiopia', 'Ethiopia'),('Fiji', 'Fiji'),('Finland', 'Finland'),('France', 'France'),('Gabon', 'Gabon'),('Gambia', 'Gambia'),('Georgia', 'Georgia'),('Germany', 'Germany'),('Ghana', 'Ghana'),('Greece', 'Greece'),('Grenada', 'Grenada'),('Guatemala', 'Guatemala'),('Guinea', 'Guinea'),('Guinea-Bissau', 'Guinea-Bissau'),('Guyana', 'Guyana'),('Haiti', 'Haiti'),('Holy See', 'Holy See'),('Honduras', 'Honduras'),('Hong Kong, China', 'Hong Kong, China'),('Hungary', 'Hungary'),('Iceland', 'Iceland'),('India', 'India'),('Indonesia', 'Indonesia'),
('Iran', 'Iran'),('Iraq', 'Iraq'),('Ireland', 'Ireland'),('Israel', 'Israel'),('Italy', 'Italy'),('Jamaica', 'Jamaica'),('Japan', 'Japan'),('Jordan', 'Jordan'),('Kazakhstan', 'Kazakhstan'),('Kenya', 'Kenya'),('Kiribati', 'Kiribati'),('Korea, North', 'Korea, North'),('Korea, South', 'Korea, South'),('Kosovo', 'Kosovo'),('Kuwait', 'Kuwait'),('Kyrgyzstan', 'Kyrgyzstan'),('Laos', 'Laos'),('Latvia', 'Latvia'),('Lebanon', 'Lebanon'),('Lesotho', 'Lesotho'),('Liberia', 'Liberia'),('Libya', 'Libya'),('Liechtenstein', 'Liechtenstein'),('Lithuania', 'Lithuania'),('Luxembourg', 'Luxembourg'),('Macau, China', 'Macau, China'),('Macedonia', 'Macedonia'),('Madagascar', 'Madagascar'),('Malawi', 'Malawi'),('Malaysia', 'Malaysia'),
('Maldives', 'Maldives'),('Mali', 'Mali'),('Malta', 'Malta'),('Marshall Islands', 'Marshall Islands'),('Mauritania', 'Mauritania'),('Mauritius', 'Mauritius'),('Mexico', 'Mexico'),('Micronesia', 'Micronesia'),('Moldova', 'Moldova'),('Monaco', 'Monaco'),('Mongolia', 'Mongolia'),('Montenegro', 'Montenegro'),('Morocco', 'Morocco'),('Mozambique', 'Mozambique'),('Namibia', 'Namibia'),('Nauru', 'Nauru'),('Nepal', 'Nepal'),('Netherlands', 'Netherlands'),('Netherlands Antilles', 'Netherlands Antilles'),('New Zealand', 'New Zealand'),('Nicaragua', 'Nicaragua'),('Niger', 'Niger'),('Nigeria', 'Nigeria'),('North Korea', 'North Korea'),('Norway', 'Norway'),('Oman', 'Oman'),('Pakistan', 'Pakistan'),('Palau', 'Palau'),
('Palestinian Territories', 'Palestinian Territories'),('Panama', 'Panama'),('Papua New Guinea', 'Papua New Guinea'),('Paraguay', 'Paraguay'),('Peru', 'Peru'),('Philippines', 'Philippines'),('Poland', 'Poland'),('Portugal', 'Portugal'),('Qatar', 'Qatar'),('Romania', 'Romania'),('Russia', 'Russia'),('Rwanda', 'Rwanda'),('Saint Kitts and Nevis', 'Saint Kitts and Nevis'),('Saint Lucia', 'Saint Lucia'),('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'),('Samoa ', 'Samoa '),('San Marino', 'San Marino'),('Sao Tome and Principe', 'Sao Tome and Principe'),('Saudi Arabia', 'Saudi Arabia'),('Senegal', 'Senegal'),('Serbia', 'Serbia'),('Seychelles', 'Seychelles'),('Sierra Leone', 'Sierra Leone'),('Singapore', 'Singapore'),
('Sint Maarten', 'Sint Maarten'),('Slovakia', 'Slovakia'),('Slovenia', 'Slovenia'),('Solomon Islands', 'Solomon Islands'),('Somalia', 'Somalia'),('South Africa', 'South Africa'),('South Korea', 'South Korea'),('South Sudan', 'South Sudan'),('Spain ', 'Spain '),('Sri Lanka', 'Sri Lanka'),('Sudan', 'Sudan'),('Suriname', 'Suriname'),('Swaziland ', 'Swaziland '),('Sweden', 'Sweden'),('Switzerland', 'Switzerland'),('Syria', 'Syria'),('Taiwan, China', 'Taiwan, China'),('Tajikistan', 'Tajikistan'),('Tanzania', 'Tanzania'),('Thailand ', 'Thailand '),('Timor-Leste', 'Timor-Leste'),('Togo', 'Togo'),('Tonga', 'Tonga'),('Trinidad and Tobago', 'Trinidad and Tobago'),('Tunisia', 'Tunisia'),('Turkey', 'Turkey'),('Turkmenistan', 'Turkmenistan'),
('Tuvalu', 'Tuvalu'),('Uganda', 'Uganda'),('Ukraine', 'Ukraine'),('United Arab Emirates', 'United Arab Emirates'),('United Kingdom', 'United Kingdom'),('Uruguay', 'Uruguay'),('Uzbekistan', 'Uzbekistan'),('Vanuatu', 'Vanuatu'),('Venezuela', 'Venezuela'),('Vietnam', 'Vietnam'),('Yemen', 'Yemen'),('Zambia', 'Zambia'),('Zimbabwe ', 'Zimbabwe '),)

#from http://stackoverflow.com/questions/16773579/customize-radio-buttons-in-django
class HorizRadioRenderer(forms.RadioSelect.renderer):
    """ this overrides widget method to put radio buttons horizontally
        instead of vertically.
    """
    def render(self):
            """Outputs radios"""
            return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))

class ExperienceForm(forms.Form):
    type = forms.ChoiceField(choices=Type, required=True)
    title = forms.CharField(max_length=100, required=True)
    guest_number = forms.IntegerField(required=True)
    location = forms.ChoiceField(choices=Location, required=True)

class ExperienceCalendarForm(forms.Form):
    date_time = forms.DateTimeField(required=True, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))

class BookingForm(forms.Form):
    user_id = forms.CharField()
    experience_id = forms.CharField()
    date = forms.ChoiceField(label="")
    time = forms.ChoiceField(label="")
    guest_number = forms.ChoiceField(label="")
    status = forms.CharField(initial="Requested")

    def __init__(self, available_date, experience_id, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
        self.fields['date'] = forms.ChoiceField(choices = available_date)
        self.fields['experience_id'] = forms.CharField(initial=experience_id)
        self.fields['experience_id'].widget.attrs['readonly'] = True
        self.fields['experience_id'].widget = forms.HiddenInput()
        self.fields['user_id'].widget.attrs['readonly'] = True
        self.fields['user_id'].widget = forms.HiddenInput()
        self.fields['status'].widget.attrs['readonly'] = True
        self.fields['status'].widget = forms.HiddenInput()
        self.fields['guest_number'].widget.attrs.update({'class' : 'booking_form_people'})
        self.fields['date'].widget.attrs.update({'class' : 'booking_form_date'})
        self.fields['time'].widget.attrs.update({'class' : 'booking_form_time'})

class CreditCardField(forms.IntegerField):
    def clean(self, value):
        """Check if given CC number is valid and one of the
           card types we accept"""
        if value and (len(value) < 13 or len(value) > 16):
            raise forms.ValidationError("Please enter in a valid credit card number.")
        return super(CreditCardField, self).clean(value)
 
class CCExpWidget(forms.MultiWidget):
    """ Widget containing two select boxes for selecting the month and year"""
    def decompress(self, value):
        return [value.month, value.year] if value else [None, None]
 
    def format_output(self, rendered_widgets):
        html = u' / '.join(rendered_widgets)
        return u'<span style="white-space: nowrap;">%s</span>' % html
 
class CCExpField(forms.MultiValueField):
    EXP_MONTH = [(x, x) for x in range(1, 13)]
    EXP_YEAR = [(x, x) for x in range(date.today().year, date.today().year + 15)]
    default_error_messages = {
        'invalid_month': u'Enter a valid month.',
        'invalid_year': u'Enter a valid year.',
    }
 
    def __init__(self, *args, **kwargs):
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])
        fields = (
            forms.ChoiceField(choices=self.EXP_MONTH,
                error_messages={'invalid': errors['invalid_month']}),
            forms.ChoiceField(choices=self.EXP_YEAR,
                error_messages={'invalid': errors['invalid_year']}),
        )
        super(CCExpField, self).__init__(fields, *args, **kwargs)
        self.widget = CCExpWidget(widgets =
            [fields[0].widget, fields[1].widget])
 
    def clean(self, value):
        exp = super(CCExpField, self).clean(value)
        if date.today() > exp:
            raise forms.ValidationError("Invalid date.")
        return exp
 
    def compress(self, data_list):
        if data_list:
            if data_list[1] in forms.fields.EMPTY_VALUES:
                error = self.error_messages['invalid_year']
                raise forms.ValidationError(error)
            if data_list[0] in forms.fields.EMPTY_VALUES:
                error = self.error_messages['invalid_month']
                raise forms.ValidationError(error)
            year = int(data_list[1])
            month = int(data_list[0])
            # find last day of the month
            day = monthrange(year, month)[1]
            return date(year, month, day)
        return None

class BookingConfirmationForm(forms.Form):
    user_id = forms.CharField()
    experience_id = forms.CharField()
    date = forms.DateField()
    time = forms.TimeField()
    guest_number = forms.IntegerField(label="People")
    status = forms.CharField(initial="Requested")
    promo_code = forms.CharField(required=False)

    card_number = CreditCardField(required=True, label="Card Number")
    expiration = CCExpField(required=True, label="Expiration")
    cvv = forms.IntegerField(required=True, label="CVV Number",
        max_value=9999, widget=forms.TextInput(attrs={'size': '4'}))

    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    street1 = forms.CharField(max_length=50)
    street2 = forms.CharField(max_length=50, required = False)
    city = forms.CharField(max_length=20)
    state = forms.CharField(max_length=10)
    country = forms.ChoiceField(choices=Country, required=True)
    postcode = forms.CharField(max_length=4)
    phone_number = forms.CharField(max_length=15, required=False)

    coupon_extra_information = forms.CharField(max_length=500, required=False)

    def __init__(self, *args, **kwargs):
        super(BookingConfirmationForm, self).__init__(*args, **kwargs)
        self.fields['experience_id'].widget.attrs['readonly'] = True
        self.fields['user_id'].widget.attrs['readonly'] = True
        self.fields['guest_number'].widget.attrs['readonly'] = True
        self.fields['date'].widget.attrs['readonly'] = True
        self.fields['time'].widget.attrs['readonly'] = True
        self.fields['status'].widget.attrs['readonly'] = True
        self.fields['experience_id'].widget = forms.HiddenInput()
        self.fields['user_id'].widget = forms.HiddenInput()
        self.fields['date'].widget = forms.HiddenInput()
        self.fields['time'].widget = forms.HiddenInput()
        self.fields['guest_number'].widget = forms.HiddenInput()
        self.fields['status'].widget = forms.HiddenInput()
        self.fields['coupon_extra_information'].widget = forms.HiddenInput()

    def clean(self):
        """
        The clean method will effectively charge the card and create a new
        Payment instance. If it fails, it simply raises the error given from
        Stripe's library as a standard ValidationError for proper feedback.
        """
        cleaned = super(BookingConfirmationForm, self).clean()
 
        if not self.errors:
            card_number = self.cleaned_data["card_number"]
            exp_month = self.cleaned_data["expiration"].month
            exp_year = self.cleaned_data["expiration"].year
            cvv = self.cleaned_data["cvv"]
            experience = Experience.objects.get(id=self.cleaned_data['experience_id'])

            extra_fee = 0.00

            cp = Coupon.objects.filter(promo_code = self.cleaned_data['promo_code'])

            if len(cp)>0 and len(self.cleaned_data["coupon_extra_information"]) > 0:
                extra = json.loads(self.cleaned_data["coupon_extra_information"])
                if type(extra["extra_fee"]) == int or type(extra["extra_fee"]) == float:
                    extra_fee = extra["extra_fee"]

            price = round(float(self.cleaned_data["guest_number"])*float(experience.price)*(1.00+settings.COMMISSION_PERCENT),2) + extra_fee
 
            payment = Payment()
            #change price into cent
            success, instance = payment.charge(int(price*100), card_number, exp_month, exp_year, cvv)
 
            if not success:
                raise forms.ValidationError("Error: %s" % str(instance))
            else:
                instance.save()
                #save the booking record
                user = User.objects.get(id=self.cleaned_data['user_id'])
                date = self.cleaned_data['date']
                time = self.cleaned_data['time']
                local_timezone = pytz.timezone(settings.TIME_ZONE)
                if len(cp) > 0:
                    booking = Booking(user = user, experience= experience, guest_number = self.cleaned_data['guest_number'], 
                                      datetime = local_timezone.localize(datetime(date.year, date.month, date.day, time.hour, time.minute)).astimezone(pytz.timezone("UTC")),
                                      submitted_datetime = datetime.utcnow(), status="paid", 
                                      coupon_extra_information=self.cleaned_data['coupon_extra_information'],
                                      coupon=Coupon.objects.get(promo_code = self.cleaned_data['promo_code']))
                else:
                    booking = Booking(user = user, experience= experience, guest_number = self.cleaned_data['guest_number'], 
                                      datetime = local_timezone.localize(datetime(date.year, date.month, date.day, time.hour, time.minute)).astimezone(pytz.timezone("UTC")),
                                      submitted_datetime = datetime.utcnow(), status="paid")
                booking.save()
                #add the user to the guest list
                #if user not in experience.guests.all():
                #    experience.guests.add(user)

                payment.charge_id = instance['id']
                payment.booking_id = booking.id
                payment.street1 = self.cleaned_data['street1']
                payment.street2 = self.cleaned_data['street2']
                payment.city = self.cleaned_data['city']
                payment.state = self.cleaned_data['state']
                payment.country = self.cleaned_data['country']
                payment.postcode = self.cleaned_data['postcode']
                payment.phone_number = self.cleaned_data['phone_number']
                payment.save()

                booking.payment_id = payment.id
                booking.save()

                # send an email to the host
                send_mail('[Tripalocal] ' + user.first_name + ' has requested your experience', '', 
                          'Tripalocal <' + Aliases.objects.filter(destination__contains=user.email)[0].mail + '>',
                            [Aliases.objects.filter(destination__contains=experience.hosts.all()[0].email)[0].mail], fail_silently=False,
                            html_message=loader.render_to_string('email_booking_requested_host.html', 
                                                                 {'experience': experience,
                                                                  'booking':booking,
                                                                  'user_first_name':user.first_name,
                                                                  'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                                  'accept_url': settings.DOMAIN_NAME + '/booking/' + str(booking.id) + '?accept=yes',
                                                                  'reject_url': settings.DOMAIN_NAME + '/booking/' + str(booking.id) + '?accept=no'}))
                # send an email to the traveler
                send_mail('[Tripalocal] You booking request is sent to the host', '', 
                          'Tripalocal <' + Aliases.objects.filter(destination__contains=experience.hosts.all()[0].email)[0].mail + '>',
                            [Aliases.objects.filter(destination__contains=user.email)[0].mail], fail_silently=False, 
                            html_message=loader.render_to_string('email_booking_requested_traveler.html',
                                                                 {'experience': experience, 
                                                                  'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                                  'booking':booking}))
                pass
 
        return cleaned

class CreateExperienceForm(forms.Form):
    start_datetime = forms.DateTimeField(required=True, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    end_datetime = forms.DateTimeField(required=True, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    repeat_cycle = forms.ChoiceField(choices=Repeat_Cycle)
    repeat_frequency = forms.ChoiceField(choices=Repeat_Frequency)
    title = forms.CharField()
    summary = forms.CharField(widget=forms.Textarea)
    guest_number_min = forms.ChoiceField(choices=Guest_Number_Min)
    guest_number_max = forms.ChoiceField(choices=Guest_Number_Max)
    price = forms.DecimalField(max_digits=6, decimal_places=2)
    price_with_booking_fee = forms.DecimalField(max_digits=6, decimal_places=2)
    duration = forms.ChoiceField(choices=Duration)
    included_food = forms.ChoiceField(widget=forms.RadioSelect(renderer=HorizRadioRenderer), choices=Included)
    included_food_detail = forms.CharField(required = False)
    included_transport = forms.ChoiceField(widget=forms.RadioSelect(renderer=HorizRadioRenderer), choices=Included)
    included_transport_detail = forms.CharField(required = False)
    included_ticket = forms.ChoiceField(widget=forms.RadioSelect(renderer=HorizRadioRenderer), choices=Included)
    included_ticket_detail = forms.CharField(required = False)
    activity = forms.CharField(widget=forms.Textarea)
    interaction = forms.CharField(widget=forms.Textarea)
    dress_code = forms.CharField(widget=forms.Textarea)
    suburb = forms.ChoiceField(choices=Suburbs)
    meetup_spot = forms.CharField(widget=forms.Textarea)
    experience_photo_1 = forms.ImageField(required = False)
    experience_photo_2 = forms.ImageField(required = False)
    experience_photo_3 = forms.ImageField(required = False)
    experience_photo_4 = forms.ImageField(required = False)
    experience_photo_5 = forms.ImageField(required = False)

def email_account_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class UserSignupForm(forms.Form):
    def signup(self, request, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        
@receiver(user_signed_up)
def handle_user_signed_up(request, **kwargs):
    user = kwargs['user']

    new_registereduser = RegisteredUser(user_id = user.id)
    new_registereduser.save()

    username = user.username

    new_email = Users(id = email_account_generator() + ".user" + "@" + settings.DOMAIN_NAME,
                        name = username,
                        maildir = username + "/")
    new_email.save()

    new_alias = Aliases(mail = new_email.id, destination = user.email + ", " + new_email.id)
    new_alias.save()

    with open('/etc/postfix/canonical', 'a') as f:
        f.write(user.email + " " + new_email.id + "\n")
        f.close()

    subprocess.Popen(['sudo','postmap','/etc/postfix/canonical'])
    
    with open('/etc/postgrey/whitelist_recipients.local', 'a') as f:
        f.write(new_email.id + "\n")
        f.close()
