from datetime import *
from calendar import monthrange
import string
import json
import random
from dateutil.tz import tzlocal

from django import forms
from bootstrap3_datetime.widgets import DateTimePicker
from django.utils.safestring import mark_safe
from experiences.constant import *
from experiences.tasks import schedule_sms, schedule_sms_if_no_confirmed
from experiences.constant import *
from experiences.models import *
from Tripalocal_V1 import settings
from experiences.telstra_sms_api import send_sms
import pytz
from django.template import loader
from tripalocal_messages.models import Aliases
from django.utils.translation import ugettext as _
from django.db import connections
from app.models import RegisteredUser
from post_office import mail

Type = (('PRIVATE', _('Private')),('NONPRIVATE', _('NonPrivate')),('RECOMMENDED', _('Recommended')),)

Location = (('Melbourne', _('Melbourne, VIC')),('Sydney', _('Sydney, NSW')),('Brisbane', _('Brisbane, QLD')),('Cairns',_('Cairns, QLD')),
            ('Goldcoast',_('Gold coast, QLD')),('Hobart',_('Hobart, TAS')), ('Adelaide', _('Adelaide, SA')),('GRSA', _('Greater South Australia')),
            ('GRVIC', _('Greater Victoria')),('GRNSW', _('Greater New South Wales')),('GRQLD', _('Greater Queensland')),
            ('Darwin',_('Darwin, NT')),('Alicesprings',_('Alice Springs, NT')),('GRNT', _('Greater Northern Territory')),
            ('Christchurch',_('Christchurch, NZ')),('Queenstown',_('Queenstown, NZ')),('Auckland', _('Auckland, NZ')),('Wellington', _('Wellington, NZ')),)


Location_reverse = ((_('Melbourne'), 'Melbourne'), (_('Sydney'), 'Sydney'),
                    (_('Brisbane'), 'Brisbane'), (_('Cairns'), 'Cairns'),
                    (_('Gold Coast'), 'Goldcoast'), (_('Hobart'), 'Hobart'),
                    (_('Adelaide'), 'Adelaide'), (_('Darwin'), 'Darwin'),
                    (_('Alice Springs'), 'Alicesprings'),
                    (_('Christchurch'), 'Christchurch'), (_('Queenstown'), 'Queenstown'),
                    (_('Auckland'), 'Auckland'), (_('Wellington'), 'Wellington'),)

#                    (_('Greater South Australia'), 'GRSA'),(_('Greater Victoria'), 'GRVIC'),
#                    (_('Greater New South Wales'), 'GRNSW'),(_('Greater Queensland'), 'GRQLD'),
#                    (_('Greater Northern Territory'), 'GRNT'),

Locations = [(_('Australia'), [('Melbourne', _('Melbourne'), _('Victoria')), ('Sydney', _('Sydney'), _('New South Wales')),
                           ('Brisbane', _('Brisbane'), _('Queensland')), ('Cairns', _('Cairns'), _('Queensland')),
                           ('Goldcoast', _('Gold Coast'), _('Queensland')), ('Hobart', _('Hobart'), _('Tasmania')),
                           ('Adelaide', _('Adelaide'), _('South Australia')),
                           ('Darwin', _('Darwin'), _('Northern Territory')),
                           ('Alicesprings', _('Alice Springs'), _('Northern Territory'))]),
             (_('New Zealand'), [('Christchurch', _('Christchurch'), _('Canterbury')),
                             ('Queenstown', _('Queenstown'), _('Otago')),
                             ('Auckland', _('Auckland'), _('Auckland')),
                             ('Wellington', _('Wellington'), _('Wellington'))])]

Language=(('None',''),('english;','English'),('english;mandarin;','English+Chinese'),)#('english;translation','English+Chinese translation'),

Repeat_Cycle = (('Weekly', 'Weekly'), ('Daily', 'Daily'), ('Monthly', 'Monthly'),)

