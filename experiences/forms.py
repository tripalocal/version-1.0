from django import forms
from bootstrap3_datetime.widgets import DateTimePicker
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from datetime import date, datetime
from calendar import monthrange 
from experiences.models import Payment, Booking, Experience, RegisteredUser
from Tripalocal_V1 import settings
import pytz, string, subprocess
from django.core.mail import send_mail
from django.template import loader
from tripalocal_messages.models import Aliases, Users

Type = (('SEE', 'See'),('DO', 'Do'),('EAT', 'Eat'),)

Location = (('Melbourne', 'Melbourne'),('Sydney', 'Sydney'),('Brisbane', 'Brisbane'),)

Repeat_Cycle = (('Daily', 'Daily'),
    ('Weekly', 'Weekly'),('Monthly', 'Monthly'),)

Repeat_Frequency = (('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),
    ('6', '6'),('7', '7'),('8', '8'),('9', '9'),('10', '10'),)

Guest_Number_Min = (('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),)

Guest_Number_Max = (('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),
    ('6', '6'),('7', '7'),('8', '8'),('9', '9'),('10', '10'),)

Duration = (('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),
    ('6', '6'),('7', '7'),('8', '8'),('9', '9'),('10', '10'),)

Included = (('Yes', 'Yes'),('No', 'No'),)

Suburbs = (('Abbotsford','Abbotsford'),('Aberfeldie','Aberfeldie'),('Airport West','Airport West'),('Albanvale','Albanvale'),('Albert Park','Albert Park'),('Albion','Albion'),('Alphington','Alphington'),('Altona','Altona'),('Altona East','Altona East'),('Altona Meadows','Altona Meadows'),('Ardeer','Ardeer'),('Armadale','Armadale'),('Arthurs Creek','Arthurs Creek'),('Ascot Vale','Ascot Vale'),('Ashburton','Ashburton'),('Aspendale','Aspendale'),('Attwood','Attwood'),('Auburn','Auburn'),('Auburn South','Auburn South'),('Avondale Heights','Avondale Heights'),('Avonsleigh','Avonsleigh'),('Badger Creek','Badger Creek'),('Balaclava','Balaclava'),('Balwyn','Balwyn'),('Balwyn North','Balwyn North'),
('Bangholme','Bangholme'),('Banyule','Banyule'),('Batman','Batman'),('Bayles','Bayles'),('Bayswater','Bayswater'),('Beaconsfield','Beaconsfield'),('Beaconsfield Upper','Beaconsfield Upper'),('Beaconsfield Upper','Beaconsfield Upper'),('Beaumaris','Beaumaris'),('Bedford Road','Bedford Road'),('Beenak','Beenak'),('Belgrave','Belgrave'),('Bellfield','Bellfield'),('Bend Of Islands','Bend Of Islands'),('Bentleigh','Bentleigh'),('Bentleigh East','Bentleigh East'),('Berwick','Berwick'),('Beveridge','Beveridge'),('Blackburn','Blackburn'),('Blind Bight','Blind Bight'),('Bonbeach','Bonbeach'),('Boronia','Boronia'),('Botanic Ridge','Botanic Ridge'),('Box Hill','Box Hill'),('Box Hill North','Box Hill North'),
('Brandon Park','Brandon Park'),('Braybrook','Braybrook'),('Brentford Square','Brentford Square'),('Briar Hill','Briar Hill'),('Brighton','Brighton'),('Brighton East','Brighton East'),('Brighton Road','Brighton Road'),('Broadmeadows','Broadmeadows'),('Brookfield','Brookfield'),('Brooklyn','Brooklyn'),('Brunswick','Brunswick'),('Brunswick East','Brunswick East'),('Brunswick South','Brunswick South'),('Bulla','Bulla'),('Bulleen','Bulleen'),('Bundoora','Bundoora'),('Bunyip','Bunyip'),('Burnley','Burnley'),('Burnside','Burnside'),('Burwood','Burwood'),('Burwood East','Burwood East'),('Calder Park','Calder Park'),('Camberwell','Camberwell'),('Camberwell East','Camberwell East'),
('Campbellfield','Campbellfield'),('Cardinia','Cardinia'),('Carlton','Carlton'),('Carlton North','Carlton North'),('Carnegie','Carnegie'),('Carrum','Carrum'),('Caulfield','Caulfield'),('Caulfield East','Caulfield East'),('Caulfield Junction','Caulfield Junction'),('Chadstone','Chadstone'),('Cheltenham','Cheltenham'),('Chirnside Park','Chirnside Park'),('Christmas Hills','Christmas Hills'),('Clarinda','Clarinda'),('Clayton','Clayton'),('Clifton Hill','Clifton Hill'),('Cockatoo','Cockatoo'),('Cocoroc','Cocoroc'),('Coldstream','Coldstream'),('Coolaroo','Coolaroo'),('Cora Lynn','Cora Lynn'),('Cotham','Cotham'),('Craigieburn','Craigieburn'),('Croydon','Croydon'),('Diamond Creek','Diamond Creek'),
('Diggers Rest','Diggers Rest'),('Dingley Village','Dingley Village'),('Docklands','Docklands'),('Doncaster','Doncaster'),('Doncaster East','Doncaster East'),('Donvale','Donvale'),('Doreen','Doreen'),('Doveton','Doveton'),('East Melbourne','East Melbourne'),('Eden Park','Eden Park'),('Elsternwick','Elsternwick'),('Eltham','Eltham'),('Endeavour Hills','Endeavour Hills'),('Epping','Epping'),('Essendon Fields','Essendon Fields'),('Fawkner','Fawkner'),('Ferntree Gully','Ferntree Gully'),('Ferny Creek','Ferny Creek'),('Fitzroy','Fitzroy'),('Flemington','Flemington'),('Footscray','Footscray'),('Fountain Gate','Fountain Gate'),('Garden City','Garden City'),('Gembrook','Gembrook'),('Gilberton','Gilberton'),
('Gilderoy','Gilderoy'),('Gladstone Park','Gladstone Park'),('Glenroy','Glenroy'),('Greenvale','Greenvale'),('Hallam','Hallam'),('Hampton','Hampton'),('Hampton Park','Hampton Park'),('Hawksburn','Hawksburn'),('Heatherton','Heatherton'),('Heathwood','Heathwood'),('Highett','Highett'),('Hoppers Crossing','Hoppers Crossing'),('Hotham Hill','Hotham Hill'),('Hughesdale','Hughesdale'),('Ivanhoe','Ivanhoe'),('Kallista','Kallista'),('Kalorama','Kalorama'),('Keilor','Keilor'),('Keilor Downs','Keilor Downs'),('Keilor East','Keilor East'),('Kew East','Kew East'),('Keysborough','Keysborough'),('Kilsyth','Kilsyth'),('Kinglake','Kinglake'),('Knox City Centre','Knox City Centre'),('Knoxfield','Knoxfield'),
('Kooyong','Kooyong'),('Kooyong','Kooyong'),('Kurunjang','Kurunjang'),('Lalor','Lalor'),('Laverton North','Laverton North'),('Lilydale','Lilydale'),('Little River','Little River'),('Lower Plenty','Lower Plenty'),('Lynbrook','Lynbrook'),('Macleod','Macleod'),('Macleod','Macleod'),('Mambourin','Mambourin'),('Maryknoll','Maryknoll'),('Melbourne','Melbourne'),('Melbourne','Melbourne'),('Melbourne','Melbourne'),('Melbourne Airport','Melbourne Airport'),('Melbourne University','Melbourne University'),('Mentone','Mentone'),('Menzies Creek','Menzies Creek'),('Mill Park','Mill Park'),('Mitcham','Mitcham'),('Monash University','Monash University'),('Monbulk','Monbulk'),('Mont Albert','Mont Albert'),
('Montmorency','Montmorency'),('Montrose','Montrose'),('Moonee Ponds','Moonee Ponds'),('Moorabbin','Moorabbin'),('Mooroolbark','Mooroolbark'),('Mount Dandenong','Mount Dandenong'),('Mount Evelyn','Mount Evelyn'),('Mount Waverley','Mount Waverley'),('Mulgrave','Mulgrave'),('Narre Warren East','Narre Warren East'),('Newport','Newport'),('Noble Park','Noble Park'),('North Warrandyte','North Warrandyte'),('Northcote','Northcote'),('Oaklands Junction','Oaklands Junction'),('Oakleigh South','Oakleigh South'),('Officer','Officer'),('Olinda','Olinda'),('Pakenham','Pakenham'),('Pakenham','Pakenham'),('Panton Hill','Panton Hill'),('Park Orchards','Park Orchards'),('Pascoe Vale','Pascoe Vale'),
('Plenty','Plenty'),('Plumpton','Plumpton'),('Plumpton','Plumpton'),('Prahran','Prahran'),('Reservoir','Reservoir'),('Rowville','Rowville'),('Sandown Village','Sandown Village'),('Sandringham','Sandringham'),('Sassafras','Sassafras'),('Scoresby','Scoresby'),('Sherbrooke','Sherbrooke'),('Silvan','Silvan'),('Smiths Gully','Smiths Gully'),('Somerton','Somerton'),('South Melbourne','South Melbourne'),('South Morang','South Morang'),('South Wharf','South Wharf'),('South Yarra','South Yarra'),('St Andrews','St Andrews'),('St Kilda','St Kilda'),('Sunbury ','Sunbury '),('Templestowe','Templestowe'),('Templestowe Lower','Templestowe Lower'),('The Basin','The Basin'),('The Patch','The Patch'),
('Thomastown','Thomastown'),('Thornbury','Thornbury'),('Tremont','Tremont'),('Tynong','Tynong'),('University Of Melbourne','University Of Melbourne'),('Upwey','Upwey'),('Vermont','Vermont'),('Wattle Glen','Wattle Glen'),('West Melbourne','West Melbourne'),('Williams Landing','Williams Landing'),('Williamstown','Williamstown'),('Wollert','Wollert'),('Wonga Park','Wonga Park'),('Woodstock','Woodstock'),('Yan Yean','Yan Yean'),('Yarrambat','Yarrambat'),('Yarraville','Yarraville'),
('Alexandria','Alexandria'),('Annandale','Annandale'),('Arncliffe','Arncliffe'),('Artarmon','Artarmon'),('Ashfield','Ashfield'),('Auburn','Auburn'),('Avalon','Avalon'),('Balgowlah','Balgowlah'),('Balmain','Balmain'),('Bankstown','Bankstown'),('Baulkham Hills','Baulkham Hills'),('Bayview','Bayview'),('Beecroft','Beecroft'),('Belfield','Belfield'),('Bellevue Hill','Bellevue Hill'),('Belmore','Belmore'),('Belrose','Belrose'),('Berowra Waters','Berowra Waters'),('Beverly Hills','Beverly Hills'),('Bexley','Bexley'),('Blacktown','Blacktown'),('Blakehurst','Blakehurst'),('Bondi','Bondi'),('Bondi Junction','Bondi Junction'),('Botany','Botany'),('Brookvale','Brookvale'),('Burwood','Burwood'),('Camden','Camden'),('Cammeray','Cammeray'),('Campbelltown','Campbelltown'),('Camperdown','Camperdown'),('Campsie','Campsie'),('Canterbury','Canterbury'),('Caringbah','Caringbah'),('Carlingford','Carlingford'),('Carlton','Carlton'),('Castle Hill','Castle Hill'),('Castlereagh','Castlereagh'),('Chatswood','Chatswood'),('Cherrybrook','Cherrybrook'),('Chester Hill','Chester Hill'),('Chippendale','Chippendale'),('Chullora','Chullora'),('Collaroy','Collaroy'),('Concord','Concord'),('Coogee','Coogee'),('Cremorne','Cremorne'),('Cronulla','Cronulla'),('Crows Nest','Crows Nest'),('Croydon','Croydon'),('Croydon Park','Croydon Park'),('Dee Why','Dee Why'),('Double Bay','Double Bay'),('Drummoyne','Drummoyne'),
('Dulwich Hill','Dulwich Hill'),('Dural','Dural'),('Earlwood','Earlwood'),('East Hills','East Hills'),('Eastwood','Eastwood'),('Edgecliff','Edgecliff'),('Enfield','Enfield'),('Epping','Epping'),('Ermington','Ermington'),('Erskine Park','Erskine Park'),('Erskineville','Erskineville'),('Fairfield','Fairfield'),('Five Dock','Five Dock'),('Forestville','Forestville'),('Frenchs Forest','Frenchs Forest'),('Galston','Galston'),('Georges Hall','Georges Hall'),('Gladesville','Gladesville'),('Glebe','Glebe'),('Glendenning','Glendenning'),('Glenorie','Glenorie'),('Gordon','Gordon'),('Granville','Granville'),('Gymea','Gymea'),('Haberfield','Haberfield'),('Harbord','Harbord'),('Heathcote','Heathcote'),('Homebush','Homebush'),('Homebush Bay','Homebush Bay'),('Hornsby','Hornsby'),('Hoxton Park','Hoxton Park'),('Hunters Hill','Hunters Hill'),('Hurstville','Hurstville'),('Ingleburn','Ingleburn'),('Jannali','Jannali'),('Kellyville','Kellyville'),('Kensington','Kensington'),('Kenthurst','Kenthurst'),('Killara','Killara'),('Kings Cross','Kings Cross'),('Kingsford','Kingsford'),('Kingsgrove','Kingsgrove'),('Kingswood','Kingswood'),('Kogarah','Kogarah'),('Kurnell','Kurnell'),('Kurrajong','Kurrajong'),('Lakemba','Lakemba'),('Lane Cove','Lane Cove'),('Lansvale','Lansvale'),('Leichhardt','Leichhardt'),('Lidcombe','Lidcombe'),('Lindfield','Lindfield'),('Liverpool','Liverpool'),('Manly','Manly'),
('Marrickville','Marrickville'),('Mascot','Mascot'),('Matraville','Matraville'),('Meadowbank','Meadowbank'),('Menai','Menai'),('Merrylands','Merrylands'),('Milperra','Milperra'),('Milsons Point','Milsons Point'),('Minchinbury','Minchinbury'),('Minto','Minto'),('Miranda','Miranda'),('Mona Vale','Mona Vale'),('Mortdale','Mortdale'),('Mosman','Mosman'),('Mount Colah','Mount Colah'),('Mount Kuring-gai','Mount Kuring-gai'),('Mulgoa','Mulgoa'),('Narellan','Narellan'),('Narrabeen','Narrabeen'),('Neutral Bay','Neutral Bay'),('Newport','Newport'),('Newtown','Newtown'),('North Richmond','North Richmond'),('North Rocks','North Rocks'),('North Ryde','North Ryde'),('North Sydney','North Sydney'),('Northbridge','Northbridge'),('Northmead','Northmead'),('Oyster Bay','Oyster Bay'),('Paddington','Paddington'),('Padstow','Padstow'),('Pagewood','Pagewood'),('Parklea','Parklea'),('Parramatta','Parramatta'),('Peakhurst','Peakhurst'),('Pennant Hills','Pennant Hills'),('Penrith','Penrith'),('Penshurst','Penshurst'),('Petersham','Petersham'),('Punchbowl','Punchbowl'),('Pymble','Pymble'),('Pyrmont','Pyrmont'),('Quakers Hill','Quakers Hill'),('Randwick','Randwick'),('Redfern','Redfern'),('Regents Park','Regents Park'),('Revesby','Revesby'),('Rhodes','Rhodes'),('Richmond','Richmond'),('Riverstone','Riverstone'),('Rockdale','Rockdale'),('Rooty Hill','Rooty Hill'),('Rose Bay','Rose Bay'),
('Rosebery','Rosebery'),('Roseville','Roseville'),('Rozelle','Rozelle'),('Rydalmere','Rydalmere'),('Ryde','Ryde'),('Sans Souci','Sans Souci'),('Seaforth','Seaforth'),('Seven Hills','Seven Hills'),('Silverdale','Silverdale'),('Silverwater','Silverwater'),('Smithfield/W.Park','Smithfield/W.Park'),('St Ives','St Ives'),('St Johns Park','St Johns Park'),('St Marys','St Marys'),('St Peters','St Peters'),('Stanmore','Stanmore'),('Strathfield','Strathfield'),('Summer Hill','Summer Hill'),('Surry Hills','Surry Hills'),('Sutherland','Sutherland'),('Sydney City','Sydney City'),('Sydney Markets','Sydney Markets'),('Sylvania','Sylvania'),('Telopea','Telopea'),('Terrey Hills','Terrey Hills'),('Toongabbie','Toongabbie'),('Turramurra','Turramurra'),('Ultimo','Ultimo'),('Vaucluse','Vaucluse'),('Villawood','Villawood'),('W. Pennant Hills','W. Pennant Hills'),('Wahroona','Wahroona'),('Warriewood','Warriewood'),('Waterloo','Waterloo'),('Waverley','Waverley'),('Wentworthville','Wentworthville'),('Willoughby','Willoughby'),('Windsor','Windsor'),('Woollahra','Woollahra'),('Yagoona','Yagoona'),('Yennora','Yennora'),
)

Country = (('Australia', 'Australia'),('China', 'China'),('United State','United State'))

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
            raise forms.ValidationError("The expiration date you entered is in the past.")
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
    phone_number = forms.CharField(max_length=15)

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
            price = float(self.cleaned_data["guest_number"])*float(experience.price)*1.25 + 2.40
 
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
                booking = Booking(user = user, experience= experience, guest_number = self.cleaned_data['guest_number'], 
                                  datetime = local_timezone.localize(datetime(date.year, date.month, date.day, time.hour, time.minute)).astimezone(pytz.timezone("UTC")),
                                  submitted_datetime = datetime.utcnow(), status="paid")
                booking.save()
                #add the user to the guest list
                if user not in experience.guests.all():
                    experience.guests.add(user)

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
                          Aliases.objects.get(destination__startswith=user.email).mail,
                            [Aliases.objects.get(destination__startswith=experience.hosts.all()[0].email).mail], fail_silently=False,
                            html_message=loader.render_to_string('email_booking_requested_host.html', 
                                                                 {'experience': experience,
                                                                  'booking':booking,
                                                                  'user_first_name':user.first_name,
                                                                  'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                                  'accept_url': settings.DOMAIN_NAME + '/booking/' + str(booking.id) + '?accept=yes',
                                                                  'reject_url': settings.DOMAIN_NAME + '/booking/' + str(booking.id) + '?accept=no'}))
                # send an email to the traveler
                send_mail('[Tripalocal] You booking request is sent to the host', '', 
                          Aliases.objects.get(destination__startswith=experience.hosts.all()[0].email).mail,
                            [Aliases.objects.get(destination__startswith=user.email).mail], fail_silently=False, 
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

class UserSignupForm(forms.Form):
    def signup(self, request, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        new_registereduser = RegisteredUser(user_id = user.id)
        new_registereduser.save()

        username = user.username

        new_email = Users(id = username + "@" + settings.DOMAIN_NAME,
                          name = username,
                          maildir = username + "/")
        new_email.save()

        new_alias = Aliases(mail = new_email.id, destination = user.email + ", " + new_email.id)
        new_alias.save()

        with open('canonical', 'a') as f:
            f.write(user.email + " " + new_email.id + "\n")
            f.close()

        #subprocess.Popen(['sudo','postmap','/etc/postfix/canonical'])