Repeat_Frequency = (('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),
    ('6', '6'),('7', '7'),('8', '8'),('9', '9'),('10', '10'),)

Guest_Number = (('1', '1' + _(' Guest')),('2', '2' + _(' Guests')),('3', '3' + _(' Guests')),('4', '4' + _(' Guests')),('5', '5' + _(' Guests')),
                ('6', '6' + _(' Guests')),('7', '7' + _(' Guests')),('8', '8' + _(' Guests')),('9', '9' + _(' Guests')),('10', '10' + _(' Guests')),)

Guest_Number_Min = (('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),('6', '6'),('7', '7'),('8', '8'),('9', '9'),('10', '10'),)

Guest_Number_Max = (('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),('6', '6'),('7', '7'),('8', '8'),('9', '9'),('10', '10'),
                    ('11', '11'),('12', '12'),('13', '13'),('14', '14'),('15', '15'),('16', '16'),('17', '17'),('18', '18'),('19', '19'),('20', '20'),)

Duration = (('1.0', '1 hour'),('1.5', '1.5 hours'),('2.0', '2 hours'),('2.5', '2.5 hours'),('3.0', '3 hours'),('4.0', '4 hours'),('5.0', '5 hours'),('6.0', '6 hours'),('7.0', '7 hours'),('8.0', '8 hours'),('9.0', '9 hours'),('10.0', '10 hours'),
('11.0', '11 hours'),('12.0', '12 hours'),('24.0', '1 day'),('48.0', '2 days'),('72.0', '3 days'),('96.0', '4 days'),('120.0', '5 days'),('144.0', '6 days'),('168.0', '7 days'),('192.0', '8 days'),
('216.0', '9 days'),('240.0', '10 days'))

Included = (('Yes', ''),('No', ''),)

Suburbs = (('Melbourne', _('Melbourne, VIC')),('Sydney', _('Sydney, NSW')),('Brisbane', _('Brisbane, QLD')),('Cairns',_('Cairns, QLD')),
            ('Goldcoast',_('Gold coast, QLD')),('Hobart',_('Hobart, TAS')), ('Adelaide', _('Adelaide, SA')),('GRSA', _('Greater South Australia')),
            ('GRVIC', _('Greater Victoria')),('GRNSW', _('Greater New South Wales')),('GRQLD', _('Greater Queensland')),
            ('Darwin',_('Darwin, NT')),('Alicesprings',_('Alice Springs, NT')),('GRNT', _('Greater Northern Territory')),
            ('Christchurch',_('Christchurch, NZ')),('Queenstown',_('Queenstown, NZ')),('Auckland', _('Auckland, NZ')),('Wellington', _('Wellington, NZ')),)

Currency = (('AUD',_('AUD')),('NZD',_('NZD')),) #('CNY',_('CNY')),
DollarSign = {'AUD':'$','NZD':'$'} #'CNY':'￥',
CurrencyCode = {'AUD':'036','NZD':'554'}

Status = (('Submitted', 'Pending Review'), ('Listed','Listed'), ('Unlisted','Unlisted'))

PRIVATE_IPS_PREFIX = ('10.', '172.', '192.', '127.')

Country = (('Australia', 'Australia'),('China', 'China'),('Afghanistan', 'Afghanistan'),('Albania', 'Albania'),('Algeria', 'Algeria'),('Andorra', 'Andorra'),('Angola', 'Angola'),('Antigua and Barbuda', 'Antigua and Barbuda'),('Argentina', 'Argentina'),('Armenia', 'Armenia'),('Aruba', 'Aruba'),('Austria', 'Austria'),('Azerbaijan', 'Azerbaijan'),('Bahamas', 'Bahamas'),('Bahrain', 'Bahrain'),('Bangladesh', 'Bangladesh'),('Barbados', 'Barbados'),('Belarus', 'Belarus'),('Belgium', 'Belgium'),('Belize', 'Belize'),('Benin', 'Benin'),('Bhutan', 'Bhutan'),('Bolivia', 'Bolivia'),('Bosnia and Herzegovina', 'Bosnia and Herzegovina'),('Botswana', 'Botswana'),('Brazil', 'Brazil'),('Brunei ', 'Brunei '),('Bulgaria', 'Bulgaria'),('Burkina Faso', 'Burkina Faso'),
('Burma', 'Burma'),('Burundi', 'Burundi'),('Cambodia', 'Cambodia'),('Cameroon', 'Cameroon'),('Canada', 'Canada'),('Cape Verde', 'Cape Verde'),('Central African Republic', 'Central African Republic'),('Chad', 'Chad'),('Chile', 'Chile'),('Colombia', 'Colombia'),('Comoros', 'Comoros'),('Congo, Democratic Republic of the', 'Congo, Democratic Republic of the'),('Congo, Republic of the', 'Congo, Republic of the'),('Costa Rica', 'Costa Rica'),('Cote dIvoire', 'Cote dIvoire'),('Croatia', 'Croatia'),('Cuba', 'Cuba'),('Curacao', 'Curacao'),('Cyprus', 'Cyprus'),('Czech Republic', 'Czech Republic'),('Denmark', 'Denmark'),('Djibouti', 'Djibouti'),('Dominica', 'Dominica'),('Dominican Republic', 'Dominican Republic'),
('East Timor', 'East Timor'),('Ecuador', 'Ecuador'),('Egypt', 'Egypt'),('El Salvador', 'El Salvador'),('Equatorial Guinea', 'Equatorial Guinea'),('Eritrea', 'Eritrea'),('Estonia', 'Estonia'),('Ethiopia', 'Ethiopia'),('Fiji', 'Fiji'),('Finland', 'Finland'),('France', 'France'),('Gabon', 'Gabon'),('Gambia', 'Gambia'),('Georgia', 'Georgia'),('Germany', 'Germany'),('Ghana', 'Ghana'),('Greece', 'Greece'),('Grenada', 'Grenada'),('Guatemala', 'Guatemala'),('Guinea', 'Guinea'),('Guinea-Bissau', 'Guinea-Bissau'),('Guyana', 'Guyana'),('Haiti', 'Haiti'),('Holy See', 'Holy See'),('Honduras', 'Honduras'),('Hong Kong, China', 'Hong Kong, China'),('Hungary', 'Hungary'),('Iceland', 'Iceland'),('India', 'India'),('Indonesia', 'Indonesia'),
('Iran', 'Iran'),('Iraq', 'Iraq'),('Ireland', 'Ireland'),('Israel', 'Israel'),('Italy', 'Italy'),('Jamaica', 'Jamaica'),('Japan', 'Japan'),('Jordan', 'Jordan'),('Kazakhstan', 'Kazakhstan'),('Kenya', 'Kenya'),('Kiribati', 'Kiribati'),('Korea, North', 'Korea, North'),('Korea, South', 'Korea, South'),('Kosovo', 'Kosovo'),('Kuwait', 'Kuwait'),('Kyrgyzstan', 'Kyrgyzstan'),('Laos', 'Laos'),('Latvia', 'Latvia'),('Lebanon', 'Lebanon'),('Lesotho', 'Lesotho'),('Liberia', 'Liberia'),('Libya', 'Libya'),('Liechtenstein', 'Liechtenstein'),('Lithuania', 'Lithuania'),('Luxembourg', 'Luxembourg'),('Macau, China', 'Macau, China'),('Macedonia', 'Macedonia'),('Madagascar', 'Madagascar'),('Malawi', 'Malawi'),('Malaysia', 'Malaysia'),
('Maldives', 'Maldives'),('Mali', 'Mali'),('Malta', 'Malta'),('Marshall Islands', 'Marshall Islands'),('Mauritania', 'Mauritania'),('Mauritius', 'Mauritius'),('Mexico', 'Mexico'),('Micronesia', 'Micronesia'),('Moldova', 'Moldova'),('Monaco', 'Monaco'),('Mongolia', 'Mongolia'),('Montenegro', 'Montenegro'),('Morocco', 'Morocco'),('Mozambique', 'Mozambique'),('Namibia', 'Namibia'),('Nauru', 'Nauru'),('Nepal', 'Nepal'),('Netherlands', 'Netherlands'),('Netherlands Antilles', 'Netherlands Antilles'),('New Zealand', 'New Zealand'),('Nicaragua', 'Nicaragua'),('Niger', 'Niger'),('Nigeria', 'Nigeria'),('North Korea', 'North Korea'),('Norway', 'Norway'),('Oman', 'Oman'),('Pakistan', 'Pakistan'),('Palau', 'Palau'),
('Palestinian Territories', 'Palestinian Territories'),('Panama', 'Panama'),('Papua New Guinea', 'Papua New Guinea'),('Paraguay', 'Paraguay'),('Peru', 'Peru'),('Philippines', 'Philippines'),('Poland', 'Poland'),('Portugal', 'Portugal'),('Qatar', 'Qatar'),('Romania', 'Romania'),('Russia', 'Russia'),('Rwanda', 'Rwanda'),('Saint Kitts and Nevis', 'Saint Kitts and Nevis'),('Saint Lucia', 'Saint Lucia'),('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'),('Samoa ', 'Samoa '),('San Marino', 'San Marino'),('Sao Tome and Principe', 'Sao Tome and Principe'),('Saudi Arabia', 'Saudi Arabia'),('Senegal', 'Senegal'),('Serbia', 'Serbia'),('Seychelles', 'Seychelles'),('Sierra Leone', 'Sierra Leone'),('Singapore', 'Singapore'),
('Sint Maarten', 'Sint Maarten'),('Slovakia', 'Slovakia'),('Slovenia', 'Slovenia'),('Solomon Islands', 'Solomon Islands'),('Somalia', 'Somalia'),('South Africa', 'South Africa'),('South Korea', 'South Korea'),('South Sudan', 'South Sudan'),('Spain ', 'Spain '),('Sri Lanka', 'Sri Lanka'),('Sudan', 'Sudan'),('Suriname', 'Suriname'),('Swaziland ', 'Swaziland '),('Sweden', 'Sweden'),('Switzerland', 'Switzerland'),('Syria', 'Syria'),('Taiwan, China', 'Taiwan, China'),('Tajikistan', 'Tajikistan'),('Tanzania', 'Tanzania'),('Thailand ', 'Thailand '),('Timor-Leste', 'Timor-Leste'),('Togo', 'Togo'),('Tonga', 'Tonga'),('Trinidad and Tobago', 'Trinidad and Tobago'),('Tunisia', 'Tunisia'),('Turkey', 'Turkey'),('Turkmenistan', 'Turkmenistan'),
('Tuvalu', 'Tuvalu'),('Uganda', 'Uganda'),('Ukraine', 'Ukraine'),('United Arab Emirates', 'United Arab Emirates'),('United Kingdom', 'United Kingdom'),('Uruguay', 'Uruguay'),('Uzbekistan', 'Uzbekistan'),('Vanuatu', 'Vanuatu'),('Venezuela', 'Venezuela'),('Vietnam', 'Vietnam'),('Yemen', 'Yemen'),('Zambia', 'Zambia'),('Zimbabwe ', 'Zimbabwe '),)

Tags = "Food & wine, Education, History & culture, Architecture, For couples, Photography worthy, Livability research, Outdoor & nature, Shopping, Sports & leisure, Extreme fun, Events, Health & beauty"

if settings.LANGUAGE_CODE.lower()=="zh-cn":
    Country = (('China', 'China'),('Australia', 'Australia'),('Afghanistan', 'Afghanistan'),('Albania', 'Albania'),('Algeria', 'Algeria'),('Andorra', 'Andorra'),('Angola', 'Angola'),('Antigua and Barbuda', 'Antigua and Barbuda'),('Argentina', 'Argentina'),('Armenia', 'Armenia'),('Aruba', 'Aruba'),('Austria', 'Austria'),('Azerbaijan', 'Azerbaijan'),('Bahamas', 'Bahamas'),('Bahrain', 'Bahrain'),('Bangladesh', 'Bangladesh'),('Barbados', 'Barbados'),('Belarus', 'Belarus'),('Belgium', 'Belgium'),('Belize', 'Belize'),('Benin', 'Benin'),('Bhutan', 'Bhutan'),('Bolivia', 'Bolivia'),('Bosnia and Herzegovina', 'Bosnia and Herzegovina'),('Botswana', 'Botswana'),('Brazil', 'Brazil'),('Brunei ', 'Brunei '),('Bulgaria', 'Bulgaria'),('Burkina Faso', 'Burkina Faso'),
('Burma', 'Burma'),('Burundi', 'Burundi'),('Cambodia', 'Cambodia'),('Cameroon', 'Cameroon'),('Canada', 'Canada'),('Cape Verde', 'Cape Verde'),('Central African Republic', 'Central African Republic'),('Chad', 'Chad'),('Chile', 'Chile'),('Colombia', 'Colombia'),('Comoros', 'Comoros'),('Congo, Democratic Republic of the', 'Congo, Democratic Republic of the'),('Congo, Republic of the', 'Congo, Republic of the'),('Costa Rica', 'Costa Rica'),('Cote dIvoire', 'Cote dIvoire'),('Croatia', 'Croatia'),('Cuba', 'Cuba'),('Curacao', 'Curacao'),('Cyprus', 'Cyprus'),('Czech Republic', 'Czech Republic'),('Denmark', 'Denmark'),('Djibouti', 'Djibouti'),('Dominica', 'Dominica'),('Dominican Republic', 'Dominican Republic'),
('East Timor', 'East Timor'),('Ecuador', 'Ecuador'),('Egypt', 'Egypt'),('El Salvador', 'El Salvador'),('Equatorial Guinea', 'Equatorial Guinea'),('Eritrea', 'Eritrea'),('Estonia', 'Estonia'),('Ethiopia', 'Ethiopia'),('Fiji', 'Fiji'),('Finland', 'Finland'),('France', 'France'),('Gabon', 'Gabon'),('Gambia', 'Gambia'),('Georgia', 'Georgia'),('Germany', 'Germany'),('Ghana', 'Ghana'),('Greece', 'Greece'),('Grenada', 'Grenada'),('Guatemala', 'Guatemala'),('Guinea', 'Guinea'),('Guinea-Bissau', 'Guinea-Bissau'),('Guyana', 'Guyana'),('Haiti', 'Haiti'),('Holy See', 'Holy See'),('Honduras', 'Honduras'),('Hong Kong, China', 'Hong Kong, China'),('Hungary', 'Hungary'),('Iceland', 'Iceland'),('India', 'India'),('Indonesia', 'Indonesia'),
('Iran', 'Iran'),('Iraq', 'Iraq'),('Ireland', 'Ireland'),('Israel', 'Israel'),('Italy', 'Italy'),('Jamaica', 'Jamaica'),('Japan', 'Japan'),('Jordan', 'Jordan'),('Kazakhstan', 'Kazakhstan'),('Kenya', 'Kenya'),('Kiribati', 'Kiribati'),('Korea, North', 'Korea, North'),('Korea, South', 'Korea, South'),('Kosovo', 'Kosovo'),('Kuwait', 'Kuwait'),('Kyrgyzstan', 'Kyrgyzstan'),('Laos', 'Laos'),('Latvia', 'Latvia'),('Lebanon', 'Lebanon'),('Lesotho', 'Lesotho'),('Liberia', 'Liberia'),('Libya', 'Libya'),('Liechtenstein', 'Liechtenstein'),('Lithuania', 'Lithuania'),('Luxembourg', 'Luxembourg'),('Macau, China', 'Macau, China'),('Macedonia', 'Macedonia'),('Madagascar', 'Madagascar'),('Malawi', 'Malawi'),('Malaysia', 'Malaysia'),
('Maldives', 'Maldives'),('Mali', 'Mali'),('Malta', 'Malta'),('Marshall Islands', 'Marshall Islands'),('Mauritania', 'Mauritania'),('Mauritius', 'Mauritius'),('Mexico', 'Mexico'),('Micronesia', 'Micronesia'),('Moldova', 'Moldova'),('Monaco', 'Monaco'),('Mongolia', 'Mongolia'),('Montenegro', 'Montenegro'),('Morocco', 'Morocco'),('Mozambique', 'Mozambique'),('Namibia', 'Namibia'),('Nauru', 'Nauru'),('Nepal', 'Nepal'),('Netherlands', 'Netherlands'),('Netherlands Antilles', 'Netherlands Antilles'),('New Zealand', 'New Zealand'),('Nicaragua', 'Nicaragua'),('Niger', 'Niger'),('Nigeria', 'Nigeria'),('North Korea', 'North Korea'),('Norway', 'Norway'),('Oman', 'Oman'),('Pakistan', 'Pakistan'),('Palau', 'Palau'),
('Palestinian Territories', 'Palestinian Territories'),('Panama', 'Panama'),('Papua New Guinea', 'Papua New Guinea'),('Paraguay', 'Paraguay'),('Peru', 'Peru'),('Philippines', 'Philippines'),('Poland', 'Poland'),('Portugal', 'Portugal'),('Qatar', 'Qatar'),('Romania', 'Romania'),('Russia', 'Russia'),('Rwanda', 'Rwanda'),('Saint Kitts and Nevis', 'Saint Kitts and Nevis'),('Saint Lucia', 'Saint Lucia'),('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'),('Samoa ', 'Samoa '),('San Marino', 'San Marino'),('Sao Tome and Principe', 'Sao Tome and Principe'),('Saudi Arabia', 'Saudi Arabia'),('Senegal', 'Senegal'),('Serbia', 'Serbia'),('Seychelles', 'Seychelles'),('Sierra Leone', 'Sierra Leone'),('Singapore', 'Singapore'),
('Sint Maarten', 'Sint Maarten'),('Slovakia', 'Slovakia'),('Slovenia', 'Slovenia'),('Solomon Islands', 'Solomon Islands'),('Somalia', 'Somalia'),('South Africa', 'South Africa'),('South Korea', 'South Korea'),('South Sudan', 'South Sudan'),('Spain ', 'Spain '),('Sri Lanka', 'Sri Lanka'),('Sudan', 'Sudan'),('Suriname', 'Suriname'),('Swaziland ', 'Swaziland '),('Sweden', 'Sweden'),('Switzerland', 'Switzerland'),('Syria', 'Syria'),('Taiwan, China', 'Taiwan, China'),('Tajikistan', 'Tajikistan'),('Tanzania', 'Tanzania'),('Thailand ', 'Thailand '),('Timor-Leste', 'Timor-Leste'),('Togo', 'Togo'),('Tonga', 'Tonga'),('Trinidad and Tobago', 'Trinidad and Tobago'),('Tunisia', 'Tunisia'),('Turkey', 'Turkey'),('Turkmenistan', 'Turkmenistan'),
('Tuvalu', 'Tuvalu'),('Uganda', 'Uganda'),('Ukraine', 'Ukraine'),('United Arab Emirates', 'United Arab Emirates'),('United Kingdom', 'United Kingdom'),('Uruguay', 'Uruguay'),('Uzbekistan', 'Uzbekistan'),('Vanuatu', 'Vanuatu'),('Venezuela', 'Venezuela'),('Vietnam', 'Vietnam'),('Yemen', 'Yemen'),('Zambia', 'Zambia'),('Zimbabwe ', 'Zimbabwe '),)
    Tags = "美食美酒, 名校游学, 历史人文, 经典建筑, 蜜月旅拍, 风光摄影, 移民考察, 亲子夏令营, 户外探险, 购物扫货, 运动休闲, 领路人自驾, 刺激享乐, 赛事庆典, 美容保健, 私人团"

#from http://stackoverflow.com/questions/16773579/customize-radio-buttons-in-django
class HorizRadioRenderer(forms.RadioSelect.renderer):
    """ this overrides widget method to put radio buttons horizontally
        instead of vertically.
    """
    def render(self):
            """Outputs radios"""
            return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))

class ExperienceForm(forms.Form):
    id = forms.CharField(max_length=10, required=False)
    title = forms.CharField(max_length=100, required=False)
    duration = forms.ChoiceField(choices=Duration, required=False)
    location = forms.ChoiceField(choices=Suburbs, required=False)
    changed_steps = forms.CharField(max_length=100, required=False)
    user_id = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(ExperienceForm, self).__init__(*args, **kwargs)
        self.fields['id'].widget.attrs['readonly'] = True
        self.fields['id'].widget = forms.HiddenInput()
        self.fields['changed_steps'].widget.attrs['readonly'] = True
        self.fields['changed_steps'].widget = forms.HiddenInput()

class ExperienceCalendarForm(forms.Form):
    id = forms.CharField(max_length=10, required=False)
    changed_steps = forms.CharField(max_length=100, required=False)
    start_datetime = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    end_datetime = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))

    blockout_start_datetime_1 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_1 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_1 = forms.BooleanField(required=False)
    blockout_repeat_cycle_1 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    blockout_repeat_frequency_1 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    blockout_repeat_end_date_1 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    blockout_repeat_extra_information_1 = forms.CharField(required=False, max_length=70)

    blockout_start_datetime_2 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_2 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_2 = forms.BooleanField(required=False)
    blockout_repeat_cycle_2 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    blockout_repeat_frequency_2 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    blockout_repeat_end_date_2 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    blockout_repeat_extra_information_2 = forms.CharField(required=False, max_length=70)

    blockout_start_datetime_3 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_3 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_3 = forms.BooleanField(required=False)
    blockout_repeat_cycle_3 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    blockout_repeat_frequency_3 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    blockout_repeat_end_date_3 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    blockout_repeat_extra_information_3 = forms.CharField(required=False, max_length=70)

    blockout_start_datetime_4 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_4 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_4 = forms.BooleanField(required=False)
    blockout_repeat_cycle_4 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    blockout_repeat_frequency_4 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    blockout_repeat_end_date_4 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    blockout_repeat_extra_information_4 = forms.CharField(required=False, max_length=70)

    blockout_start_datetime_5 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_5 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_5 = forms.BooleanField(required=False)
    blockout_repeat_cycle_5 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    blockout_repeat_frequency_5 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    blockout_repeat_end_date_5 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    blockout_repeat_extra_information_5 = forms.CharField(required=False, max_length=70)

    instant_booking_start_datetime_1 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_1 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_1 = forms.BooleanField(required=False)
    instant_booking_repeat_cycle_1 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    instant_booking_repeat_frequency_1 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    instant_booking_repeat_end_date_1 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    instant_booking_repeat_extra_information_1 = forms.CharField(required=False, max_length=70)

    instant_booking_start_datetime_2 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_2 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_2 = forms.BooleanField(required=False)
    instant_booking_repeat_cycle_2 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    instant_booking_repeat_frequency_2 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    instant_booking_repeat_end_date_2 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    instant_booking_repeat_extra_information_2 = forms.CharField(required=False, max_length=70)

    instant_booking_start_datetime_3 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_3 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_3 = forms.BooleanField(required=False)
    instant_booking_repeat_cycle_3 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    instant_booking_repeat_frequency_3 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    instant_booking_repeat_end_date_3 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    instant_booking_repeat_extra_information_3 = forms.CharField(required=False, max_length=70)

    instant_booking_start_datetime_4 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_4 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_4 = forms.BooleanField(required=False)
    instant_booking_repeat_cycle_4 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    instant_booking_repeat_frequency_4 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    instant_booking_repeat_end_date_4 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    instant_booking_repeat_extra_information_4 = forms.CharField(required=False, max_length=70)

    instant_booking_start_datetime_5 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_5 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_5 = forms.BooleanField(required=False)
    instant_booking_repeat_cycle_5 = forms.ChoiceField(required=False, choices=Repeat_Cycle)
    instant_booking_repeat_frequency_5 = forms.ChoiceField(required=False, choices=Repeat_Frequency)
    instant_booking_repeat_end_date_5 = forms.DateField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    instant_booking_repeat_extra_information_5 = forms.CharField(required=False, max_length=70)

    def __init__(self, *args, **kwargs):
        super(ExperienceCalendarForm, self).__init__(*args, **kwargs)
        self.fields['id'].widget.attrs['readonly'] = True
        self.fields['id'].widget = forms.HiddenInput()
        self.fields['changed_steps'].widget.attrs['readonly'] = True
        self.fields['changed_steps'].widget = forms.HiddenInput()

class ExperiencePriceForm(forms.Form):
    id = forms.CharField(max_length=10, required=False)
    changed_steps = forms.CharField(max_length=100, required=False)
    duration = forms.ChoiceField(required=False, choices=Duration)
    min_guest_number = forms.ChoiceField(required=False, choices=Guest_Number_Min)
    max_guest_number = forms.ChoiceField(required=False, choices=Guest_Number_Max)
    type = forms.ChoiceField(choices=Type, required=False)
    price = forms.DecimalField(required=False, max_digits=6, decimal_places=2, min_value=1)
    price_with_booking_fee = forms.DecimalField(required=False, max_digits=6, decimal_places=2, min_value=1)
    dynamic_price = forms.CharField(max_length=100, required=False)
    currency = forms.ChoiceField(choices=Currency, required=False)

    def __init__(self, *args, **kwargs):
        super(ExperiencePriceForm, self).__init__(*args, **kwargs)
        self.fields['id'].widget.attrs['readonly'] = True
        self.fields['id'].widget = forms.HiddenInput()
        self.fields['type'].widget.attrs['readonly'] = True
        self.fields['type'].widget = forms.HiddenInput()
        self.fields['dynamic_price'].widget.attrs['readonly'] = True
        self.fields['dynamic_price'].widget = forms.HiddenInput()
        self.fields['changed_steps'].widget.attrs['readonly'] = True
        self.fields['changed_steps'].widget = forms.HiddenInput()

class ExperienceOverviewForm(forms.Form):
    id = forms.CharField(max_length=10, required=False)
    changed_steps = forms.CharField(max_length=100, required=False)
    title = forms.CharField(required=False, max_length=100)
    title_other = forms.CharField(required = False, max_length=100)
    summary = forms.CharField(required=False, widget=forms.Textarea)
    summary_other = forms.CharField(required = False, widget=forms.Textarea)
    language = forms.CharField(required=False, max_length=100)

    def __init__(self, *args, **kwargs):
        super(ExperienceOverviewForm, self).__init__(*args, **kwargs)
        self.fields['id'].widget.attrs['readonly'] = True
        self.fields['id'].widget = forms.HiddenInput()
        self.fields['language'].widget.attrs['readonly'] = True
        self.fields['language'].widget = forms.HiddenInput()
        self.fields['changed_steps'].widget.attrs['readonly'] = True
        self.fields['changed_steps'].widget = forms.HiddenInput()

class ExperienceDetailForm(forms.Form):
    id = forms.CharField(max_length=10, required=False)
    changed_steps = forms.CharField(max_length=100, required=False)
    activity = forms.CharField(required=False, widget=forms.Textarea)
    interaction = forms.CharField(required=False, widget=forms.Textarea)
    dress_code = forms.CharField(required=False, widget=forms.Textarea)
    included_food = forms.ChoiceField(required=False, widget=forms.RadioSelect(renderer=HorizRadioRenderer), choices=Included)
    included_food_detail = forms.CharField(required = False, widget=forms.Textarea)
    included_transport = forms.ChoiceField(required=False, widget=forms.RadioSelect(renderer=HorizRadioRenderer), choices=Included)
    included_transport_detail = forms.CharField(required = False, widget=forms.Textarea)
    included_ticket = forms.ChoiceField(required=False, widget=forms.RadioSelect(renderer=HorizRadioRenderer), choices=Included)
    included_ticket_detail = forms.CharField(required = False, widget=forms.Textarea)

    activity_other = forms.CharField(required = False, widget=forms.Textarea)
    interaction_other = forms.CharField(required = False, widget=forms.Textarea)
    dress_code_other = forms.CharField(required = False, widget=forms.Textarea)
    included_food_detail_other = forms.CharField(required = False, widget=forms.Textarea)
    included_transport_detail_other = forms.CharField(required = False, widget=forms.Textarea)
    included_ticket_detail_other = forms.CharField(required = False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(ExperienceDetailForm, self).__init__(*args, **kwargs)
        self.fields['id'].widget.attrs['readonly'] = True
        self.fields['id'].widget = forms.HiddenInput()
        self.fields['changed_steps'].widget.attrs['readonly'] = True
        self.fields['changed_steps'].widget = forms.HiddenInput()

class ExperiencePhotoForm(forms.Form):
    id = forms.CharField(max_length=10, required=False)
    changed_steps = forms.CharField(max_length=100, required=False)
    experience_photo_1 = forms.ImageField(required = False)
    experience_photo_2 = forms.ImageField(required = False)
    experience_photo_3 = forms.ImageField(required = False)
    experience_photo_4 = forms.ImageField(required = False)
    experience_photo_5 = forms.ImageField(required = False)
    experience_photo_6 = forms.ImageField(required = False)
    experience_photo_7 = forms.ImageField(required = False)
    experience_photo_8 = forms.ImageField(required = False)
    experience_photo_9 = forms.ImageField(required = False)
    experience_photo_10 = forms.ImageField(required = False)
    delete_photo = forms.CharField(max_length=50, required=False)

    def __init__(self, *args, **kwargs):
        super(ExperiencePhotoForm, self).__init__(*args, **kwargs)
        self.fields['id'].widget.attrs['readonly'] = True
        self.fields['id'].widget = forms.HiddenInput()
        self.fields['changed_steps'].widget.attrs['readonly'] = True
        self.fields['changed_steps'].widget = forms.HiddenInput()
        self.fields['delete_photo'].widget.attrs['readonly'] = True
        self.fields['delete_photo'].widget = forms.HiddenInput()

class ExperienceLocationForm(forms.Form):
    id = forms.CharField(max_length=10, required=False)
    changed_steps = forms.CharField(max_length=100, required=False)
    suburb = forms.ChoiceField(required=False, choices=Suburbs)
    meetup_spot = forms.CharField(required=False, widget=forms.Textarea)
    meetup_spot_other = forms.CharField(required=False, widget=forms.Textarea)
    dropoff_spot = forms.CharField(required=False, widget=forms.Textarea)
    dropoff_spot_other = forms.CharField(required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(ExperienceLocationForm, self).__init__(*args, **kwargs)
        self.fields['id'].widget.attrs['readonly'] = True
        self.fields['id'].widget = forms.HiddenInput()
        self.fields['changed_steps'].widget.attrs['readonly'] = True
        self.fields['changed_steps'].widget = forms.HiddenInput()

class ExperienceSummaryForm(forms.Form):
    type = forms.ChoiceField(choices=Type, required=True)

    start_datetime = forms.DateTimeField(required=True, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    end_datetime = forms.DateTimeField(required=True, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_start_datetime_1 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_1 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_cycle_1 = forms.ChoiceField(choices=Repeat_Cycle)
    blockout_repeat_frequency_1 = forms.ChoiceField(choices=Repeat_Frequency)
    blockout_repeat_extra_information_1 = forms.CharField(max_length=50)
    blockout_start_datetime_2 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_2 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_cycle_2 = forms.ChoiceField(choices=Repeat_Cycle)
    blockout_repeat_frequency_2 = forms.ChoiceField(choices=Repeat_Frequency)
    blockout_repeat_extra_information_2 = forms.CharField(max_length=50)
    blockout_start_datetime_3 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_3 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_cycle_3 = forms.ChoiceField(choices=Repeat_Cycle)
    blockout_repeat_frequency_3 = forms.ChoiceField(choices=Repeat_Frequency)
    blockout_repeat_extra_information_3 = forms.CharField(max_length=50)
    blockout_start_datetime_4 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_4 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_cycle_4 = forms.ChoiceField(choices=Repeat_Cycle)
    blockout_repeat_frequency_4 = forms.ChoiceField(choices=Repeat_Frequency)
    blockout_repeat_extra_information_4 = forms.CharField(max_length=50)
    blockout_start_datetime_5 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_end_datetime_5 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    blockout_repeat_cycle_5 = forms.ChoiceField(choices=Repeat_Cycle)
    blockout_repeat_frequency_5 = forms.ChoiceField(choices=Repeat_Frequency)
    blockout_repeat_extra_information_5 = forms.CharField(max_length=50)
    instant_booking_start_datetime_1 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_1 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_cycle_1 = forms.ChoiceField(choices=Repeat_Cycle)
    instant_booking_repeat_frequency_1 = forms.ChoiceField(choices=Repeat_Frequency)
    instant_booking_repeat_extra_information_1 = forms.CharField(max_length=50)
    instant_booking_start_datetime_2 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_2 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_cycle_2 = forms.ChoiceField(choices=Repeat_Cycle)
    instant_booking_repeat_frequency_2 = forms.ChoiceField(choices=Repeat_Frequency)
    instant_booking_repeat_extra_information_2 = forms.CharField(max_length=50)
    instant_booking_start_datetime_3 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_3 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_cycle_3 = forms.ChoiceField(choices=Repeat_Cycle)
    instant_booking_repeat_frequency_3 = forms.ChoiceField(choices=Repeat_Frequency)
    instant_booking_repeat_extra_information_3 = forms.CharField(max_length=50)
    instant_booking_start_datetime_4 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_4 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_cycle_4 = forms.ChoiceField(choices=Repeat_Cycle)
    instant_booking_repeat_frequency_4 = forms.ChoiceField(choices=Repeat_Frequency)
    instant_booking_repeat_extra_information_4 = forms.CharField(max_length=50)
    instant_booking_start_datetime_5 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_end_datetime_5 = forms.DateTimeField(required=False, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    instant_booking_repeat_cycle_5 = forms.ChoiceField(choices=Repeat_Cycle)
    instant_booking_repeat_frequency_5 = forms.ChoiceField(choices=Repeat_Frequency)
    instant_booking_repeat_extra_information_5 = forms.CharField(max_length=50)

    duration = forms.ChoiceField(choices=Duration)
    min_guest_number = forms.IntegerField(required=True)
    max_guest_number = forms.IntegerField(required=True)
    price = forms.DecimalField(max_digits=6, decimal_places=2)
    price_with_booking_fee = forms.DecimalField(max_digits=6, decimal_places=2)
    included_food = forms.ChoiceField(widget=forms.RadioSelect(renderer=HorizRadioRenderer), choices=Included)
    included_food_detail = forms.CharField(required = False)
    included_transport = forms.ChoiceField(widget=forms.RadioSelect(renderer=HorizRadioRenderer), choices=Included)
    included_transport_detail = forms.CharField(required = False)
    included_ticket = forms.ChoiceField(widget=forms.RadioSelect(renderer=HorizRadioRenderer), choices=Included)
    included_ticket_detail = forms.CharField(required = False)

    title = forms.CharField()
    summary = forms.CharField(widget=forms.Textarea)

    activity = forms.CharField(widget=forms.Textarea)
    interaction = forms.CharField(widget=forms.Textarea)
    dress_code = forms.CharField(widget=forms.Textarea)

    experience_photo_1 = forms.ImageField(required = False)
    experience_photo_2 = forms.ImageField(required = False)
    experience_photo_3 = forms.ImageField(required = False)
    experience_photo_4 = forms.ImageField(required = False)
    experience_photo_5 = forms.ImageField(required = False)

    suburb = forms.ChoiceField(choices=Suburbs)
    meetup_spot = forms.CharField(widget=forms.Textarea)
    dropoff_spot = forms.CharField(widget=forms.Textarea)

class BookingForm(forms.Form):
    user_id = forms.CharField()
    experience_id = forms.CharField()
    date = forms.ChoiceField(label="")
    time = forms.ChoiceField(label="")
    guest_number = forms.ChoiceField(label="")
    status = forms.CharField(initial="Requested")

    def __init__(self, available_date, experience_id, user_id, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
        self.fields['date'] = forms.ChoiceField(choices = available_date)
        self.fields['experience_id'] = forms.CharField(initial=experience_id)
        self.fields['experience_id'].widget.attrs['readonly'] = True
        self.fields['experience_id'].widget = forms.HiddenInput()
        self.fields['user_id'] = forms.CharField(initial=user_id)
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

def check_coupon(coupon, experience_id, guest_number):

    rules = json.loads(coupon.rules)
    guest_number = int(guest_number)
    experience_id = int(experience_id)

    if "ids" in rules and experience_id not in rules["ids"]:
        result = {"valid":False,"error":"the coupon cannot be used on this experience -- id"}
        return result

    if "group_size" in rules and (guest_number % rules["group_size"] != 0):
        result = {"valid":False,"error":"the coupon cannot be used on this experience -- group size"}
        return result

    bks = Booking.objects.filter(experience_id=experience_id, coupon_id=coupon.id).exclude(status__iexact="rejected")
    bks_t = len(bks) if bks is not None else 0
    if "times" in rules and bks_t >= rules["times"]:
        result = {"valid":False,"error":"the coupon cannot be used on this experience -- times"}
        return result

    free = False
    extra_fee = 0.0
    if type(rules["extra_fee"]) == int or type(rules["extra_fee"]) == float:
        extra_fee = rules["extra_fee"]
    elif type(rules["extra_fee"]) == str and rules["extra_fee"]== "FREE":
        free = True
        result={"valid":True,"new_price":0.0}
        return result

    #not free:
    subtotal_price = 0.0
    experience = Experience.objects.get(id = experience_id)
    if experience.dynamic_price and type(experience.dynamic_price) == str:
        price = experience.dynamic_price.split(',')
        if len(price)+experience.guest_number_min-2 == experience.guest_number_max:
        #these is comma in the end, so the length is max-min+2
            if guest_number <= experience.guest_number_min:
                subtotal_price = float(experience.price) * float(experience.guest_number_min)
            else:
                subtotal_price = float(price[guest_number-experience.guest_number_min]) * float(guest_number)
        else:
            #wrong dynamic settings
            subtotal_price = float(experience.price)*float(guest_number)
    else:
        subtotal_price = float(experience.price)*float(guest_number)

    COMMISSION_PERCENT = round(experience.commission/(1-experience.commission),3)
    if extra_fee == 0.00:
        price = round(subtotal_price*(1.00+COMMISSION_PERCENT), 0)*(1.00+settings.STRIPE_PRICE_PERCENT) + settings.STRIPE_PRICE_FIXED
    elif extra_fee >= 1.00 or extra_fee <= -1.00:
        #absolute value
        price = round(subtotal_price*(1.00+COMMISSION_PERCENT)+extra_fee, 0)*(1.00+settings.STRIPE_PRICE_PERCENT) + settings.STRIPE_PRICE_FIXED
    else:
        #percentage, e.g., 30% discount --> percentage == -0.3
        price = round(subtotal_price*(1.00+COMMISSION_PERCENT), 0)*(1+extra_fee)*(1.00+settings.STRIPE_PRICE_PERCENT) + settings.STRIPE_PRICE_FIXED

    result = {"valid":True, "new_price":price}
    return result

class BookingConfirmationForm(forms.Form):
    user_id = forms.CharField()
    experience_id = forms.CharField()
    date = forms.DateField()
    time = forms.TimeField()
    guest_number = forms.IntegerField(label="People")
    status = forms.CharField(initial="Requested")
    promo_code = forms.CharField(required=False)

    card_number = CreditCardField(required=False, label="Card Number")
    expiration = CCExpField(required=False, label="Expiration")
    cvv = forms.IntegerField(required=False, label="CVV Number",
        max_value=9999, widget=forms.TextInput(attrs={'size': '4'}))

    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    street1 = forms.CharField(max_length=50, required = False)
    street2 = forms.CharField(max_length=50, required = False)
    city_town = forms.CharField(max_length=20, required = False)
    state = forms.CharField(max_length=10, required = False)
    country = forms.ChoiceField(choices=Country, required = False)
    postcode = forms.CharField(max_length=4, required = False)
    phone_number = forms.CharField(max_length=15, required=True)

    coupon_extra_information = forms.CharField(max_length=500, required=False)
    booking_extra_information = forms.CharField(widget=forms.Textarea, required=False)
    price_paid = forms.DecimalField(max_digits=6, decimal_places=2, required=False)

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
        local_timezone = pytz.timezone(settings.TIME_ZONE)

        if not self.errors and ('Refresh' not in self.data):
            stripeToken = self.data["stripeToken"] if "stripeToken" in self.data else None
            #card_number = self.cleaned_data["card_number"]
            #exp_month = self.cleaned_data["expiration"].month
            #exp_year = self.cleaned_data["expiration"].year
            #cvv = self.cleaned_data["cvv"]
            experience = AbstractExperience.objects.get(id=self.cleaned_data['experience_id'])

            extra_fee = 0.00
            free = False
            self.cleaned_data['price_paid'] = -1.0

            dt = self.cleaned_data['date']
            tm = self.cleaned_data['time']
            bk_dt = local_timezone.localize(datetime(dt.year, dt.month, dt.day, tm.hour, tm.minute)).astimezone(pytz.timezone("UTC"))
            cp = Coupon.objects.filter(promo_code__iexact = self.cleaned_data['promo_code'],
                                       end_datetime__gt = bk_dt,
                                       start_datetime__lt = bk_dt)

            if len(cp)>0:
                valid = check_coupon(cp[0], experience.id, self.cleaned_data['guest_number'])
                if valid['valid']:
                    self.cleaned_data['price_paid'] = valid['new_price']
                    rules = json.loads(cp[0].rules)
                    if type(rules["extra_fee"]) == int or type(rules["extra_fee"]) == float:
                        extra_fee = rules["extra_fee"]
                    elif type(rules["extra_fee"]) == str and rules["extra_fee"]== "FREE":
                        free = True
                else:
                    raise forms.ValidationError(valid['error'])

            user = User.objects.get(id=self.cleaned_data['user_id'])
            guest_number = int(self.cleaned_data["guest_number"])
            coupon_extra_information=self.cleaned_data['coupon_extra_information'],
            coupon=cp[0] if len(cp)>0 else None
            payment_street1 = self.cleaned_data['street1']
            payment_street2 = self.cleaned_data['street2']
            payment_city = self.cleaned_data['city_town']
            payment_state = self.cleaned_data['state']
            payment_country = self.cleaned_data['country']
            payment_postcode = self.cleaned_data['postcode']
            payment_phone_number = self.cleaned_data['phone_number']

            ids = []
            dates = []
            times = []
            ids.append(self.cleaned_data['experience_id'])
            dates.append(dt.strftime("%Y/%m/%d"))
            times.append(tm.strftime("%H"))

            if 'Stripe' in self.data or 'stripeToken' in self.data:
                booking_extra_information="Need Chinese Translation" if 'booking_extra_information' in self.cleaned_data and self.cleaned_data['booking_extra_information'] else ""
                ItineraryBookingForm.booking(ItineraryBookingForm(),ids,dates,times,user,guest_number,
                             coupon_extra_information = coupon_extra_information, coupon = coupon,
                             payment_phone_number = payment_phone_number, stripe_token = stripeToken)
            elif 'UnionPay' in self.data:
                booking_extra_information=self.cleaned_data['booking_extra_information']
                if coupon:
                    st = "paid" if valid['valid'] and valid['new_price']==0.0 else 'requested'
                    booking = Booking(user = user, experience= experience, guest_number = guest_number,
                                        datetime = bk_dt,
                                        submitted_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC), status=st,
                                        coupon_extra_information=coupon_extra_information,
                                        coupon=coupon,
                                        booking_extra_information=booking_extra_information)
                    if valid['valid'] and valid['new_price']==0.0:
                        send_booking_email_verification(booking, experience, user, instant_booking(experience,dt,tm))
                        sms_notification(booking, experience, user, self.cleaned_data['phone_number'])

                else:
                    booking = Booking(user = user, experience= experience, guest_number = guest_number,
                                        datetime = bk_dt,
                                        submitted_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC), status="requested",
                                        booking_extra_information=booking_extra_information)
                booking.save()

                if not coupon or not valid['valid'] or valid['new_price'] > 0.0:
                    payment = Payment()
                    payment.booking_id = booking.id
                    payment.phone_number = self.cleaned_data['phone_number']
                    payment.save()

                    booking.payment_id = payment.id
                    booking.save()

                #add the user to the guest list
                if user not in experience.guests.all():
                #experience.guests.add(user)
                    cursor = connections['default'].cursor()
                    cursor.execute("Insert into experiences_experience_guests (experience_id,user_id) values (%s, %s)", [experience.id, user.id])

        return cleaned

class CreateExperienceForm(forms.Form):
    id=forms.IntegerField()
    host = forms.CharField()
    host_first_name = forms.CharField()
    host_last_name = forms.CharField()
    host_image_url = forms.CharField(required = False)
    host_image = forms.ImageField(required = False)
    host_bio = forms.CharField(widget=forms.Textarea, required = False)
    language = forms.ChoiceField(choices=Language)
    #start_datetime = forms.DateTimeField(required=True, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    #end_datetime = forms.DateTimeField(required=True, widget=DateTimePicker(options={"format": "YYYY-MM-DD HH:mm"}))
    #repeat_cycle = forms.ChoiceField(choices=Repeat_Cycle)
    #repeat_frequency = forms.ChoiceField(choices=Repeat_Frequency)
    title = forms.CharField()
    summary = forms.CharField(widget=forms.Textarea)
    guest_number_min = forms.ChoiceField(choices=Guest_Number_Min)
    guest_number_max = forms.ChoiceField(choices=Guest_Number_Max)
    price = forms.DecimalField(max_digits=6, decimal_places=2)
    price_with_booking_fee = forms.DecimalField(max_digits=6, decimal_places=2)
    currency = forms.ChoiceField(choices=Currency)
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
    dropoff_spot = forms.CharField(widget=forms.Textarea)
    status = forms.ChoiceField(choices=Status)
    experience_photo_1 = forms.ImageField(required = False)
    experience_photo_2 = forms.ImageField(required = False)
    experience_photo_3 = forms.ImageField(required = False)
    experience_photo_4 = forms.ImageField(required = False)
    experience_photo_5 = forms.ImageField(required = False)
    experience_photo_6 = forms.ImageField(required = False)
    experience_photo_7 = forms.ImageField(required = False)
    experience_photo_8 = forms.ImageField(required = False)
    experience_photo_9 = forms.ImageField(required = False)
    experience_photo_10 = forms.ImageField(required = False)
    host_id_photo_1 = forms.ImageField(required = False)
    host_id_photo_2 = forms.ImageField(required = False)
    host_id_photo_3 = forms.ImageField(required = False)
    host_id_photo_4 = forms.ImageField(required = False)
    host_id_photo_5 = forms.ImageField(required = False)
    dynamic_price = forms.CharField(widget=forms.HiddenInput, required = False)
    phone_number = forms.CharField()

    def __init__(self, *args, **kwargs):
        super(CreateExperienceForm, self).__init__(*args, **kwargs)
        self.fields['host_id_photo_1'].widget.attrs['class'] = 'upload'
        self.fields['host_id_photo_2'].widget.attrs['class'] = 'upload'
        self.fields['host_id_photo_3'].widget.attrs['class'] = 'upload'
        self.fields['host_id_photo_4'].widget.attrs['class'] = 'upload'
        self.fields['host_id_photo_5'].widget.attrs['class'] = 'upload'

def email_account_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class ReviewForm(forms.ModelForm):

    comment = forms.CharField(min_length=10, max_length=200, required = False, widget=forms.Textarea)
    personal_comment = forms.CharField(min_length=10, max_length=200, required = False, widget=forms.Textarea)
    operator_comment = forms.CharField(min_length=10, max_length=200, required = False, widget=forms.Textarea)

    class Meta:
        model = Review
        fields=('rate','comment','personal_comment','operator_comment',)

class ExperienceAvailabilityForm(forms.Form):
    start_datetime = forms.DateTimeField(required=True, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    end_datetime = forms.DateTimeField(required=True, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))

SortBy=((1,_('Popularity')),(2,_('Outdoor')),(3,_('Urban')),)
class CustomItineraryForm(forms.Form):
    start_datetime = forms.DateTimeField(required=True, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    end_datetime = forms.DateTimeField(required=True, widget=DateTimePicker(options={"format": "YYYY-MM-DD"}))
    guest_number = forms.ChoiceField(choices=Guest_Number_Min, required=True)
    city = forms.CharField(widget=forms.Textarea,  required=True)
    language = forms.CharField(widget=forms.Textarea,  required=True, initial="English,Mandarin")
    tags = forms.CharField(widget=forms.Textarea, required=True, initial=Tags)
    all_tags = forms.CharField(widget=forms.Textarea, required=True, initial=Tags)
    itinerary_string = forms.CharField(widget=forms.Textarea, required=False)
    sort = forms.ChoiceField(choices=SortBy, required=True)

    def __init__(self, *args, **kwargs):
        super(CustomItineraryForm, self).__init__(*args, **kwargs)
        self.fields['start_datetime'].widget.attrs['readonly'] = True
        self.fields['start_datetime'].widget = forms.HiddenInput()
        self.fields['end_datetime'].widget.attrs['readonly'] = True
        self.fields['end_datetime'].widget = forms.HiddenInput()
        self.fields['itinerary_string'].widget.attrs['readonly'] = True
        self.fields['itinerary_string'].widget = forms.HiddenInput()
        self.fields['city'].widget.attrs['readonly'] = True
        self.fields['city'].widget = forms.HiddenInput()
        self.fields['tags'].widget.attrs['readonly'] = True
        self.fields['tags'].widget = forms.HiddenInput()
        self.fields['all_tags'].widget.attrs['readonly'] = True
        self.fields['all_tags'].widget = forms.HiddenInput()
        self.fields['language'].widget.attrs['readonly'] = True
        self.fields['language'].widget = forms.HiddenInput()

def schedule_request_reminder_sms(booking_id, host_id, guest_name, schedule_time):
    registered_user = RegisteredUser.objects.get(user_id=host_id)
    host_phone_num = registered_user.phone_number

    if host_phone_num:
        msg = _('%s' % REQUEST_REMIND_HOST).format(guest_name=guest_name)
        schedule_sms_if_no_confirmed.apply_async([host_phone_num, msg, booking_id], eta=schedule_time)

def instant_booking(experience, bk_date, bk_time):
    is_instant_booking = False
    local_timezone = pytz.timezone(settings.TIME_ZONE)
    instant_bookings = experience.instantbookingtimeperiod_set.all()
    for ib in instant_bookings:
        ib_start = ib.start_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
        ib_end = ib.end_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
        if ib.repeat:
            if ib.repeat_cycle.lower() == "daily":
                if (ib_start.date() - bk_date).days % ib.repeat_frequency == 0:
                    # for daily repeated time periods, the start and end time must be in the same day
                    if not (ib_start.hour <= bk_time.hour and bk_time.hour <= ib_end.hour):
                        # not a match: hour
                        continue
                    is_instant_booking = True
                    break
            elif ib.repeat_cycle.lower() == "weekly":
                weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                monday1 = (bk_date.date()-timedelta(days=bk_date.weekday()))
                monday2 = (ib_start.date() - timedelta(days=ib_start.date().weekday()))
                if ib.repeat_extra_information.find(weekdays[bk_date.weekday()])>=0 and ((monday1-monday2)/7).days%ib.repeat_frequency == 0:
                    # for weekly repeated time periods, the start and end time must be in the same day
                    if not (ib_start.hour <= bk_time.hour and bk_time.hour <= ib_end.hour):
                        # not a match: hour
                        continue
                    is_instant_booking = True
                    break
            elif ib.repeat_cycle.lower() == "monthly":
                if bk_date.day >= ib_start.date().day and bk_date.day <= ib_end.date().day and (bk_date.month - ib_start.month)%ib.repeat_frequency == 0:
                    if bk_date.day == ib_start.date().day and ib_start.hour > bk_time.hour:
                        # not a match: hour
                        continue
                    if bk_date.day == ib_end.date().day and ib_end.hour < bk_time.hour:
                        # not a match: hour
                        continue
                    is_instant_booking = True
                    break
        else:
            booking_datetime = local_timezone.localize(datetime(bk_date.year, bk_date.month, bk_date.day, bk_time.hour, bk_time.minute))
            if ib_start <= booking_datetime and booking_datetime <= ib_end:
                is_instant_booking = True
                break

    return is_instant_booking

class ItineraryBookingForm(forms.Form):
    user_id = forms.CharField()
    experience_id = forms.CharField(widget=forms.Textarea)
    date = forms.CharField(widget=forms.Textarea)
    time = forms.CharField(widget=forms.Textarea)
    guest_number = forms.IntegerField(label="People")
    itinerary_string = forms.CharField(widget=forms.Textarea, required=False)
    status = forms.CharField(initial="Requested")
    promo_code = forms.CharField(required=False)

    card_number = CreditCardField(required=True, label="Card Number")
    expiration = CCExpField(required=True, label="Expiration")
    cvv = forms.IntegerField(required=True, label="CVV Number",
        max_value=9999, widget=forms.TextInput(attrs={'size': '4'}))

    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    street1 = forms.CharField(max_length=50, required = False)
    street2 = forms.CharField(max_length=50, required = False)
    city_town = forms.CharField(max_length=20, required = False)
    state = forms.CharField(max_length=10, required = False)
    country = forms.ChoiceField(choices=Country, required = False)
    postcode = forms.CharField(max_length=4, required = False)
    phone_number = forms.CharField(max_length=15, required=False)

    coupon_extra_information = forms.CharField(max_length=500, required=False)
    booking_extra_information = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super(ItineraryBookingForm, self).__init__(*args, **kwargs)
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
        self.fields['itinerary_string'].widget.attrs['readonly'] = True
        self.fields['itinerary_string'].widget = forms.HiddenInput()

    def booking(self,ids,dates,times,user,guest_number,
                card_number=None,exp_month=None,exp_year=None,cvv=None,
                booking_extra_information=None,coupon_extra_information=None,coupon=None,
                payment_street1=None,payment_street2=None,payment_city=None,
                payment_state=None,payment_country=None,payment_postcode=None,payment_phone_number=None,stripe_token=None):

        for i in range(len(ids)):
            extra_fee = 0.00
            free = False

            if coupon is not None:
                extra = json.loads(coupon.rules)
                if type(extra["extra_fee"]) == int or type(extra["extra_fee"]) == float:
                    extra_fee = extra["extra_fee"]
                elif type(extra["extra_fee"]) == str and extra["extra_fee"] == "FREE":
                    free = True

            if cvv == "ALIPAY":
                free = True
                booking_extra_information = card_number

            experience = AbstractExperience.objects.get(id=ids[i])
            if type(experience) == Experience:
                experience.title = experience.get_title(settings.LANGUAGES[0][0])
                experience.meetup_spot = get_experience_meetup_spot(experience, settings.LANGUAGES[0][0])
                experience.dropoff_spot = get_experience_dropoff_spot(experience, settings.LANGUAGES[0][0])
            else:
                experience.title = experience.get_title(settings.LANGUAGES[0][0])

            if not free:
                subtotal_price = 0.0
                if experience.dynamic_price and type(experience.dynamic_price) == str:
                    price = experience.dynamic_price.split(',')
                    if len(price)+experience.guest_number_min-2 == experience.guest_number_max:
                    #these is comma in the end, so the length is max-min+2
                        if guest_number <= experience.guest_number_min:
                            subtotal_price = float(experience.price) * float(experience.guest_number_min)
                        else:
                            subtotal_price = float(price[guest_number-experience.guest_number_min]) * float(guest_number)
                    else:
                        #wrong dynamic settings
                        subtotal_price = float(experience.price)*float(guest_number)
                else:
                    subtotal_price = float(experience.price)*float(guest_number)

                COMMISSION_PERCENT = round(experience.commission/(1-experience.commission),3)
                if extra_fee == 0.00:
                    price = round(subtotal_price*(1.00+COMMISSION_PERCENT), 0)*(1.00+settings.STRIPE_PRICE_PERCENT) + settings.STRIPE_PRICE_FIXED
                elif extra_fee >= 1.00 or extra_fee <= -1.00:
                    #absolute value
                    price = round(subtotal_price*(1.00+COMMISSION_PERCENT)+extra_fee, 0)*(1.00+settings.STRIPE_PRICE_PERCENT) + settings.STRIPE_PRICE_FIXED
                else:
                    #percentage, e.g., 30% discount --> percentage == -0.3
                    price = round(subtotal_price*(1.00+COMMISSION_PERCENT), 0)*(1+extra_fee)*(1.00+settings.STRIPE_PRICE_PERCENT) + settings.STRIPE_PRICE_FIXED

                if price > 0:
                    payment = Payment()
                    #change price into cent
                    success, instance = payment.charge(int(price*100), experience.currency, card_number, exp_month, exp_year, cvv, stripe_token)
                else:
                    success = True
                    free = True

            else:
                success = True

            if not success:
                raise forms.ValidationError("Error: %s" % str(instance))
            else:
                #save the booking record
                #user = User.objects.get(id=self.cleaned_data['user_id']) #moved outside of the for loop
                host = get_host(experience)
                bk_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(dates[i].strip(), "%Y/%m/%d"))
                bk_time = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(times[i].split(":")[0].strip(), "%H"))
                local_timezone = pytz.timezone(settings.TIME_ZONE)

                is_instant_booking = instant_booking(experience, bk_date, bk_time)

                if coupon:
                    booking = Booking(user = user, experience= experience, guest_number = guest_number,
                                        datetime = local_timezone.localize(datetime(bk_date.year, bk_date.month, bk_date.day, bk_time.hour, bk_time.minute)).astimezone(pytz.timezone("UTC")),
                                        submitted_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC), status="paid",
                                        coupon_extra_information=coupon_extra_information,
                                        coupon=coupon,
                                        booking_extra_information=booking_extra_information)
                else:
                    booking = Booking(user = user, experience= experience, guest_number = guest_number,
                                        datetime = local_timezone.localize(datetime(bk_date.year, bk_date.month, bk_date.day, bk_time.hour, bk_time.minute)).astimezone(pytz.timezone("UTC")),
                                        submitted_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC), status="paid", booking_extra_information=booking_extra_information)
                booking.save()
                #add the user to the guest list
                if type(experience) == Experience and user not in experience.guests.all():
                #experience.guests.add(user)
                    cursor = connections['default'].cursor()
                    cursor.execute("Insert into experiences_experience_guests (experience_id,user_id) values (%s, %s)", [experience.id, user.id])

                if not free:
                    instance.save()
                    payment.charge_id = instance['id']
                    payment.booking_id = booking.id
                    payment.street1 = payment_street1 if payment_street1 is not None else ""
                    payment.street2 = payment_street2 if payment_street2 is not None else ""
                    payment.city = payment_city if payment_city is not None else ""
                    payment.state = payment_state if payment_state is not None else ""
                    payment.country = payment_country if payment_country is not None else ""
                    payment.postcode = payment_postcode if payment_postcode is not None else ""
                    payment.phone_number = payment_phone_number if payment_phone_number is not None else ""
                    payment.save()

                    booking.payment_id = payment.id
                    booking.save()

                send_booking_email_verification(booking, experience, user, is_instant_booking)
                sms_notification(booking, experience, user, payment_phone_number)

    def clean(self):
        """
        The clean method will effectively charge the card and create a new
        Payment instance. If it fails, it simply raises the error given from
        Stripe's library as a standard ValidationError for proper feedback.
        """
        cleaned = super(ItineraryBookingForm, self).clean()

        if not self.errors and (not 'Refresh' in self.data):
            card_number = self.cleaned_data["card_number"]
            exp_month = self.cleaned_data["expiration"].month
            exp_year = self.cleaned_data["expiration"].year
            cvv = self.cleaned_data["cvv"]

            ids = self.cleaned_data['experience_id'].split(';')
            dates = self.cleaned_data['date'].split(';')
            times = self.cleaned_data['time'].split(';')

            ids.remove('')
            dates.remove('')
            times.remove('')

            date_start = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(dates[0].strip() + " " + times[0].split(":")[0].strip(), "%Y/%m/%d %H"))
            date_end = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(dates[len(dates)-1].strip() + " " + times[len(dates)-1].split(":")[0].strip(), "%Y/%m/%d %H"))
            cp = Coupon.objects.filter(promo_code__iexact = self.cleaned_data['promo_code'],
                                       end_datetime__gt = date_end,
                                       start_datetime__lt = date_start)

            if len(cp)>0:
                rules = json.loads(cp[0].rules)
                #TODO

            user = User.objects.get(id=self.cleaned_data['user_id'])
            guest_number = int(self.cleaned_data["guest_number"])
            booking_extra_information="Need Chinese Translation" if 'booking_extra_information' in self.cleaned_data and self.cleaned_data['booking_extra_information'] else ""
            coupon_extra_information=self.cleaned_data['coupon_extra_information'],
            coupon=cp[0] if len(cp)>0 else None
            payment_street1 = self.cleaned_data['street1']
            payment_street2 = self.cleaned_data['street2']
            payment_city = self.cleaned_data['city_town']
            payment_state = self.cleaned_data['state']
            payment_country = self.cleaned_data['country']
            payment_postcode = self.cleaned_data['postcode']
            payment_phone_number = self.cleaned_data['phone_number']

            self.booking(ids,dates,times,user,guest_number,
                         card_number,exp_month,exp_year,cvv,
                         booking_extra_information,coupon_extra_information,coupon,
                         payment_street1,payment_street2,payment_city,payment_state,payment_country,payment_postcode,payment_phone_number)

        return cleaned

def get_host(experience):
    if type(experience) == Experience:
        return experience.hosts.all()[0]
    else:
        return experience.provider.user

def send_booking_email_verification(booking, experience, user, is_instant_booking):
    if type(experience) != Experience: #issue 209
        return

    host = get_host(experience)
    if not is_instant_booking:
        if not settings.DEVELOPMENT:
            # send an email to the host
            mail.send(subject=_('[Tripalocal] ') + user.first_name + _(' has requested your experience'), message='',
                        sender=_('Tripalocal <') + Aliases.objects.filter(destination__contains=user.email)[0].mail + '>',
                        recipients = [Aliases.objects.filter(destination__contains=host.email)[0].mail], #fail_silently=False,
                        priority='now',
                        html_message=loader.render_to_string('experiences/email_booking_requested_host.html',
                                                                {'experience': experience,
                                                                'booking':booking,
                                                                'user_first_name':user.first_name,
                                                                'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                                'accept_url': settings.DOMAIN_NAME + '/booking/' + str(booking.id) + '?accept=yes',
                                                                'reject_url': settings.DOMAIN_NAME + '/booking/' + str(booking.id) + '?accept=no',
                                                                'LANGUAGE':settings.LANGUAGE_CODE}))

            # send an email to the traveler
            mail.send(subject=_('[Tripalocal] Your booking request is sent to the host'),  message='',
                        sender=_('Tripalocal <') + Aliases.objects.filter(destination__contains=host.email)[0].mail + '>',
                        recipients = [Aliases.objects.filter(destination__contains=user.email)[0].mail], #fail_silently=False,
                        priority='now',
                        html_message=loader.render_to_string('experiences/email_booking_requested_traveler.html',
                                                                {'experience': experience,
                                                                'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                                'booking':booking,
                                                                'LANGUAGE':settings.LANGUAGE_CODE}))
    else:
        #instant booking
        booking.status = "accepted"
        booking.save()
        if booking.coupon_id != None and booking.coupon.promo_code.startswith("once"):
            #the coupon can be used once, make it unavailable
            booking.coupon.end_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC)
            booking.coupon.save()

        if not settings.DEVELOPMENT:
            #send an email to the traveller
            mail.send(subject=_('[Tripalocal] Booking confirmed'), message='',
                        sender=_('Tripalocal <') + Aliases.objects.filter(destination__contains=host.email)[0].mail + '>',
                        recipients = [Aliases.objects.filter(destination__contains=user.email)[0].mail],
                        priority='now',  #fail_silently=False,
                        html_message=loader.render_to_string('experiences/email_booking_confirmed_traveler.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'user':user,
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                            'LANGUAGE':settings.LANGUAGE_CODE}))

            #schedule an email to the traveller one day before the experience
            mail.send(subject=_('[Tripalocal] Booking reminder'), message='',
                        sender=_('Tripalocal <') + Aliases.objects.filter(destination__contains=host.email)[0].mail + '>',
                        recipients = [Aliases.objects.filter(destination__contains=user.email)[0].mail],
                        priority='high',  scheduled_time = booking.datetime - timedelta(days=1),
                        html_message=loader.render_to_string('experiences/email_reminder_traveler.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'user':user, #not host --> need "my" phone number
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                            'LANGUAGE':settings.LANGUAGE_CODE}))

            #schedule an email to the host one day before the experience
            mail.send(subject=_('[Tripalocal] Booking reminder'), message='',
                        sender=_('Tripalocal <') + Aliases.objects.filter(destination__contains=user.email)[0].mail + '>',
                        recipients = [Aliases.objects.filter(destination__contains=host.email)[0].mail],
                        priority='high',  scheduled_time = booking.datetime - timedelta(days=1),
                        html_message=loader.render_to_string('experiences/email_reminder_host.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'user':user,
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                            'LANGUAGE':settings.LANGUAGE_CODE}))

            #schedule an email for reviewing the experience
            mail.send(subject=_('[Tripalocal] How was your experience?'), message='',
                        sender=settings.DEFAULT_FROM_EMAIL,
                        recipients = [Aliases.objects.filter(destination__contains=user.email)[0].mail],
                        priority='high',  scheduled_time = booking.datetime + timedelta(days=1, hours=experience.duration),
                        html_message=loader.render_to_string('experiences/email_review_traveler.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                            'review_url':settings.DOMAIN_NAME + '/reviewexperience/' + str(experience.id),
                                                            'LANGUAGE':settings.LANGUAGE_CODE}))

            #send an email to the host
            mail.send(subject=_('[Tripalocal] Booking confirmed'), message='',
                        sender=_('Tripalocal <') + Aliases.objects.filter(destination__contains=user.email)[0].mail + '>',
                        recipients = [Aliases.objects.filter(destination__contains=host.email)[0].mail],
                        priority='now',  #fail_silently=False,
                        html_message=loader.render_to_string('experiences/email_booking_confirmed_host.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'user':user,
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                            'LANGUAGE':settings.LANGUAGE_CODE}))

def sms_notification(booking, experience, user, phone_number):
    if type(experience) == Experience:
        exp_title = experience.get_title(settings.LANGUAGE_CODE)
    else:
        exp_title = experience.get_title(settings.LANGUAGE_CODE)
        return #issue 209

    customer_phone_num = phone_number
    exp_datetime_local = booking.datetime.astimezone(tzlocal())
    exp_datetime_local_str = exp_datetime_local.strftime(_("%H:%M %d %b %Y"))
    host = get_host(experience)
    send_booking_request_sms(exp_datetime_local_str, exp_title, host, customer_phone_num, user)
    schedule_request_reminder_sms(booking.id, host.id, user.first_name, booking.datetime + timedelta(days=1))

def send_booking_request_sms(exp_datetime, exp_title, host, customer_phone_num, customer):
    registered_user = RegisteredUser.objects.get(user_id=host.id)
    host_phone_num = registered_user.phone_number

    if host_phone_num:
        msg = _('%s' % REQUEST_SENT_NOTIFY_HOST).format(customer.first_name, exp_title, exp_datetime, customer.first_name)
        send_sms(host_phone_num, msg)

    if customer_phone_num:
        msg = _('%s' % REQUEST_SENT_NOTIFY_CUSTOMER).format(host.first_name, exp_title, exp_datetime)
        send_sms(customer_phone_num, msg)

class SearchForm(forms.Form):
    start_date = forms.DateTimeField(required=False)
    end_date = forms.DateTimeField(required=False)
    guest_number = forms.ChoiceField(choices=Guest_Number, widget=forms.Select(attrs={'class':'ui dropdown smaller-box'}), required=False)
    city = forms.ChoiceField(choices=Location, widget=forms.Select(attrs={'class':'ui dropdown'}), required=True)
    language = forms.CharField(widget=forms.Textarea,  required=False, initial="English,Mandarin")
    is_kids_friendly = forms.BooleanField(required=False, widget=forms.CheckboxInput())
    is_host_with_cars = forms.BooleanField(required=False, widget=forms.CheckboxInput())
    is_private_tours = forms.BooleanField(required=False, widget=forms.CheckboxInput())
    tags = forms.CharField(widget=forms.Textarea, required=False, initial=Tags)
    all_tags = forms.CharField(widget=forms.Textarea, required=True, initial=Tags)

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['tags'].widget.attrs['readonly'] = True
        self.fields['tags'].widget = forms.HiddenInput()
        self.fields['all_tags'].widget.attrs['readonly'] = True
        self.fields['all_tags'].widget = forms.HiddenInput()
        self.fields['language'].widget.attrs['readonly'] = True
        self.fields['language'].widget = forms.HiddenInput()
