from io import BytesIO
from urllib.parse import urlencode
from app.wechat_payment.api import UnifiedOrderPay, OrderQuery
from app.wechat_payment.utils import dict_to_xml
from django.core.files.storage import default_storage as storage
from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic.list import ListView
from django.views.generic import DetailView
from experiences.forms import *
from datetime import *
import pytz, os, json, math, PIL, xlsxwriter
from django.template import RequestContext, loader
from Tripalocal_V1 import settings
from decimal import Decimal
from django import forms
from tripalocal_messages.models import Aliases
from app.forms import SubscriptionForm
from mixpanel import Mixpanel
from dateutil.relativedelta import relativedelta
from django.db import connections
from app.models import *
from PIL import Image
from django.utils.translation import ugettext as _
from post_office import mail
from collections import OrderedDict
from django.http import Http404
from django.core.urlresolvers import reverse
from experiences.constant import  *
from experiences.tasks import schedule_sms
from experiences.telstra_sms_api import send_sms
from unionpay import client, signer
from unionpay.util.helper import load_config, make_order_id
from django.views.decorators.csrf import csrf_exempt
import itertools
import xmltodict
from django.db.models import Q

MaxPhotoNumber=10
PROFILE_IMAGE_SIZE_LIMIT = 1048576
MaxIDImage=5

LANG_CN = settings.LANGUAGES[1][0]
LANG_EN = settings.LANGUAGES[0][0]
GEO_POSTFIX = settings.GEO_POSTFIX

def isEnglish(s):
    try:
        s.decode('ascii') if isinstance(s, bytes) else s.encode('ascii')
    except UnicodeDecodeError:
        return False
    except UnicodeEncodeError:
        return False
    else:
        return True

def experience_fee_calculator(price, commission_rate):
    if type(price)==int or type(price) == float:
        COMMISSION_PERCENT = round(commission_rate/(1-commission_rate),3)
        return round(price*(1.00+COMMISSION_PERCENT), 0)*(1.00+settings.STRIPE_PRICE_PERCENT) + settings.STRIPE_PRICE_FIXED

    return price

def next_time_slot(repeat_cycle, repeat_frequency, repeat_extra_information, current_datetime, daylightsaving):
    #daylightsaving: whether it was in daylightsaving when this blockout/instant booking record was created
    current_datetime_local = current_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))

    if daylightsaving:#daylight saving
        if current_datetime_local.dst() == timedelta(0):# not daylight saving
            current_datetime_local = current_datetime_local + relativedelta(hours=1)
    elif current_datetime_local.dst() != timedelta(0):
        current_datetime_local = current_datetime_local - relativedelta(hours=1)

    if repeat_cycle.lower() == "daily":
        return current_datetime + relativedelta(days=+repeat_frequency)
    elif repeat_cycle.lower() == "weekly":
        if repeat_extra_information:
            days_name = repeat_extra_information.split(';')
            days=[]
            for day in days_name:
                if day.lower() == "monday":
                    days.append(0)
                elif day.lower() == "tuesday":
                    days.append(1)
                elif day.lower() == "wednesday":
                    days.append(2)
                elif day.lower() == "thursday":
                    days.append(3)
                elif day.lower() == "friday":
                    days.append(4)
                elif day.lower() == "saturday":
                    days.append(5)
                elif day.lower() == "sunday":
                    days.append(6)

            days.sort()
            current_day = current_datetime_local.date().weekday()
            if current_day in days:
                if days.index(current_day) < len(days)-1:
                    next_day = days[days.index(current_day)+1]
                    next_day -= current_day
                    return current_datetime + relativedelta(days=+next_day)
                else: # days.index(current_day) == len(days)-1:
                    next_day = days[0] - days[days.index(current_day)] + 7
                    return current_datetime + relativedelta(weeks=(repeat_frequency-1), days=next_day)
            else:
                #conflicting input
                #return current_datetime + relativedelta(days=(days[len(days)-1]-current_day))
                raise Exception("func next_time_slot, conflicting input, weekly repeated experience")
        else:
            raise Exception("func next_time_slot, empty string: repeat_extra_information")
    elif repeat_cycle.lower() == "monthly":
        if repeat_extra_information:
            #if repeat_extra_information == "date":
            return current_datetime + relativedelta(months=+repeat_frequency)
            #TODO
            #elif repeat_extra_information == "day":

        else:
            raise Exception("func next_time_slot, empty string: repeat_extra_information")
    else:
        raise Exception("func next_time_slot, illegal repeat_cycle")

def get_available_experiences(exp_type, start_datetime, end_datetime, guest_number=None, city=None, language=None, keywords=None):
    #city/keywords is a string like A,B,C,
    local_timezone = pytz.timezone(settings.TIME_ZONE)
    available_options = []
    end_datetime = end_datetime.replace(hour=22)

    exp_type = exp_type.lower()
    if exp_type == 'all':
        experiences = AbstractExperience.objects.all()
        experiences = [e for e in experiences if e.status == 'Listed']
    elif exp_type == 'newproduct':
        experiences = AbstractExperience.objects.instance_of(NewProduct)
        experiences = [e for e in experiences if e.status == 'Listed']
    else:
        experiences = AbstractExperience.objects.instance_of(Experience)
        if exp_type == 'itinerary':
            experiences = [e for e in experiences if e.status == 'Listed' and e.type == 'ITINERARY']
        else:
            experiences = [e for e in experiences if e.status == 'Listed' and e.type != 'ITINERARY']

    if city is not None:
        city = str(city).lower().split(",")

        if len(city) > 1 and (end_datetime-start_datetime).days+1 != len(city):
            raise TypeError("Wrong format: city, incorrect length")

        if not isEnglish(city[0]):
            for i in range(len(city)):
                city[i] = dict(Location_reverse).get(city[i]).lower()

        experiences = [e for e in experiences if e.city.lower() in city]


    for experience in experiences:
        if guest_number is not None and (experience.guest_number_max < int(guest_number) or experience.guest_number_min > int(guest_number)):
            continue

        if guest_number is None:
            if experience.guest_number_min <= 4 and experience.guest_number_max>=4:
                guest_number = 4
            elif experience.guest_number_min > 4:
                guest_number = experience.guest_number_min
            elif experience.guest_number_max < 4:
                guest_number = experience.guest_number_max

        if keywords is not None:
            experience_tags = experience.get_tags(settings.LANGUAGES[0][0])
            tags = keywords.strip().split(",")
            match = False
            for tag in tags:
                if tag.strip() in experience_tags:
                    match = True
                    break
            if not match:
                continue

        if language is not None:
            experience_language = experience.language.split(";") if experience.language is not None else ''
            experience_language = [x.lower() for x in experience_language]
            languages = language.split(",")
            match = False
            for l in languages:
                if l.lower() in experience_language:
                    match = True
                    break
            if not match:
                continue

        sdt = start_datetime
        last_sdt = pytz.timezone('UTC').localize(datetime.min)

        #calculate rate
        rate = 0.0
        counter = 0
        for review in experience.review_set.all():
            rate += review.rate
            counter += 1

        if counter > 0:
            rate /= counter

        #check if calendar updated
        calendar_updated = False
        if len(experience.instantbookingtimeperiod_set.all()) > 0 or len(experience.blockouttimeperiod_set.all()) > 0:
            calendar_updated = True

        host = get_host(experience)
        exp_price = float(experience.price)
        if experience.dynamic_price != None and len(experience.dynamic_price.split(',')) == experience.guest_number_max - experience.guest_number_min + 2 :
            exp_price = float(experience.dynamic_price.split(",")[int(guest_number)-experience.guest_number_min])

        photo_url = ''
        photos = experience.photo_set.all()
        if photos is not None and len(photos) > 0:
            photo_url = photos[0].directory+photos[0].name

        #get the number of booking times
        bks = Booking.objects.filter(experience_id = experience.id)
        if bks is not None:
            bks = len(bks)
        else:
            bks = 0

        if type(experience) is Experience:
            tp = experience.type
        else:
            tp ="NEWPRODUCT"

        experience_avail = {'id':experience.id, 'title': experience.get_title(settings.LANGUAGES[0][0]), 'rate': rate,
                            'duration':int(experience.duration) if float(experience.duration).is_integer() else experience.duration,
                            'city':experience.city, 'description':experience.get_description(settings.LANGUAGES[0][0]),
                            'language':experience.language, 'calendar_updated':calendar_updated,
                            'price':experience_fee_calculator(exp_price, experience.commission),
                            'currency':str(dict(Currency)[experience.currency.upper()]),
                            'dollarsign':DollarSign[experience.currency.upper()],'dates':{},
                            'photo_url':photo_url, 'type':tp , 'popularity':bks, 'tags':experience.get_tags(settings.LANGUAGES[0][0])}

        if exp_type == 'experience':
            experience_avail['meetup_spot'] = get_experience_meetup_spot(experience, settings.LANGUAGES[0][0])
            experience_avail['host_image'] = host.registereduser.image_url
            experience_avail['host'] = host.first_name + ' ' + host.last_name

        blockouts = experience.blockouttimeperiod_set.filter(experience_id=experience.id)
        blockout_start = []
        blockout_end = []
        blockout_index=0

        #calculate all the blockout time periods
        for blk in blockouts:
            if blk.start_datetime.astimezone(pytz.timezone(settings.TIME_ZONE)).dst() != timedelta(0):
                daylightsaving = True
            else:
                daylightsaving = False

            if blk.repeat:
                b_l =  blk.end_datetime - blk.start_datetime
                if not blk.repeat_end_date or blk.repeat_end_date > (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date():
                    blk.repeat_end_date = (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date()
                while blk.start_datetime.date() <= blk.repeat_end_date:
                    blockout_index += 1
                    blockout_start.append(blk.start_datetime)
                    blockout_end.append(blk.start_datetime + b_l)

                    blk.start_datetime = next_time_slot(blk.repeat_cycle, blk.repeat_frequency,
                                                        blk.repeat_extra_information, blk.start_datetime,daylightsaving)

            else:
                blockout_index += 1
                blockout_start.append(blk.start_datetime)
                blockout_end.append(blk.end_datetime)

        blockout_start.sort()
        blockout_end.sort()

        instantbookings = experience.instantbookingtimeperiod_set.filter(experience_id=experience.id)
        instantbooking_start = []
        instantbooking_end = []
        instantbooking_index=0

        #calculate all the instant booking time periods
        for ib in instantbookings :
            if ib.start_datetime.astimezone(pytz.timezone(settings.TIME_ZONE)).dst() != timedelta(0):
                daylightsaving = True
            else:
                daylightsaving = False

            if ib.repeat:
                ib_l =  ib.end_datetime - ib.start_datetime
                if not ib.repeat_end_date or ib.repeat_end_date > (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date():
                    ib.repeat_end_date = (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date()
                while ib.start_datetime.date() <= ib.repeat_end_date:
                    instantbooking_index += 1
                    instantbooking_start.append(ib.start_datetime)
                    instantbooking_end.append(ib.start_datetime + ib_l)

                    ib.start_datetime = next_time_slot(ib.repeat_cycle, ib.repeat_frequency,
                                                       ib.repeat_extra_information, ib.start_datetime, daylightsaving)

            else:
                instantbooking_index += 1
                instantbooking_start.append(ib.start_datetime)
                instantbooking_end.append(ib.end_datetime)

        instantbooking_start.sort()
        instantbooking_end.sort()

        bookings = experience.booking_set.filter(experience_id=experience.id).exclude(status__iexact="rejected")

        block_i=0
        instantbooking_i=0
        while (sdt <= end_datetime):
            sdt_local = sdt.astimezone(local_timezone)
            if pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone(settings.TIME_ZONE)).dst() != timedelta(0):
                #daylight saving
                if not sdt_local.dst() != timedelta(0):
                    # not daylight saving
                    sdt_local = sdt_local + relativedelta(hours=1)
            elif sdt_local.dst() != timedelta(0):
                sdt_local = sdt_local - relativedelta(hours=1)

            if sdt_local.date() != last_sdt.date():
                new_date = sdt_local.strftime("%Y/%m/%d")
                experience_avail['dates'][new_date] = []
                last_sdt = sdt_local

            #check if the date is blocked
            blocked = False

            #block 10pm-7am if repeated hourly
            #if experience.repeat_cycle == "Hourly" and (sdt_local.time().hour <= 7 or sdt_local.time().hour >= 22):
            #    blocked = True

            if not blocked:
                #blockout_start, blockout_end are sorted, sdt keeps increasing
                #block_i: skip the periods already checked
                for b_i in range(block_i, blockout_index):
                    if (blockout_start[b_i] <= sdt and sdt <= blockout_end[b_i]) or (blockout_start[b_i] <= sdt+relativedelta(hours=+experience.duration) and sdt+relativedelta(hours=+experience.duration) <= blockout_end[b_i]):
                        blocked = True
                        break
                    if sdt+relativedelta(hours=+experience.duration) < blockout_start[b_i]:
                        #no need to check further slots after the current one
                        break
                    block_i += 1

            if not blocked:
                i = 0
                for bking in bookings :
                    if bking.datetime == sdt and bking.status.lower() != "rejected":
                        i += bking.guest_number
                    #if someone book a 2pm experience, and the experience last 3 hours, the system should automatically wipe out the 3pm, 4pm and 5pm sessions
                    if bking.datetime < sdt and bking.datetime + timedelta(hours=experience.duration) >= sdt and bking.status.lower() != "rejected":
                        i += experience.guest_number_max #changed from bking.guest_number to experience.guest_number_max

                if i == 0 or (experience.type == "NONPRIVATE" and i < experience.guest_number_max):
                    if (hasattr(experience, 'repeat_cycle') and experience.repeat_cycle != "") or (sdt_local.time().hour > 7 and sdt_local.time().hour <22):
                        instant_booking = False
                        #instantbooking_start, instantbooking_end are sorted, sdt keeps increasing
                        #instantbooking_i: skip the periods already checked
                        for ib_i in range(instantbooking_i, instantbooking_index):
                            if (instantbooking_start[ib_i] <= sdt and sdt <= instantbooking_end[ib_i]): # and (instantbooking_start[ib_i] <= sdt+relativedelta(hours=+experience.duration) and sdt+relativedelta(hours=+experience.duration) <= instantbooking_end[ib_i]):
                                instant_booking = True
                                break
                            if sdt+relativedelta(hours=+experience.duration) < instantbooking_start[ib_i]:
                                #no need to check further slots after the current one
                                break
                            if sdt > instantbooking_start[ib_i]:
                                instantbooking_i += 1

                        d = {'available_seat': experience.guest_number_max - i,
                                'time_string': sdt_local.strftime("%H").lstrip('0') if sdt_local.strftime("%H")!="00" else "0",
                                'instant_booking': instant_booking}
                        experience_avail['dates'][sdt_local.strftime("%Y/%m/%d")].append(d)

            sdt += timedelta(hours=1)
        experience_avail['dates'] = OrderedDict(sorted(experience_avail['dates'].items(), key=lambda t: t[0]))
        available_options.append(experience_avail)
    return available_options

def experience_availability(request):
    if not request.user.is_authenticated() or not request.user.is_staff:
        return HttpResponseRedirect(GEO_POSTFIX)

    context = RequestContext(request)
    form = ExperienceAvailabilityForm()

    if request.method == 'POST':
        form = ExperienceAvailabilityForm(request.POST)

        if form.is_valid():
            start_datetime = form.cleaned_data['start_datetime'] if 'start_datetime' in form.cleaned_data and form.cleaned_data['start_datetime'] != None else pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone(settings.TIME_ZONE))
            end_datetime = form.cleaned_data['end_datetime'] if 'end_datetime' in form.cleaned_data and form.cleaned_data['end_datetime'] != None else pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone(settings.TIME_ZONE)) + timedelta(days=1)
            local_timezone = pytz.timezone(settings.TIME_ZONE)
            available_options = []

            available_options = get_available_experiences('experience', start_datetime, end_datetime)

            #add title
            dict = {'id':'Id', 'title':'Title', 'host':'Host', 'dates':{}}
            sdt = start_datetime
            while (sdt <= end_datetime):
                dict['dates'][sdt.astimezone(local_timezone).strftime("%Y/%m/%d")] = [{'time_string':sdt.astimezone(local_timezone).strftime("%m/%d")}]
                sdt += relativedelta(days=1)
            dict['dates'] = OrderedDict(sorted(dict['dates'].items(), key=lambda t: t[0]))
            available_options.insert(0,dict)

            #workbook = xlsxwriter.Workbook(os.path.join(os.path.join(settings.PROJECT_ROOT,'xls'), 'Experience availability.xlsx'))
            #worksheet = workbook.add_worksheet()

            #row = 0
            #for experience in available_options:
            #    col = 0
            #    worksheet.write(row, col, experience['id'])
            #    col += 1
            #    worksheet.write(row, col, experience['title'])
            #    col += 1
            #    worksheet.write(row, col, experience['host'])
            #    col += 1
            #    for date, slots in experience['dates'].items():
            #        str=''
            #        for slot in slots:
            #            str += slot['time_string']
            #            if 'instant_booking' in slot and slot['instant_booking']:
            #                str += '(I)'
            #            str += ' '
            #        worksheet.write(row, col, str)
            #        col += 1
            #    row += 1
            #workbook.close()

            return render_to_response('experiences/experience_availability.html', {'form':form,'available_options':available_options}, context)

    return render_to_response('experiences/experience_availability.html', {'form':form}, context)

class ExperienceListView(ListView):
    template_name = 'experiences/experience_list.html'
    #paginate_by = 9
    #context_object_name = 'experience_list'

    def get_queryset(self):
        if self.request.user.is_authenticated() and self.request.user.is_superuser:
            return Experience.objects.all#()
        else:
            return HttpResponseRedirect(GEO_POSTFIX + "admin/login/?next=" + GEO_POSTFIX + "experiencelist")

def getAvailableOptions(experience, available_options, available_date):

    top_instant_bookings = -1

    last_sdt = pytz.timezone('UTC').localize(datetime.min)
    local_timezone = pytz.timezone(settings.TIME_ZONE)

    #requirement change: all timeslots are considered available unless being explicitly blocked
    #while (sdt < datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(hours=+6)):
        #if experience.repeat_cycle == "Hourly" :
        #    sdt += timedelta(hours=experience.repeat_frequency)
        #elif experience.repeat_cycle == "Daily" :
        #    sdt += timedelta(days=experience.repeat_frequency)
        #elif experience.repeat_cycle == "Weekly" :
        #    sdt += timedelta(weeks=experience.repeat_frequency)
        #else :
            #TODO
    #set the start time to 6 hours later
    sdt = datetime.utcnow().replace(tzinfo=pytz.UTC).replace(minute=0, second=0, microsecond=0) + relativedelta(hours=+23)

    blockouts = experience.blockouttimeperiod_set.filter(experience_id=experience.id)
    blockout_start = []
    blockout_end = []
    blockout_index=0

    #calculate all the blockout time periods
    for blk in blockouts :
        if blk.start_datetime.astimezone(pytz.timezone(settings.TIME_ZONE)).dst() != timedelta(0):
            daylightsaving = True
        else:
            daylightsaving = False

        if blk.repeat:
            b_l =  blk.end_datetime - blk.start_datetime
            if not blk.repeat_end_date or blk.repeat_end_date > (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date():
                blk.repeat_end_date = (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date()
            while blk.start_datetime.date() <= blk.repeat_end_date:
                blockout_index += 1
                blockout_start.append(blk.start_datetime)
                blockout_end.append(blk.start_datetime + b_l)

                blk.start_datetime = next_time_slot(blk.repeat_cycle, blk.repeat_frequency,
                                                    blk.repeat_extra_information, blk.start_datetime, daylightsaving)

        else:
            blockout_index += 1
            blockout_start.append(blk.start_datetime)
            blockout_end.append(blk.end_datetime)

    blockout_start.sort()
    blockout_end.sort()

    instantbookings = experience.instantbookingtimeperiod_set.filter(experience_id=experience.id)
    instantbooking_start = []
    instantbooking_end = []
    instantbooking_index=0

    #calculate all the instant booking time periods
    for ib in instantbookings :
        if ib.start_datetime.astimezone(pytz.timezone(settings.TIME_ZONE)).dst() != timedelta(0):
            daylightsaving = True
        else:
            daylightsaving = False

        if ib.repeat:
            ib_l =  ib.end_datetime - ib.start_datetime
            if not ib.repeat_end_date or ib.repeat_end_date > (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date():
                ib.repeat_end_date = (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date()
            while ib.start_datetime.date() <= ib.repeat_end_date:
                instantbooking_index += 1
                instantbooking_start.append(ib.start_datetime)
                instantbooking_end.append(ib.start_datetime + ib_l)

                ib.start_datetime = next_time_slot(ib.repeat_cycle, ib.repeat_frequency,
                                                   ib.repeat_extra_information, ib.start_datetime, daylightsaving)

        else:
            instantbooking_index += 1
            instantbooking_start.append(ib.start_datetime)
            instantbooking_end.append(ib.end_datetime)

    instantbooking_start.sort()
    instantbooking_end.sort()

    bookings = experience.booking_set.filter(experience_id=experience.id).exclude(status__iexact="rejected")

    block_i=0
    instantbooking_i=0
    while (sdt <= experience.end_datetime and sdt <= datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2) ):
        #check if the date is blocked
        blocked = False

        #block 10pm-7am if repeated hourly
        sdt_local = sdt.astimezone(local_timezone)
        if pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone(settings.TIME_ZONE)).dst() != timedelta(0):
            #daylight saving
            if not sdt_local.dst() != timedelta(0):
                # not daylight saving
                sdt_local = sdt_local + relativedelta(hours=1)
        elif sdt_local.dst() != timedelta(0):
            sdt_local = sdt_local - relativedelta(hours=1)
        #if experience.repeat_cycle == "Hourly" and (sdt_local.time().hour <= 7 or sdt_local.time().hour >= 22):
        #    blocked = True

        if not blocked:
            #blockout_start, blockout_end are sorted, sdt keeps increasing
            #block_i: skip the periods already checked
            for b_i in range(block_i, blockout_index):
                if (blockout_start[b_i] <= sdt and sdt <= blockout_end[b_i]) or (blockout_start[b_i] <= sdt+relativedelta(hours=+experience.duration) and sdt+relativedelta(hours=+experience.duration) <= blockout_end[b_i]):
                    blocked = True
                    break
                if sdt+relativedelta(hours=+experience.duration) < blockout_start[b_i]:
                    #no need to check further slots after the current one
                    break
                block_i += 1

        if not blocked:
            i = 0
            for bking in bookings :
                if bking.datetime == sdt and bking.status.lower() != "rejected":
                    i += bking.guest_number
                #if someone book a 2pm experience, and the experience last 3 hours, the system should automatically wipe out the 3pm, 4pm and 5pm sessions
                if bking.datetime < sdt and bking.datetime + timedelta(hours=experience.duration) >= sdt and bking.status.lower() != "rejected":
                    i += experience.guest_number_max

            if i == 0 or (experience.type == "NONPRIVATE" and i < experience.guest_number_max):
                if (sdt_local.time().hour > 7 and sdt_local.time().hour <22):
                    instant_booking = False
                    #instantbooking_start, instantbooking_end are sorted, sdt keeps increasing
                    #instantbooking_i: skip the periods already checked
                    for ib_i in range(instantbooking_i, instantbooking_index):
                        if (instantbooking_start[ib_i] <= sdt and sdt <= instantbooking_end[ib_i]):# and (instantbooking_start[ib_i] <= sdt+relativedelta(hours=+experience.duration) and sdt+relativedelta(hours=+experience.duration) <= instantbooking_end[ib_i]):
                            instant_booking = True
                            break
                        if sdt+relativedelta(hours=+experience.duration) < instantbooking_start[ib_i]:
                            #no need to check further slots after the current one
                            break
                        if sdt > instantbooking_start[ib_i]:
                            instantbooking_i += 1

                    dict = {'available_seat': experience.guest_number_max - i,
                            'date_string': sdt_local.strftime("%d/%m/%Y"),
                            'time_string': sdt_local.strftime("%H:%M"),
                            'datetime': sdt_local,
                            'instant_booking': instant_booking}

                    if instant_booking:
                        top_instant_bookings += 1

                    if instant_booking and top_instant_bookings < 3:
                        available_options.insert(top_instant_bookings, dict)
                    else:
                        available_options.append(dict)

                    if sdt_local.date() != last_sdt.date():
                        new_date = ((sdt_local.strftime("%d/%m/%Y"),
                                            sdt_local.strftime("%d/%m/%Y")),)
                        available_date += new_date
                        last_sdt = sdt_local

        #requirement change: all timeslots are considered available unless being explicitly blocked
        sdt += timedelta(hours=1)
        #if experience.repeat_cycle == "Hourly" :
        #    sdt += timedelta(hours=experience.repeat_frequency)
        #elif experience.repeat_cycle == "Daily" :
        #    sdt += timedelta(days=experience.repeat_frequency)
        #elif experience.repeat_cycle == "Weekly" :
        #    sdt += timedelta(weeks=experience.repeat_frequency)
        #else :
            #TODO
    return available_date

class ExperienceDetailView(DetailView):
    model = AbstractExperience
    template_name = 'experiences/experience_detail.html'
    #context_object_name = 'experience'

    def post(self, request, *args, **kwargs):
        #if not request.user.is_authenticated():
        #    return HttpResponseForbidden()

        self.object = self.get_object()

        if request.method == 'POST':
            form = BookingConfirmationForm(request.POST)
            form.data = form.data.copy()
            form.data['user_id'] = request.user.id
            form.data['first_name'] = request.user.first_name
            form.data['last_name'] = request.user.last_name
            experience = AbstractExperience.objects.get(id=form.data['experience_id'])
            experience.dollarsign = DollarSign[experience.currency.upper()]
            #experience.currency = str(dict(Currency)[experience.currency.upper()])#comment out on purpose --> stripe
            if type(experience) == Experience:
                experience.title = experience.get_title(settings.LANGUAGES[0][0])
            else:
                experience.title = experience.get_title(settings.LANGUAGES[0][0])
            experience_price = experience.price

            if float(experience.duration).is_integer():
                experience.duration = int(experience.duration)

            guest_number = int(form.data['guest_number'])
            subtotal_price = 0.0
            if experience.dynamic_price and type(experience.dynamic_price) == str:
                price = experience.dynamic_price.split(',')
                if len(price)+experience.guest_number_min-2 == experience.guest_number_max:
                #these is comma in the end, so the length is max-min+2
                    if guest_number <= experience.guest_number_min:
                        subtotal_price = float(experience.price) * float(experience.guest_number_min)
                    else:
                        subtotal_price = float(price[guest_number-experience.guest_number_min]) * float(guest_number)
                        experience_price = float(price[guest_number-experience.guest_number_min])
                    #if guest_number > experience.guest_number_min:
                    #    for p_index in range(1, guest_number-experience.guest_number_min+1):
                    #        subtotal_price += float(price[p_index])
                else:
                    #wrong dynamic settings
                    subtotal_price = float(experience.price)*float(form.data['guest_number'])
            else:
                subtotal_price = float(experience.price)*float(form.data['guest_number'])

            COMMISSION_PERCENT = round(experience.commission/(1-experience.commission),3)
            return render(request, 'experiences/experience_booking_confirmation.html',
                          {'form': form, #'eid':self.object.id,
                           'experience': experience,
                           'experience_price': experience_price,
                           'guest_number':form.data['guest_number'],
                           'date':form.data['date'],
                           'time':form.data['time'],
                           'subtotal_price':round(subtotal_price*(1.00+COMMISSION_PERCENT),0),
                           'service_fee':round(subtotal_price*(1.00+COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                           'total_price': experience_fee_calculator(subtotal_price, experience.commission),
                           'user_email':request.user.email,
                           'GEO_POSTFIX':settings.GEO_POSTFIX,
                           'LANGUAGE':settings.LANGUAGE_CODE,
                           'commission':COMMISSION_PERCENT + 1,
                           })

    def get_context_data(self, **kwargs):
        context = super(ExperienceDetailView, self).get_context_data(**kwargs)
        experience = context['experience'] if 'experience' in context else context['newproduct']
        if 'experience' not in context:
            context['experience'] = experience
            experience.type="PRODUCT"
        sdt = experience.start_datetime
        last_sdt = pytz.timezone('UTC').localize(datetime.min)
        local_timezone = pytz.timezone(settings.TIME_ZONE)
        available_options = []
        available_date = ()

        # Photo with minimum index will be cover photo.
        min_index = 11
        cover_photo = None
        # Get cover photo index.
        for photo in experience.photo_set.all():
            # Get photo index:
            index = int(photo.name.split("_")[1].split(".")[0])
            if index < min_index:
                min_index = index
                cover_photo = photo
        context['cover_photo'] = cover_photo

        if experience.end_datetime < datetime.utcnow().replace(tzinfo=pytz.UTC):
            if self.request.user.id != get_host(experience).id:
                # other user, experience already expired
                context['expired'] = True
                return context
            else:
                # host, experience already expired
                context['host_only_expired'] = True
                return context

        if not experience.status.lower() == "listed":
            owner_id = get_host(experience).id

            if self.request.user.id != owner_id and not self.request.user.is_superuser:
                # other user, experience not published
                context['listed'] = False
                return context
            else:
                # host, experience not published
                context['host_only_unlisted'] = True
                #return context

        context['experience_city'] = dict(Location).get(experience.city)

        available_date = getAvailableOptions(experience, available_options, available_date)

        context['available_options'] = available_options
        uid = self.request.user.id if self.request.user.is_authenticated() else None
        context['form'] = BookingForm(available_date, experience.id, uid)

        if float(experience.duration).is_integer():
            experience.duration = int(experience.duration)

        rate = 0.0
        counter = 0
        for review in experience.review_set.all():
            rate += review.rate
            counter += 1

        if counter > 0:
            rate /= counter
        context['experience_rate'] = math.ceil(rate)

        if self.request.user.is_authenticated():
            context["user_email"] = self.request.user.email

        if type(experience) is Experience:
            context["host_bio"] = get_user_bio(get_host(experience).registereduser, settings.LANGUAGES[0][0])
            host_image = get_host(experience).registereduser.image_url
            if host_image == None or len(host_image) == 0:
                context['host_image'] = 'profile_default.jpg'
            else:
                context['host_image'] = host_image

        context['in_wishlist'] = False
        wishlist = self.request.user.registereduser.wishlist.all() if self.request.user.is_authenticated() else None
        if wishlist and len(wishlist) > 0:
            for i in range(len(wishlist)):
                if wishlist[i].id == experience.id:
                    context['in_wishlist'] = True
                    break

        related_experiences = []
        cursor = connections['default'].cursor()
        cursor.execute("select experience_id from experiences_experience_guests where experience_id != %s and user_id in" +
                       "(select user_id from experiences_experience_guests where experience_id=%s)",
                             [experience.id, experience.id])
        ids = cursor.fetchall()
        if ids and len(ids)>0:
            for id in ids:
                related_experiences.append(id[0])
            related_experiences = list(Experience.objects.filter(id__in=related_experiences).filter(city__iexact=experience.city))
        if len(related_experiences)<3:
            cursor = connections['default'].cursor()
            cursor.execute("select experience_id from (select distinct experience_id, count(experiencetag_id)" +
                           "from experiences_experience_tags where experience_id!=%s and experiencetag_id in" +
                           "(SELECT experiencetag_id FROM experiences_experience_tags where experience_id=%s)" +
                           "group by experience_id order by count(experiencetag_id) desc) as t1", #LIMIT %s
                             [experience.id, experience.id])
            ids = cursor.fetchall()
            r_ids = []
            for i in range(len(ids)):
                r_ids.append(ids[i][0])

            queryset = Experience.objects.filter(id__in=r_ids).filter(city__iexact=experience.city).filter(status__iexact="listed")
            for exp in queryset:
                if not any(x.id == exp.id for x in related_experiences):
                    related_experiences.append(exp)
                if len(related_experiences)>=3:
                    break

        if len(related_experiences)<3:
            queryset = Experience.objects.filter(city__iexact=experience.city).filter(status__iexact="listed").order_by('?')[:3]
            for exp in queryset:
                related_experiences.append(exp)
                if len(related_experiences)>=3:
                    break

        for i in range(0,len(related_experiences)):
            related_experiences[i].dollarsign = DollarSign[related_experiences[i].currency.upper()]
            related_experiences[i].currency = str(dict(Currency)[related_experiences[i].currency.upper()])
            related_experiences[i].title = related_experiences[i].get_title(settings.LANGUAGES[0][0])
            related_experiences[i].description = related_experiences[i].get_description(settings.LANGUAGES[0][0])
            setExperienceDisplayPrice(related_experiences[i])
            if float(related_experiences[i].duration).is_integer():
                related_experiences[i].duration = int(related_experiences[i].duration)
            if related_experiences[i].commission > 0.0:
                related_experiences[i].commission = related_experiences[i].commission/(1-related_experiences[i].commission)+1
            else:
                related_experiences[i].commission = settings.COMMISSION_PERCENT+1

        related_experiences_added_to_wishlist = []

        if self.request.user.is_authenticated():
            for r in related_experiences:
                cursor.execute("select id from app_registereduser_wishlist where experience_id = %s and registereduser_id=%s",
                             [r.id,self.request.user.registereduser.id])
                wl = cursor.fetchone()
                if wl and len(wl)>0:
                    related_experiences_added_to_wishlist.append(True)
                else:
                    related_experiences_added_to_wishlist.append(False)
        else:
            for r in related_experiences:
                related_experiences_added_to_wishlist.append(False)

        context['related_experiences'] = zip(related_experiences, related_experiences_added_to_wishlist)

        experience.dollarsign = DollarSign[experience.currency.upper()]
        experience.currency = str(dict(Currency)[experience.currency.upper()])
        
        if type(experience) is Experience:
            experience.title = experience.get_title(settings.LANGUAGES[0][0])
            experience.description = experience.get_description(settings.LANGUAGES[0][0])
            experience.activity = get_experience_activity(experience, settings.LANGUAGES[0][0])
            experience.interaction = get_experience_interaction(experience, settings.LANGUAGES[0][0])
            experience.dress = get_experience_dress(experience, settings.LANGUAGES[0][0])
            experience.whatsincluded = get_experience_whatsincluded(experience, settings.LANGUAGES[0][0])
        else:
            if experience.newproducti18n_set is not None and len(experience.newproducti18n_set.all()) > 0:
                t = experience.newproducti18n_set.filter(language=settings.LANGUAGES[0][0])
                if len(t)>0:
                    t = t[0]
                else:
                    t = experience.newproducti18n_set.all()[0]

                experience.title = t.title
                experience.description = t.description
                experience.highlights = t.highlights
                experience.tips = t.tips
                experience.pickup_detail = t.pickup_detail
                experience.refund_policy = t.refund_policy
                experience.whatsincluded = t.whatsincluded

        if experience.commission > 0.0:
            experience.commission = round(experience.commission/(1-experience.commission),3)+1
        else:
            experience.commission = settings.COMMISSION_PERCENT+1

        context['GEO_POSTFIX'] = settings.GEO_POSTFIX
        context['LANGUAGE'] = settings.LANGUAGE_CODE
        context['wishlist_webservice'] = "https://" + settings.ALLOWED_HOSTS[0] + settings.GEO_POSTFIX + "service_wishlist/"
        return context

EXPERIENCE_IMAGE_SIZE_LIMIT = 2097152

@csrf_exempt
def experience_booking_successful(request, experience=None, guest_number=None, booking_datetime=None, price_paid=None, is_instant_booking=False, *args, **kwargs):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/")

    if (request.GET is None or len(request.GET) == 0) and experience is None:
        return HttpResponseRedirect(GEO_POSTFIX)

    data = request.GET
    if experience is None and data is not None:
        experience = Experience.objects.get(id=data['experience_id'])
        guest_number = int(data['guest_number'])
        booking_datetime = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(data['booking_datetime'], "%Y-%m-%d%H:%M"))
        price_paid = float(data['price_paid'])
        is_instant_booking = True if data['is_instant_booking'] == "True" else False

    mp = Mixpanel(settings.MIXPANEL_TOKEN)
    mp.track(request.user.email, 'Sent request to '+ get_host(experience).first_name)

    if not settings.DEVELOPMENT:
        mp = Mixpanel(settings.MIXPANEL_TOKEN)
        mp.track(request.user.email, 'Sent request to '+ get_host(experience).first_name)

    template = 'experiences/experience_booking_successful_requested.html'
    if is_instant_booking:
        template = 'experiences/experience_booking_successful_confirmed.html'

    if type(experience) == Experience:
        experience.title = experience.get_title(settings.LANGUAGES[0][0])
    else:
        experience.title = experience.get_title(settings.LANGUAGES[0][0])

    return render(request,template,{'experience': experience,
                                    'price_paid':price_paid,
                                    'guest_number':guest_number,
                                    'booking_datetime':booking_datetime,
                                    'user':request.user,
                                    'experience_url':'http://' + settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                    'GEO_POSTFIX':settings.GEO_POSTFIX,
                                    'LANGUAGE':settings.LANGUAGE_CODE})

def experience_booking_confirmation(request):
    # Get the context from the request.
    context = RequestContext(request)
    display_error = False

    if not request.user.is_authenticated():
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/")

    # A HTTP POST?
    if request.method == 'POST':
        form = BookingConfirmationForm(request.POST)
        experience = AbstractExperience.objects.get(id=form.data['experience_id'])
        experience.dollarsign = DollarSign[experience.currency.upper()]
        #experience.currency = str(dict(Currency)[experience.currency.upper()])#comment out on purpose --> stripe
        if type(experience) == Experience:
            experience.title = experience.get_title(settings.LANGUAGES[0][0])
            experience.meetup_spot = get_experience_meetup_spot(experience, settings.LANGUAGES[0][0])
        else:
            experience.title = experience.get_title(settings.LANGUAGES[0][0])

        guest_number = int(form.data['guest_number'])
        subtotal_price = 0.0
        experience_price = experience.price
        if experience.dynamic_price and type(experience.dynamic_price) == str:
            price = experience.dynamic_price.split(',')
            if len(price)+experience.guest_number_min-2 == experience.guest_number_max:
            #these is comma in the end, so the length is max-min+2
                if guest_number <= experience.guest_number_min:
                    subtotal_price = float(experience.price) * float(experience.guest_number_min)
                else:
                    subtotal_price = float(price[guest_number-experience.guest_number_min]) * float(guest_number)
                    experience_price = float(price[guest_number-experience.guest_number_min])
            else:
                #wrong dynamic settings
                subtotal_price = float(experience.price)*float(form.data['guest_number'])
        else:
            subtotal_price = float(experience.price)*float(form.data['guest_number'])
        COMMISSION_PERCENT = round(experience.commission/(1-experience.commission),3)
        total_price = experience_fee_calculator(subtotal_price, experience.commission)
        subtotal_price = round(subtotal_price*(1.00+COMMISSION_PERCENT),0)

        if 'Refresh' in request.POST:
            #get coupon information
            wrong_promo_code = False
            code = form.data['promo_code']
            bk_dt = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['date'].strip()+form.data['time'].strip(),"%Y-%m-%d%H:%M"))
            coupons = Coupon.objects.filter(promo_code__iexact = code,
                                            end_datetime__gt = bk_dt,
                                            start_datetime__lt = bk_dt)
            if not len(coupons):
                coupon = Coupon()
                wrong_promo_code = True
            else:
                valid = check_coupon(coupons[0], experience.id, form.data['guest_number'])
                if not valid['valid']:
                    coupon = Coupon()
                    wrong_promo_code = True
                else:
                    coupon = coupons[0]
                    total_price = valid['new_price']

            if not settings.DEVELOPMENT:
                mp = Mixpanel(settings.MIXPANEL_TOKEN)
                mp.track(request.user.email, 'Clicked on "Refresh"')

            return render_to_response('experiences/experience_booking_confirmation.html', {'form': form,
                                                                           'user_email':request.user.email,
                                                                           'wrong_promo_code':wrong_promo_code,
                                                                           'coupon':coupon,
                                                                           'experience': experience,
                                                                           'guest_number':form.data['guest_number'],
                                                                           'date':form.data['date'],
                                                                           'time':form.data['time'],
                                                                           'subtotal_price':subtotal_price,
                                                                           'experience_price':experience_price,
                                                                           'service_fee':round(subtotal_price*(1.00+COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                                                                           'total_price': total_price,
                                                                           'commission':1 + COMMISSION_PERCENT,
                                                                           'GEO_POSTFIX':settings.GEO_POSTFIX,
                                                                           'LANGUAGE':settings.LANGUAGE_CODE}, context)

        elif 'Stripe' in request.POST or 'stripeToken' in request.POST:
            #submit the form
            display_error = True
            if form.is_valid():
                request.user.registereduser.phone_number = form.cleaned_data['phone_number']
                request.user.registereduser.save()

                if form.cleaned_data['status'] == 'accepted':
                    return experience_booking_successful(request,
                                                         experience,
                                                         int(form.data['guest_number']),
                                                         datetime.strptime(form.data['date'] + " " + form.data['time'], "%Y-%m-%d %H:%M"),
                                                         form.cleaned_data['price_paid'], True)
                else:
                    return experience_booking_successful(request,
                                                         experience,
                                                         int(form.data['guest_number']),
                                                         datetime.strptime(form.data['date'] + " " + form.data['time'], "%Y-%m-%d %H:%M"),
                                                         form.cleaned_data['price_paid'])

            else:
                return render_to_response('experiences/experience_booking_confirmation.html', {'form': form,
                                                                           'user_email':request.user.email,
                                                                           'display_error':display_error,
                                                                           'experience': experience,
                                                                           'guest_number':form.data['guest_number'],
                                                                           'date':form.data['date'],
                                                                           'time':form.data['time'],
                                                                           'subtotal_price':subtotal_price,
                                                                           'experience_price':experience_price,
                                                                           'service_fee':round(subtotal_price*(1.00+COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                                                                           'total_price': total_price,
                                                                           'commission':1 + COMMISSION_PERCENT,
                                                                           'GEO_POSTFIX':settings.GEO_POSTFIX,
                                                                           'LANGUAGE':settings.LANGUAGE_CODE}, context)
        elif 'UnionPay' in request.POST:
            display_error = True
            order_id = make_order_id('Tripalocal')
            form.data = form.data.copy()
            form.data['booking_extra_information'] = order_id
            if form.is_valid():
                config = load_config(os.path.join(settings.PROJECT_ROOT, 'unionpay/settings.yaml').replace('\\', '/'))
                bk_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['date'].strip(), "%Y-%m-%d"))
                bk_time = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['time'].split(":")[0].strip(), "%H"))
                total_price = form.cleaned_data['price_paid'] if form.cleaned_data['price_paid'] != -1.0 else total_price

                if total_price > 0.0:
                    #not free
                    response = client.UnionpayClient(config).pay(int(total_price*100),order_id, channel_type='07',#currency_code=CurrencyCode[experience.currency.upper()],
                                                                 front_url='http://' + settings.ALLOWED_HOSTS[0] + '/experience_booking_successful/?experience_id=' + str(experience.id)
                                                                 + '&guest_number=' + form.data['guest_number']
                                                                 + '&booking_datetime=' + form.data['date'].strip()+form.data['time'].strip()
                                                                 + '&price_paid=' + str(total_price)
                                                                 + '&is_instant_booking=' + str(instant_booking(experience,bk_date,bk_time)))
                    return HttpResponse(response)
                else:
                    #free
                    return experience_booking_successful(request,
                                                         experience,
                                                         int(form.data['guest_number']),
                                                         datetime.strptime(form.data['date'] + " " + form.data['time'], "%Y-%m-%d %H:%M"),
                                                         form.cleaned_data['price_paid'],
                                                         instant_booking(experience,bk_date,bk_time))

            else:
                return render_to_response('experiences/experience_booking_confirmation.html', {'form': form,
                                                                           'user_email':request.user.email,
                                                                           'display_error':display_error,
                                                                           'experience': experience,
                                                                           'guest_number':form.data['guest_number'],
                                                                           'date':form.data['date'],
                                                                           'time':form.data['time'],
                                                                           'subtotal_price':subtotal_price,
                                                                           'experience_price':experience_price,
                                                                           'service_fee':round(subtotal_price*(1.00+COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                                                                           'total_price': total_price,
                                                                           'commission':1 + COMMISSION_PERCENT,
                                                                           'GEO_POSTFIX':settings.GEO_POSTFIX,
                                                                           'LANGUAGE':settings.LANGUAGE_CODE}, context)

        elif 'WeChat' in request.POST:
            display_error = True
            unified_pay = UnifiedOrderPay(settings.WECHAT_APPID, settings.WECHAT_MCH_ID, settings.WECHAT_API_KEY)
            from app.views import create_wx_trade_no
            out_trade_no = create_wx_trade_no(settings.WECHAT_MCH_ID)
            notify_url = request.build_absolute_uri(reverse('wechat_qr_payment_notify'))
            form.data = form.data.copy()
            form.data['booking_extra_information'] = out_trade_no

            if form.is_valid():
                bk_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['date'].strip(), "%Y-%m-%d"))
                bk_time = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['time'].split(":")[0].strip(), "%H"))
                total_price = form.cleaned_data['price_paid'] if form.cleaned_data['price_paid'] != -1.0 else total_price

                if total_price > 0.0:
                    #not free
                    # todo: remove stub money amout
                    pay_info = unified_pay.post(experience.get_title(settings.LANGUAGES[0][0]), out_trade_no,
                                                str(1), "127.0.0.1", notify_url)
                    if pay_info['return_code'] == 'SUCCESS' and pay_info['result_code'] == 'SUCCESS':
                        code_url = pay_info['code_url']
                        success_url = 'http://' + settings.ALLOWED_HOSTS[0] \
                                      + '/experience_booking_successful/?experience_id=' + str(experience.id) \
                                      + '&guest_number=' + form.data['guest_number'] \
                                      + '&booking_datetime=' + form.data['date'].strip() + form.data['time'].strip() \
                                      + '&price_paid=' + str(total_price) + '&is_instant_booking=' \
                                      + str(instant_booking(experience, bk_date, bk_time))

                        return redirect(url_with_querystring(reverse('wechat_qr_payment'), code_url=code_url,
                                                             out_trade_no=out_trade_no, success_url=success_url))
                    else:
                        return HttpResponse('<html><body>WeChat Payment Error.</body></html>')
                else:
                    #free
                    return experience_booking_successful(request,
                                                         experience,
                                                         int(form.data['guest_number']),
                                                         datetime.strptime(form.data['date'] + " " + form.data['time'], "%Y-%m-%d %H:%M"),
                                                         form.cleaned_data['price_paid'],
                                                         instant_booking(experience,bk_date,bk_time))

            else:
                return render_to_response('experiences/experience_booking_confirmation.html', {'form': form,
                                                                           'user_email':request.user.email,
                                                                           'display_error':display_error,
                                                                           'experience': experience,
                                                                           'guest_number':form.data['guest_number'],
                                                                           'date':form.data['date'],
                                                                           'time':form.data['time'],
                                                                           'subtotal_price':subtotal_price,
                                                                           'experience_price':experience_price,
                                                                           'service_fee':round(subtotal_price*(1.00+COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                                                                           'total_price': total_price,
                                                                           'commission':1 + COMMISSION_PERCENT,
                                                                           'GEO_POSTFIX':settings.GEO_POSTFIX,
                                                                           'LANGUAGE':settings.LANGUAGE_CODE}, context)

        else:
            #TODO
            #submit name missing in IE
            return HttpResponseRedirect(GEO_POSTFIX)
    else:
        # If the request was not a POST
        #form = BookingConfirmationForm()
        return HttpResponseRedirect(GEO_POSTFIX)


def url_with_querystring(path, **kwargs):
    return path + '?' + urlencode(kwargs)


def saveProfileImage(user, profile, image_file):
    content_type = image_file.content_type.split('/')[0]
    if content_type == "image":
        if image_file._size > PROFILE_IMAGE_SIZE_LIMIT:
            raise forms.ValidationError(_('Image size exceeds the limit'))
    else:
        raise forms.ValidationError(_('File type is not supported'))

    dirname = settings.MEDIA_ROOT + '/hosts/' + str(user.id) + '/'
    if not os.path.isdir(dirname):
        os.mkdir(dirname)

    name, extension = os.path.splitext(image_file.name)
    extension = extension.lower()
    if extension in ('.bmp', '.png', '.jpeg', '.jpg') :
        filename = ('host' + str(user.id) + '_1_' + user.first_name.title().strip() + user.last_name[:1].title() + extension).encode('ascii', 'ignore').decode('ascii')
        destination = open(dirname + filename, 'wb+')
        for chunk in image_file.chunks():
            destination.write(chunk)
        destination.close()
        profile.image_url = "hosts/" + str(user.id) + '/' + filename
        profile.image = profile.image_url
        profile.save()

        #crop the image
        im = Image.open(dirname + filename)
        w, h = im.size
        if w > 1200:
            basewidth = 1200
            wpercent = (basewidth/float(w))
            hsize = int((float(h)*float(wpercent)))
            im = im.resize((basewidth,hsize), PIL.Image.ANTIALIAS).save(dirname + filename)

        #copy to the other website -- folder+file
        if settings.LANGUAGES[0][0] == "en":
            dirname_other = settings.MEDIA_ROOT.replace("Tripalocal_V1","Tripalocal_CN") + '/hosts/' + str(user.id) + '/'
        elif settings.LANGUAGES[0][0] == "zh":
            dirname_other = settings.MEDIA_ROOT.replace("Tripalocal_CN","Tripalocal_V1") + '/hosts/' + str(user.id) + '/'

        if not os.path.isdir(dirname_other):
            os.mkdir(dirname_other)

        subprocess.Popen(['cp',dirname + filename, dirname_other + filename])

def saveExperienceImage(experience, photo, extension, index):
    filename = 'experience' + str(experience.id) + '_' + str(index) + extension
    dir_name = 'experiences/' + str(experience.id) + '/'

    photos = Photo.objects.filter(name=filename)
    if len(photos) != 0:
        ph = photos[0]
        photos[0].image.delete()
    else:
        ph = Photo(name=filename, directory=dir_name, experience=experience)

    ph.image = photo
    ph.save()

    #create the corresponding thumbnail (force .jpg)
    basewidth = 400
    thumb_file_name = 'thumbnails/experiences/experience' + str(experience.id) + '_' + str(index) + '.jpg'

    if storage.exists(thumb_file_name):
        storage.delete(thumb_file_name)
    try:
        f = storage.open(dir_name + filename, 'rb')
        img = Image.open(f)
        f_thumb = storage.open(thumb_file_name, "wb")
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
        img_out = BytesIO()
        img.save(img_out, format='JPEG')
        f_thumb.write(img_out.getvalue())
        f_thumb.close()
    except:
        #TODO
        pass

def updateExperience(experience, id, start_datetime, end_datetime, repeat_cycle, repeat_frequency, guest_number_min,
                   guest_number_max, price, currency, duration, city, status, language, dynamic_price,
                   title, description, activity, interaction, dress, meetup_spot, lan, lan2=None):
    experience.id = id
    experience.start_datetime = start_datetime
    experience.end_datetime = end_datetime
    experience.repeat_cycle = repeat_cycle
    experience.repeat_frequency = repeat_frequency
    experience.guest_number_min = guest_number_min
    experience.guest_number_max = guest_number_max
    experience.price = price
    experience.currency = currency
    experience.duration = duration
    experience.city = city
    experience.status = status
    experience.language = language
    experience.dynamic_price = dynamic_price

    experience.save()

    #save title
    t = experience.experiencetitle_set.filter(experience = experience, language=lan) if experience.experiencetitle_set is not None else None
    if t is not None and len(t):
        t[0].title = title
        t[0].save()
    else:
        t = ExperienceTitle(experience = experience, title = title, language = lan)
        t.save()
    if lan2 is not None:
        t = ExperienceTitle(experience = experience, title = title, language = lan2)
        t.save()

    #save description
    t = experience.experiencedescription_set.filter(experience = experience, language=lan) if experience.experiencedescription_set is not None else None
    if t is not None and len(t):
        t[0].description = description
        t[0].save()
    else:
        t = ExperienceDescription(experience = experience, description = description, language = lan)
        t.save()
    if lan2 is not None:
        t = ExperienceDescription(experience = experience, description = description, language = lan2)
        t.save()

    #save activity
    t = experience.experienceactivity_set.filter(experience = experience, language=lan) if experience.experienceactivity_set is not None else None
    if t is not None and len(t):
        t[0].activity = activity
        t[0].save()
    else:
        t = ExperienceActivity(experience = experience, activity = activity, language = lan)
        t.save()
    if lan2 is not None:
        t = ExperienceActivity(experience = experience, activity = activity, language = lan2)
        t.save()

    #save interaction
    t = experience.experienceinteraction_set.filter(experience = experience, language=lan) if experience.experienceinteraction_set is not None else None
    if t is not None and len(t):
        t[0].interaction = interaction
        t[0].save()
    else:
        t = ExperienceInteraction(experience = experience, interaction = interaction, language = lan)
        t.save()
    if lan2 is not None:
        t = ExperienceInteraction(experience = experience, interaction = interaction, language = lan2)
        t.save()

    #save dress
    t = experience.experiencedress_set.filter(experience = experience, language=lan) if experience.experiencedress_set is not None else None
    if t is not None and len(t):
        t[0].dress = dress
        t[0].save()
    else:
        t = ExperienceDress(experience = experience, dress = dress, language = lan)
        t.save()
    if lan2 is not None:
        t = ExperienceDress(experience = experience, dress = dress, language = lan2)
        t.save()

    #save meetup_spot
    t = experience.experiencemeetupspot_set.filter(experience = experience, language=lan) if experience.experiencemeetupspot_set is not None else None
    if t is not None and len(t):
        t[0].meetup_spot = meetup_spot
        t[0].save()
    else:
        t = ExperienceMeetupSpot(experience = experience, meetup_spot = meetup_spot, language = lan)
        t.save()
    if lan2 is not None:
        t = ExperienceMeetupSpot(experience = experience, meetup_spot = meetup_spot, language = lan2)
        t.save()

    return experience

def create_experience(request, id=None):
    context = RequestContext(request)
    data={}
    files={}
    display_error = False

    if not request.user.is_authenticated() or not request.user.is_staff:
        return HttpResponseRedirect(GEO_POSTFIX + "admin")

    if request.method == "GET":
        if id:
            # edit an experience
            experience = get_object_or_404(Experience, pk=id)
            if experience.currency is None:
                experience.currency = 'aud'
            host = get_host(experience)
            registerUser = host.registereduser
            list = experience.whatsincluded_set.filter(item="Food", language=settings.LANGUAGES[0][0])
            if len(list) > 0:
                if list[0].included:
                    included_food = "Yes"
                else:
                    included_food = "No"
                include_food_detail = list[0].details
            else:
                included_food = "No"
                include_food_detail = None

            list = experience.whatsincluded_set.filter(item="Ticket", language=settings.LANGUAGES[0][0])
            if len(list) > 0:
                if list[0].included:
                    included_ticket = "Yes"
                else:
                    included_ticket = "No"
                included_ticket_detail = list[0].details
            else:
                included_ticket = "No"
                included_ticket_detail = None

            list = experience.whatsincluded_set.filter(item="Transport", language=settings.LANGUAGES[0][0])
            if len(list) > 0:
                if list[0].included:
                    included_transport = "Yes"
                else:
                    included_transport = "No"
                included_transport_detail = list[0].details
            else:
                included_transport = "No"
                included_transport_detail = None

            if experience.price is None:
                experience.price = Decimal.from_float(0.0)

            if experience.commission is not None and experience.commission > 0:
                COMMISSION_PERCENT = round(experience.commission/(1-experience.commission),3)
            else:
                COMMISSION_PERCENT = settings.COMMISSION_PERCENT
            data = {"id":experience.id,
                "host":get_host(experience).email,
                "host_first_name":get_host(experience).first_name,
                "host_last_name":get_host(experience).last_name,
                "host_bio": get_user_bio(registerUser, settings.LANGUAGES[0][0]),
                "host_image":registerUser.image,
                "host_image_url":registerUser.image_url,
                "language":experience.language,
                "start_datetime":experience.start_datetime,
                "end_datetime":experience.end_datetime,
                #"repeat_cycle":experience.repeat_cycle,
                #"repeat_frequency":experience.repeat_frequency,
                "phone_number":registerUser.phone_number,
                "title":experience.get_title(settings.LANGUAGES[0][0]),
                "summary":experience.get_description(settings.LANGUAGES[0][0]),
                "guest_number_min":experience.guest_number_min,
                "guest_number_max":experience.guest_number_max,
                "price":round(experience.price,2),
                "price_with_booking_fee":round(experience.price*Decimal.from_float(1.00+COMMISSION_PERCENT), 0)*Decimal.from_float(1.00+settings.STRIPE_PRICE_PERCENT)+Decimal.from_float(settings.STRIPE_PRICE_FIXED),
                "currency":experience.currency.upper(),
                "duration":experience.duration,
                "included_food":included_food,
                "included_food_detail":include_food_detail,
                "included_ticket":included_ticket,
                "included_ticket_detail":included_ticket_detail,
                "included_transport":included_transport,
                "included_transport_detail":included_transport_detail,
                "activity":get_experience_activity(experience, settings.LANGUAGES[0][0]),
                "interaction":get_experience_interaction(experience, settings.LANGUAGES[0][0]),
                "dress_code":get_experience_dress(experience, settings.LANGUAGES[0][0]),
                "suburb":experience.city,
                "meetup_spot":get_experience_meetup_spot(experience, settings.LANGUAGES[0][0]),
                "status":experience.status,
                "dynamic_price":experience.dynamic_price
            }

            for i in range(1,MaxPhotoNumber+1):
                list = experience.photo_set.filter(name__startswith='experience'+str(id)+'_'+str(i))
                if len(list)>0:
                    photo = list[0]
                    data['experience_photo_'+str(i)+'_file_name'] = photo.name
                    data['experience_photo_'+str(i)] = photo.image

            for i in range(1,MaxIDImage+1):
                list = host.userphoto_set.filter(name__startswith='host_id'+str(host.id)+'_'+str(i))
                if len(list)>0:
                    photo = list[0]
                    data['host_id_photo_'+str(i)+'_file_name'] = photo.name
                    data['host_id_photo_'+str(i)] = photo.image

            photo = registerUser.image
            if photo:
                data['host_image_file_name'] = photo.name.split('/')[-1]
                data['host_image'] = photo
        else:
            #create a new experience
            experience = Experience()

        # Get payment calculation parameter.
        COMMISSION_PERCENT = round(experience.commission/(1-experience.commission),3)
        context['COMMISSION_PERCENT'] = COMMISSION_PERCENT
        context['STRIPE_PRICE_PERCENT'] = settings.STRIPE_PRICE_PERCENT
        context['STRIPE_PRICE_FIXED'] = settings.STRIPE_PRICE_FIXED

        # Set dynamic prices presentation logic:
        dynamic_pricing_items_number = 0
        max_dynamic_pricing_items = 10
        if experience.dynamic_price:
            prices = str(experience.dynamic_price).split(',')[:-1]
            context['dynamic_pricing_items'] = prices
            dynamic_pricing_items_number = prices.__len__()
        else:
            context['dynamic_pricing_items'] = []
            dynamic_pricing_items_number = 0

        context['dynamic_pricing_hidden_fields'] = range(dynamic_pricing_items_number + 1,11)
        form = CreateExperienceForm(data, files)

    elif request.method == 'POST':
        form = CreateExperienceForm(request.POST, request.FILES)
        display_error = True

        if form.is_valid():
            try:
                #check if the user exist
                user = User.objects.get(email=form.data['host'])
            except User.DoesNotExist:
                form.add_error("host","host email does not exist")
            return render_to_response('experiences/create_experience.html', {'form': form, 'display_error':display_error}, context)

            if not id:
                #create a new experience
                if len(Experience.objects.filter(id=form.data['id']))>0:
                    raise forms.ValidationError(_('Experience with the same Id already exists'))
                experience = Experience()
                lan2 = settings.LANGUAGES[1][0]
            else:
                #edit an experience
                experience = get_object_or_404(Experience, pk=id)
                lan2 = None

            experience = updateExperience(experience=experience,
                                        id=form.data['id'],
                                        start_datetime = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime("2015-01-01 00:00", "%Y-%m-%d %H:%M")).astimezone(pytz.timezone('UTC')),#form.data['start_datetime']
                                        end_datetime = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime("2025-01-01 00:00", "%Y-%m-%d %H:%M")).astimezone(pytz.timezone('UTC')),#form.data['end_datetime']
                                        repeat_cycle = "Hourly",
                                        repeat_frequency = 1,
                                        guest_number_min = form.data['guest_number_min'],
                                        guest_number_max = form.data['guest_number_max'],
                                        price = form.data['price'],
                                        currency = form.data['currency'].lower(),
                                        duration = form.data['duration'],
                                        city = form.data['suburb'],
                                        status = form.data['status'],
                                        language = form.data['language'],
                                        dynamic_price = form.data['dynamic_price'],

                                        title = form.data['title'],
                                        description = form.data['summary'],
                                        activity = form.data['activity'],
                                        interaction = form.data['interaction'],
                                        dress = form.data['dress_code'],
                                        meetup_spot = form.data['meetup_spot'],
                                        lan = settings.LANGUAGES[0][0],
                                        lan2 = lan2)

            #update experience-host relation
            cursor = connections['default'].cursor()
            cursor.execute("delete from experiences_experience_hosts where experience_id=%s", [experience.id])
            cursor.execute("Insert into experiences_experience_hosts (experience_id,user_id) values (%s, %s)", [experience.id, user.id])

            #update host information
            user = User.objects.get(email=form.data['host'])
            user.first_name = form.data['host_first_name']
            user.last_name = form.data['host_last_name']
            user.save()
            save_user_bio(user.registereduser, form.data['host_bio'], settings.LANGUAGES[0][0])
            user.registereduser.phone_number = form.data['phone_number']
            user.registereduser.save()

            #save experience images
            dirname = settings.MEDIA_ROOT + '/experiences/' + str(experience.id) + '/'
            if not os.path.isdir(dirname):
                os.mkdir(dirname)

            count = 0
            for index in range (1,MaxPhotoNumber+1):
                if 'experience_photo_'+str(index) in request.FILES:
                    content = request.FILES['experience_photo_'+str(index)]
                    content_type = content.content_type.split('/')[0]
                    if content_type == "image":
                        if content._size > EXPERIENCE_IMAGE_SIZE_LIMIT:
                            raise forms.ValidationError(_('Image size exceeds the limit'))
                    else:
                        raise forms.ValidationError(_('File type is not supported'))

                    #count += 1 #count does not necessarily equal index
                    name, extension = os.path.splitext(request.FILES['experience_photo_'+str(index)].name)
                    extension = extension.lower()
                    if extension in ('.bmp', '.png', '.jpeg', '.jpg') :
                        saveExperienceImage(experience, content, extension, index)

                        name = 'experience' + str(experience.id) + '_' + str(index)
                        if not len(experience.photo_set.filter(name__startswith=name))>0:
                            photo = Photo(name = filename, directory = 'experiences/' + str(experience.id) + '/',
                                          image = 'experiences/' + str(experience.id) + '/' + filename, experience = experience)
                            photo.save()
                        else:
                            photo = experience.photo_set.filter(name__startswith=name)[0]
                            photo.name = filename
                            photo.image = 'experiences/' + str(experience.id) + '/' + filename
                            photo.save()

            #save host's driver license images
            dirname = settings.MEDIA_ROOT + '/hosts_id/' + str(user.id) + '/'
            if not os.path.isdir(dirname):
                os.mkdir(dirname)

            count = 0
            for index in range (1,MaxIDImage+1):
                if 'host_id_photo_'+str(index) in request.FILES:
                    content = request.FILES['host_id_photo_'+str(index)]
                    content_type = content.content_type.split('/')[0]
                    if content_type == "image":
                        if content._size > EXPERIENCE_IMAGE_SIZE_LIMIT:
                            raise forms.ValidationError(_('Image size exceeds the limit'))
                    else:
                        raise forms.ValidationError(_('File type is not supported'))

                    #count += 1 #count does not necessarily equal index
                    name, extension = os.path.splitext(request.FILES['host_id_photo_'+str(index)].name)
                    extension = extension.lower()
                    if extension in ('.bmp', '.png', '.jpeg', '.jpg') :
                        filename = 'host_id' + str(user.id) + '_' + str(index) + extension
                        destination = open(dirname + filename, 'wb+')
                        for chunk in request.FILES['host_id_photo_'+str(index)].chunks():
                            destination.write(chunk)
                        destination.close()

                        #copy to the other website -- folder+file
                        if settings.LANGUAGES[0][0] == "en":
                            dirname_other = settings.MEDIA_ROOT.replace("Tripalocal_V1","Tripalocal_CN") + '/hosts_id/' + str(user.id) + '/'
                        elif settings.LANGUAGES[0][0] == "zh":
                            dirname_other = settings.MEDIA_ROOT.replace("Tripalocal_CN","Tripalocal_V1") + '/hosts_id/' + str(user.id) + '/'
                        if not os.path.isdir(dirname_other):
                            os.mkdir(dirname_other)
                        subprocess.Popen(['cp',dirname + filename, dirname_other + filename])

                        if not len(user.userphoto_set.filter(name__startswith=filename))>0:
                            photo = UserPhoto(name = filename, directory = 'hosts_id/' + str(user.id) + '/',
                                          image = 'hosts_id/' + str(user.id) + '/' + filename, user = user)
                            photo.save()

            #save profile image
            if 'host_image' in request.FILES:
                saveProfileImage(user, user.registereduser, request.FILES['host_image'])

            #add whatsincluded
            if not id:
                food = WhatsIncluded(item='Food', included = (form.data['included_food']=='Yes'),
                                     details = form.data['included_food_detail'],
                                     experience = experience, language=settings.LANGUAGES[0][0])
                ticket = WhatsIncluded(item='Ticket', included = (form.data['included_ticket']=='Yes'),
                                       details = form.data['included_ticket_detail'],
                                       experience = experience, language=settings.LANGUAGES[0][0])
                transport = WhatsIncluded(item='Transport', included = (form.data['included_transport']=='Yes'),
                                          details = form.data['included_transport_detail'],
                                          experience = experience, language=settings.LANGUAGES[0][0])
                food.save()
                ticket.save()
                transport.save()
                # make a copy for a second language
                food = WhatsIncluded(item='Food', included = (form.data['included_food']=='Yes'),
                                     details = form.data['included_food_detail'],
                                     experience = experience, language=settings.LANGUAGES[1][0])
                ticket = WhatsIncluded(item='Ticket', included = (form.data['included_ticket']=='Yes'),
                                       details = form.data['included_ticket_detail'],
                                       experience = experience, language=settings.LANGUAGES[1][0])
                transport = WhatsIncluded(item='Transport', included = (form.data['included_transport']=='Yes'),
                                          details = form.data['included_transport_detail'],
                                          experience = experience, language=settings.LANGUAGES[1][0])
                food.save()
                ticket.save()
                transport.save()
            else:
                if len(experience.whatsincluded_set.filter(item="Food", language=settings.LANGUAGES[0][0]))>0:
                    wh = WhatsIncluded.objects.get(id=experience.whatsincluded_set.filter(item="Food", language=settings.LANGUAGES[0][0])[0].id)
                    wh.included = (form.data['included_food']=='Yes')
                    wh.details = form.data['included_food_detail']
                    wh.save()
                else:
                    food = WhatsIncluded(item='Food',included = (form.data['included_food']=='Yes'),
                                         details = form.data['included_food_detail'],
                                         experience = experience, language=settings.LANGUAGES[0][0])
                    food.save()

                if len(experience.whatsincluded_set.filter(item="Ticket", language=settings.LANGUAGES[0][0]))>0:
                    wh = WhatsIncluded.objects.get(id=experience.whatsincluded_set.filter(item="Ticket", language=settings.LANGUAGES[0][0])[0].id)
                    wh.included = (form.data['included_ticket']=='Yes')
                    wh.details = form.data['included_ticket_detail']
                    wh.save()
                else:
                    ticket = WhatsIncluded(item='Ticket', included = (form.data['included_ticket']=='Yes'),
                                           details = form.data['included_ticket_detail'],
                                           experience = experience, language=settings.LANGUAGES[0][0])
                    ticket.save()

                if len(experience.whatsincluded_set.filter(item="Transport", language=settings.LANGUAGES[0][0]))>0:
                    wh = WhatsIncluded.objects.get(id=experience.whatsincluded_set.filter(item="Transport", language=settings.LANGUAGES[0][0])[0].id)
                    wh.included = (form.data['included_transport']=='Yes')
                    wh.details = form.data['included_transport_detail']
                    wh.save()
                else:
                    transport = WhatsIncluded(item='Transport', included = (form.data['included_transport']=='Yes'),
                                              details = form.data['included_transport_detail'],
                                              experience = experience, language=settings.LANGUAGES[0][0])
                    transport.save()

            return HttpResponseRedirect(GEO_POSTFIX + 'admin/experiences/experience/'+experience.id)

    return render_to_response('experiences/create_experience.html', {'form': form, 'display_error':display_error}, context)

def schedule_review_sms(customer_phone_num, host_name, review_schedule_time):
    if customer_phone_num:
        msg = _('%s' % REVIEW_NOTIFY_CUSTOMER).format(host_name=host_name)
        schedule_sms.apply_async([customer_phone_num, msg], eta=review_schedule_time)

def schedule_reminder_sms(guest, host, exp_title, customer_phone_num, reminder_scheduled_time, exp_datetime):
    registered_user = RegisteredUser.objects.get(user_id=host.id)
    host_phone_num = registered_user.phone_number

    if host_phone_num:
        msg = _('%s' % REMINDER_NOTIFY_HOST).format(exp_title=exp_title, customer_name=guest.first_name, exp_datetime=exp_datetime)
        schedule_sms.apply_async([host_phone_num, msg], eta=reminder_scheduled_time)

    if customer_phone_num:
        msg = _('%s' % REMINDER_NOTIFY_CUSTOMER).format(exp_title=exp_title, host_name=host.first_name, exp_datetime=exp_datetime)
        schedule_sms.apply_async([customer_phone_num, msg], eta=reminder_scheduled_time)

def update_booking(id, accepted, user):
    if id and accepted:
        booking = get_object_or_404(Booking, pk=id)
        if booking.status.lower() == "accepted":
            # the host already accepted the booking
            #messages.add_message(request, messages.INFO, 'The booking request has already been accepted.')
            booking_success = False
            result={'booking_success':booking_success, 'error':'the booking has been accepted'}
            return result

        if booking.status.lower() == "rejected":
            # the host/guest already rejected/cancelled the booking
            #messages.add_message(request, messages.INFO, 'The booking request has already been rejected.')
            booking_success = False
            result={'booking_success':booking_success, 'error':'the booking has been cancelled/rejected'}
            return result

        experience = Experience.objects.get(id=booking.experience_id)
        experience.title = experience.get_title(settings.LANGUAGES[0][0])
        experience.meetup_spot = get_experience_meetup_spot(experience, settings.LANGUAGES[0][0])
        if not get_host(experience).id == user.id:
            booking_success = False
            result={'booking_success':booking_success, 'error':'only the host can accept/reject the booking'}
            return result

        guest = User.objects.get(id = booking.user_id)
        host = user

        if accepted == "yes":
            booking.status = "accepted"
            booking.save()
            if booking.coupon_id != None and booking.coupon.promo_code.startswith("once"):
                #the coupon can be used once, make it unavailable
                booking.coupon.end_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC)
                booking.coupon.save()

            exp_title = experience.get_title(settings.LANGUAGE_CODE)
            customer_phone_num = booking.payment.phone_number
            exp_datetime_local = booking.datetime.astimezone(tzlocal())
            exp_datetime_local_str = exp_datetime_local.strftime(_("%H:%M %-d %b %Y"))

            send_booking_confirmed_sms(exp_datetime_local_str, exp_title, host, customer_phone_num, guest)

            #send an email to the traveller
            mail.send(subject=_('[Tripalocal] Booking confirmed'), message='',
                      sender=_('Tripalocal <') + Aliases.objects.filter(destination__contains=host.email)[0].mail + '>',
                      recipients=[Aliases.objects.filter(destination__contains=guest.email)[0].mail],
                      priority='now',  #fail_silently=False,
                      html_message=loader.render_to_string('experiences/email_booking_confirmed_traveler.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'user':guest, #not host --> need "my" phone number
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                            'LANGUAGE':settings.LANGUAGE_CODE}))


            reminder_scheduled_time = booking.datetime - timedelta(days=1)
            schedule_reminder_sms(guest, host, exp_title, customer_phone_num, reminder_scheduled_time, exp_datetime_local_str)

            #schedule an email to the traveller one day before the experience
            mail.send(subject=_('[Tripalocal] Booking reminder'), message='',
                      sender=_('Tripalocal <') + Aliases.objects.filter(destination__contains=host.email)[0].mail + '>',
                      recipients = [Aliases.objects.filter(destination__contains=guest.email)[0].mail],
                      priority='high',  scheduled_time = booking.datetime - timedelta(days=1),
                      html_message=loader.render_to_string('experiences/email_reminder_traveler.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'user':guest, #not host --> need "my" phone number
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                            'LANGUAGE':settings.LANGUAGE_CODE}))

            #schedule an email to the host one day before the experience
            mail.send(subject=_('[Tripalocal] Booking reminder'), message='',
                      sender=_('Tripalocal <') + Aliases.objects.filter(destination__contains=guest.email)[0].mail + '>',
                      recipients = [Aliases.objects.filter(destination__contains=host.email)[0].mail],
                      priority='high',  scheduled_time = booking.datetime - timedelta(days=1),
                      html_message=loader.render_to_string('experiences/email_reminder_host.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'user':guest,
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                            'LANGUAGE':settings.LANGUAGE_CODE}))

            review_scheduled_time = booking.datetime + timedelta(hours=experience.duration+1)
            schedule_review_sms(customer_phone_num, host.first_name, review_scheduled_time)

            #schedule an email for reviewing the experience
            mail.send(subject=_('[Tripalocal] How was your experience?'), message='',
                      sender=settings.DEFAULT_FROM_EMAIL,
                      recipients = [Aliases.objects.filter(destination__contains=guest.email)[0].mail],
                      priority='high',  scheduled_time = booking.datetime + timedelta(hours=experience.duration+1),
                      html_message=loader.render_to_string('experiences/email_review_traveler.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                            'review_url':settings.DOMAIN_NAME + '/reviewexperience/' + str(experience.id),
                                                            'LANGUAGE':settings.LANGUAGE_CODE}))

            #send an email to the host
            mail.send(subject=_('[Tripalocal] Booking confirmed'), message='',
                      sender=_('Tripalocal <') + Aliases.objects.filter(destination__contains=guest.email)[0].mail + '>',
                      recipients=[Aliases.objects.filter(destination__contains=host.email)[0].mail],
                      priority='now',  #fail_silently=False,
                      html_message=loader.render_to_string('experiences/email_booking_confirmed_host.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'user':guest,
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                            'LANGUAGE':settings.LANGUAGE_CODE}))
            email_template = 'experiences/email_booking_confirmed_host.html'
            booking_success = True

        elif accepted == "no":
            extra_fee = 0.00
            free = False

            if booking.coupon_id:
                extra = json.loads(booking.coupon.rules)
                if type(extra["extra_fee"]) == int or type(extra["extra_fee"]) == float:
                    extra_fee = extra["extra_fee"]
                elif type(extra["extra_fee"]) == str and extra["extra_fee"] == "FREE":
                    free = True

            if not free:
                payment = Payment.objects.get(booking_id=booking.id)

                guest_number = int(booking.guest_number)
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
                        subtotal_price = float(experience.price)*float(booking.guest_number)
                else:
                    subtotal_price = float(experience.price)*float(booking.guest_number)

                #refund_amount does not include process fee: the transaction can't be undone
                COMMISSION_PERCENT = round(experience.commission/(1-experience.commission),3)
                refund_amount = round(subtotal_price*(1+COMMISSION_PERCENT),0)

                if extra_fee <= -1:
                    refund_amount = round(subtotal_price*(1+COMMISSION_PERCENT), 0) + extra_fee
                if extra_fee < 0 and extra_fee > -1:
                    refund_amount = round(subtotal_price*(1+COMMISSION_PERCENT), 0) * (1+extra_fee)

                if payment.charge_id.startswith('ch_'):
                    #stripe
                    success, response = payment.refund(charge_id=payment.charge_id, amount=int(refund_amount*100))
                else:
                    #union pay
                    config = load_config(os.path.join(settings.PROJECT_ROOT, 'unionpay/settings.yaml').replace('\\', '/'))
                    response = client.UnionpayClient(config).refund(int(refund_amount*100),
                                                         payment.booking.booking_extra_information.replace("Tripalocal","UPRefund"),
                                                         payment.charge_id, '000201', '07')

                    success = True if response['respCode'] == '00' else False
                    if success:
                        booking.refund_id=response['queryId']
                        booking.save()
            else:
                success = True

            if success:
                booking.status = "rejected"
                booking.save()

                #send SMS
                exp_title = experience.get_title(settings.LANGUAGE_CODE)
                customer_phone_num = booking.payment.phone_number
                exp_datetime_local = booking.datetime.astimezone(tzlocal())
                exp_datetime_local_str = exp_datetime_local.strftime(_("%H:%M %d %b %Y"))
                send_booking_cancelled_sms(exp_datetime_local_str, exp_title, host, customer_phone_num, guest)
                
                #send an email to the traveller
                mail.send(subject=_('[Tripalocal] Your experience is cancelled'), message='',
                          sender=_('Tripalocal <') + Aliases.objects.filter(destination__contains=host.email)[0].mail + '>',
                          recipients=[Aliases.objects.filter(destination__contains=guest.email)[0].mail],
                          priority='now',  #fail_silently=False,
                          html_message=loader.render_to_string('experiences/email_booking_cancelled_traveler.html',
                                                                {'experience': experience,
                                                                'booking':booking,
                                                                'user':host,
                                                                'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                                'LANGUAGE':settings.LANGUAGE_CODE}))
                #send an email to the host
                mail.send(subject=_('[Tripalocal] Cancellation confirmed'), message='',
                          sender=_('Tripalocal <') + Aliases.objects.filter(destination__contains=guest.email)[0].mail + '>',
                          recipients=[Aliases.objects.filter(destination__contains=host.email)[0].mail],
                          priority='now',  #fail_silently=False,
                          html_message=loader.render_to_string('experiences/email_booking_cancelled_host.html',
                                                                {'experience': experience,
                                                                 'booking':booking,
                                                                 'user':guest,
                                                                 'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                                 'LANGUAGE':settings.LANGUAGE_CODE}))
                email_template = 'experiences/email_booking_cancelled_host.html'
                booking_success = True

            else:
                #TODO
                #ask the host to try again, or contact us
                #messages.add_message(request, messages.INFO, 'Please try to cancel the request later. Contact us if this happens again. Sorry for the inconvenience.')
                #return HttpResponseRedirect(GEO_POSTFIX)
                booking_success = False
        result={'booking_success':booking_success,'email_template':email_template if booking_success else '',
                'experience': experience, 'booking':booking, 'guest':guest,}
    #wrong format
    else:
        booking_success = False
        result={'booking_success':booking_success}

    return result

def send_booking_confirmed_sms(exp_datetime, exp_title, host, customer_phone_num, customer):
    registered_user = RegisteredUser.objects.get(user_id=host.id)
    host_phone_num = registered_user.phone_number

    if host_phone_num:
        msg = _('%s' % BOOKING_CONFIRMED_NOTIFY_HOST).format(exp_title=exp_title, customer_name=customer.first_name,
                                                             exp_datetime=exp_datetime)
        send_sms(host_phone_num, msg)

    if customer_phone_num:
        msg = _('%s' % BOOKING_CONFIRMED_NOTIFY_CUSTOMER).format(exp_title=exp_title, host_name=host.first_name,
                                                                 exp_datetime=exp_datetime)
        send_sms(customer_phone_num, msg)

def send_booking_cancelled_sms(exp_datetime, exp_title, host, customer_phone_num, customer):
    registered_user = RegisteredUser.objects.get(user_id=host.id)
    host_phone_num = registered_user.phone_number

    if host_phone_num:
        msg = _('%s' % BOOKING_CANCELLED_NOTIFY_HOST).format(exp_title=exp_title, customer_name=customer.first_name,
                                                             exp_datetime=exp_datetime)
        send_sms(host_phone_num, msg)

    if customer_phone_num:
        msg = _('%s' % BOOKING_CANCELLED_NOTIFY_CUSTOMER).format(exp_title=exp_title, host_name=host.first_name,
                                                                 exp_datetime=exp_datetime)
        send_sms(customer_phone_num, msg)

def booking_accepted(request, id=None):
    #TODO
    # respond within 48 hours?

    accepted = request.GET.get('accept')

    if not request.user.is_authenticated():
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/?next=" + GEO_POSTFIX + "booking/" + str(id) + "?accept="+accepted)

    form = SubscriptionForm()
    user = request.user

    result = update_booking(id, accepted, user)
    booking_success = result['booking_success']

    if booking_success:
        email_template = result['email_template']
        booking = result['booking']
        experience = result['experience']
        guest = result['guest']

        return render(request, email_template,
                        {'experience': experience,
                        'booking':booking,
                        'user':guest,
                        'experience_url':'http://' + settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                        'webpage':True})
    else:
        return HttpResponseRedirect(GEO_POSTFIX)

# Takes the experience primary key and returns the number of reviews it has received.
def getNReviews(experienceKey):
    #nReviews = 0
    reviewList = Review.objects.filter(experience_id=experienceKey)
    #for review in reviewList:
    #    if (review.experience.id == experienceKey):
    #        nReviews += 1

    return len(reviewList)

# Takes the experience primary key and returns the background image
def getBGImageURL(experienceKey):
    BGImageURL = ""
    photoList = Photo.objects.filter(experience_id=experienceKey)
    if len(photoList):
        BGImageURL = 'thumbnails/experiences/'+ photoList[0].name.split('.')[0] + '.jpg'
    return BGImageURL

def tagsOnly(tag, exp):
    experience_tags = exp.get_tags(settings.LANGUAGES[0][0])
    return tag in experience_tags

def getProfileImage(experience):
    profileImage = RegisteredUser.objects.get(user_id=get_host(experience).id).image_url
    if profileImage:
        return profileImage
    else:
        'profile_default.jpg'

def setExperienceDisplayPrice(experience):
    if experience.dynamic_price and len(experience.dynamic_price.split(',')) == experience.guest_number_max - experience.guest_number_min + 2 and experience.guest_number_min < 4:
        dp = experience.dynamic_price.split(',')
        if experience.guest_number_max < 4 or experience.guest_number_max - experience.guest_number_min < 4:
            experience.price = dp[len(dp)-2]#the string ends with ",", so the last one is ''
        elif experience.guest_number_min <= 4:
            experience.price = dp[4-experience.guest_number_min]

def setProductDisplayPrice(experience):
    #if experience.price_type == NewProduct.NORMAL:
    #    experience.price = experience.price
    #elif experience.price_type == NewProduct.AGE_PRICE:
    #    experience.price = experience.children_price
    #else:
    setExperienceDisplayPrice(experience)

def new_experience(request):
    context = RequestContext(request)
    form = ExperienceForm()

    if request.method == 'POST':
        form = ExperienceForm(request.POST)
        if form.is_valid():
            experience = Experience(start_datetime=datetime.utcnow().replace(tzinfo=pytz.UTC).replace(minute=0),
                                    end_datetime=datetime.utcnow().replace(tzinfo=pytz.UTC).replace(
                                        minute=0) + relativedelta(years=10),

                                    duration=form.cleaned_data['duration'],
                                    city=form.cleaned_data['location'],
                                    language="english;",
                                    guest_number_max=10,
                                    guest_number_min=1,
                                    status='Draft',
                                    currency='aud'
                                    )
            experience.save()
            experience.new_experience_i18n_info()
            user_id = None
            host = None
            if request.user.is_superuser:
                user_id = form.cleaned_data['user_id']
                if User.objects.filter(username=user_id).__len__() == 1:
                    host = User.objects.get(username=user_id)
                elif User.objects.filter(email=user_id).__len__() == 1:
                    host = User.objects.get(email=user_id)
                elif User.objects.filter(id=int(user_id)).__len__() == 1:
                    host = User.objects.get(id=int(user_id))
            else:
                user_id = request.user.id
                host = User.objects.get(id=user_id)
            experience.hosts.add(host)
            set_exp_title_all_langs(experience, form.cleaned_data['title'], LANG_EN, LANG_CN)
            #todo: add record to chinese database

            first_step = 'price'
            return redirect(reverse('manage_listing', kwargs={'exp_id': experience.id, 'step': first_step}))
    else:
        if request.user.is_superuser:
            data = {}
            data['user_id'] = request.user.username
            form = ExperienceForm(data=data)
            return render_to_response('new_experience.html', {'form': form}, context)
        return render_to_response('new_experience.html', {'form': form}, context)

def manage_listing_price(request, experience, context):
    if request.method == 'GET':
        data = {}
        data['min_guest_number'] = experience.guest_number_min
        data['max_guest_number'] = experience.guest_number_max
        data['duration'] = experience.duration
        data['price'] = experience.price
        data['dynamic_price'] = experience.dynamic_price
        data['type'] = experience.type
        data['currency'] = experience.currency
        COMMISSION_PERCENT = round(experience.commission/(1-experience.commission),3)
        if experience.price != None:
            data['price_with_booking_fee'] = round(float(experience.price) * (1.00 + COMMISSION_PERCENT), 2)
        form = ExperiencePriceForm(initial=data)

        return render_to_response('price_form.html', {'form': form}, context)
    elif request.method == 'POST':
        form = ExperiencePriceForm(request.POST)
        if form.is_valid():
            if 'dynamic_price' in form.data:
                experience.dynamic_price = form.cleaned_data['dynamic_price']
            if 'min_guest_number' in form.data:
                experience.guest_number_min = form.cleaned_data['min_guest_number']
            if 'max_guest_number' in form.data:
                experience.guest_number_max = form.cleaned_data['max_guest_number']
            if 'duration' in form.data:
                experience.duration = form.cleaned_data['duration']
            if 'price' in form.data:
                experience.price = form.cleaned_data['price']
            if 'type' in form.data:
                experience.type = form.cleaned_data['type']
            if 'currency' in form.data:
                experience.currency = form.cleaned_data['currency']

            # todo: add to chinese db
            experience.save()
            return HttpResponse(json.dumps({'success': True}), content_type='application/json')

def manage_listing_overview(request, experience, context):
    if request.method == 'GET':
        data = {}
        data['title'] = experience.get_title(LANG_EN)
        data['summary'] = experience.get_description(LANG_EN)
        data['language'] = experience.language

        data['title_other'] = experience.get_title(LANG_CN)
        data['summary_other'] = experience.get_description(LANG_CN)

        form = ExperienceOverviewForm(initial=data)

        return render_to_response('overview_form.html', {'form': form}, context)

    elif request.method == 'POST':
        form = ExperienceOverviewForm(request.POST)
        if form.is_valid():
            if 'title' in form.data:
                title = form.cleaned_data['title']
                set_exp_title_all_langs(experience, title, LANG_EN, LANG_CN)
            if 'title_other' in form.data:
                title_other = form.cleaned_data['title_other']
                set_exp_title(experience, title_other, LANG_CN)

            if 'summary' in form.data:
                description = form.cleaned_data['summary']
                set_exp_desc_all_langs(experience, description, LANG_EN, LANG_CN)
            if 'summary_other' in form.data:
                description_other = form.cleaned_data['summary_other']
                set_exp_description(experience, description_other, LANG_CN)
            if 'language' in form.data:
                experience.language = form.cleaned_data['language']

        experience.save()
        return HttpResponse(json.dumps({'success': True}), content_type='application/json')

def manage_listing_detail(request, experience, context):
    if request.method == 'GET':
        data = {}
        data['activity'] = get_experience_activity(experience, LANG_EN)
        data['interaction'] = get_experience_interaction(experience, LANG_EN)
        data['dress_code'] = get_experience_dress(experience, LANG_EN)

        data['activity_other'] = get_experience_activity(experience, LANG_CN)
        data['interaction_other'] = get_experience_interaction(experience, LANG_CN)
        data['dress_code_other'] = get_experience_dress(experience, LANG_CN)


        includes = get_experience_whatsincluded(experience, LANG_EN)
        set_response_exp_includes_detail(data, includes)
        set_response_exp_includes(data, includes)
        includes_other_lang = get_experience_whatsincluded(experience, LANG_CN)
        set_response_exp_includes_detail_other_lang(data, includes_other_lang)

        form = ExperienceDetailForm(initial=data)

        return render_to_response('detail_form.html', {'form': form}, context)

    elif request.method == 'POST':
        form = ExperienceDetailForm(request.POST)
        if form.is_valid():
            if 'activity' in form.data:
                set_exp_activity_all_langs(experience, form.cleaned_data['activity'], LANG_EN, LANG_CN)
            if 'interaction' in form.data:
                set_exp_interaction_all_langs(experience, form.cleaned_data['interaction'], LANG_EN, LANG_CN)
            if 'dress_code' in form.data:
                set_exp_dress_all_langs(experience, form.cleaned_data['dress_code'], LANG_EN, LANG_CN)

            if 'activity_other' in form.data:
                set_exp_activity(experience, form.cleaned_data['activity_other'], LANG_CN)
            if 'interaction_other' in form.data:
                set_exp_interaction(experience, form.cleaned_data['interaction_other'], LANG_CN)
            if 'dress_code_other' in form.data:
                set_exp_dress(experience, form.cleaned_data['dress_code_other'], LANG_CN)

            if 'included_food' in form.data:
                is_food_included = form.cleaned_data['included_food'] == 'Yes'
                set_experience_includes(experience, 'Food', is_food_included, LANG_EN)
                set_experience_includes(experience, 'Food', is_food_included, LANG_CN)
            if 'included_transport' in form.data:
                is_transport_included = form.cleaned_data['included_transport'] == 'Yes'
                set_experience_includes(experience, 'Transport', is_transport_included, LANG_EN)
                set_experience_includes(experience, 'Transport', is_transport_included, LANG_CN)
            if 'included_ticket' in form.data:
                is_ticket_included = form.cleaned_data['included_ticket'] == 'Yes'
                set_experience_includes(experience, 'Ticket', is_ticket_included, LANG_EN)
                set_experience_includes(experience, 'Ticket', is_ticket_included, LANG_CN)


            if 'included_food_detail' in form.data:
                set_exp_includes_detail_all_langs(experience, 'Food', form.cleaned_data['included_food_detail'],
                                                  LANG_EN, LANG_CN)
            if 'included_transport_detail' in form.data:
                set_exp_includes_detail_all_langs(experience, 'Transport', form.cleaned_data['included_transport_detail'],
                                                  LANG_EN, LANG_CN)
            if 'included_ticket_detail' in form.data:
                set_exp_includes_detail_all_langs(experience, 'Ticket', form.cleaned_data['included_ticket_detail'],
                                                  LANG_EN, LANG_CN)

            if 'included_food_detail_other' in form.data:
                set_exp_includes_detail(experience, 'Food', form.cleaned_data['included_food_detail_other'], LANG_CN)
            if 'included_transport_detail_other' in form.data:
                set_exp_includes_detail(experience, 'Transport', form.cleaned_data['included_transport_detail_other'],
                                        LANG_CN)
            if 'included_ticket_detail_other' in form.data:
                set_exp_includes_detail(experience, 'Ticket', form.cleaned_data['included_ticket_detail_other'],
                                        LANG_CN)
            experience.save()

        return HttpResponse(json.dumps({'success': True}), content_type='application/json')

def manage_listing_photo(request, experience, context):

    if request.method == 'GET':
        data = {}
        photo_indexes = ''
        photo_list = []
        photos = Photo.objects.filter(experience_id = experience.id)
        for index in range(len(photos)):
            photo_index = photos[index].name.split('_')[-1].split('.')[0]
            data['experience_photo_' + photo_index] = photos[index]
            data['experience_photo_' + photo_index + '_file_name'] = photos[index].name
            data['id'] = experience.id
            photo_list = photo_list + [photo_index]
        photo_list.sort()
        if photo_list:
            for photo_index in photo_list:
                photo_indexes = photo_indexes + photo_index  + ','
        data['photo_indexes'] = photo_indexes
        form = ExperiencePhotoForm(data)
        return render_to_response('photo_form.html', {'form': form}, context)

    elif request.method == 'POST':
        form = ExperiencePhotoForm(request.POST, request.FILES)
        if 'delete_file' in request.POST:
            index = request.POST['delete_file']
            extension = '.jpg'
            filename = 'experience' + str(experience.id) + '_' + str(index) + extension

            photo = Photo.objects.filter(name=filename)
            if photo.__len__() == 1:
                photo[0].image.delete()
                thumb_file_name = 'thumbnails/experiences/' + filename
                storage.delete(thumb_file_name)

                photo[0].delete()
                return HttpResponse(json.dumps({'success': True, 'data': 'delete_image', 'index':index}), content_type='application/json')
            else:
                return HttpResponse(json.dumps({'success': False}), content_type='application/json')

        if form.is_valid():
            for index in range(1, 11):
                field_name = 'experience_photo_' + str(index)

                if field_name in request.FILES:
                    file = request.FILES[field_name]
                    if file._size > EXPERIENCE_IMAGE_SIZE_LIMIT:
                            raise forms.ValidationError(_('Image size exceeds the limit'))
                    extension = '.jpg'
                    filename = 'experience' + str(experience.id) + '_' + str(index) + extension
                    dir_name = 'experiences/' + str(experience.id) + '/'

                    photos = Photo.objects.filter(name=filename)
                    if len(photos) != 0:
                        photo = photos[0]
                        photos[0].image.delete()
                    else:
                        photo = Photo(name=filename, directory=dir_name, experience=experience)


                    photo.image = file
                    photo.save()

                    #create the corresponding thumbnail (force .jpg)
                    basewidth = 400
                    thumb_file_name = 'thumbnails/experiences/experience' + str(experience.id) + '_' + str(index) + '.jpg'

                    if storage.exists(thumb_file_name):
                        storage.delete(thumb_file_name)
                    try:
                        f = storage.open(dir_name + filename, 'rb')
                        img = Image.open(f)
                        f_thumb = storage.open(thumb_file_name, "wb")
                        wpercent = (basewidth / float(img.size[0]))
                        hsize = int((float(img.size[1]) * float(wpercent)))
                        img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                        img_out = BytesIO()
                        img.save(img_out, format='JPEG')
                        f_thumb.write(img_out.getvalue())
                        f_thumb.close()
                    except:
                        return HttpResponse(json.dumps({'success': False}), content_type='application/json')


            experience.save()
        return HttpResponse(json.dumps({'success': True}), content_type='application/json')

def manage_listing_location(request, experience, context):
    if request.method == 'GET':
        data = {}
        data['meetup_spot'] =  get_experience_meetup_spot(experience, LANG_EN)
        data['meetup_spot_other'] =  get_experience_meetup_spot(experience, LANG_CN)
        data['dropoff_spot'] =  get_experience_dropoff_spot(experience, LANG_EN)
        data['dropoff_spot_other'] =  get_experience_dropoff_spot(experience, LANG_CN)
        data['suburb'] =  experience.city

        form = ExperienceLocationForm(initial=data)

        return render_to_response('location_form.html', {'form': form}, context)

    elif request.method == 'POST':
        form = ExperienceLocationForm(request.POST)
        if form.is_valid():
            if 'meetup_spot' in form.data:
                set_exp_meetup_spot_all_langs(experience, form.cleaned_data['meetup_spot'], LANG_EN, LANG_CN)
            if 'meetup_spot_other' in form.data:
                set_exp_meetup_spot(experience, form.cleaned_data['meetup_spot_other'], LANG_CN)
            if 'suburb' in form.data:
                experience.city = form.cleaned_data['suburb']
            if 'dropoff_spot' in form.data:
                set_exp_dropoff_spot_all_langs(experience, form.cleaned_data['dropoff_spot'], LANG_EN, LANG_CN)
            if 'dropoff_spot_other' in form.data:
                set_exp_dropoff_spot(experience, form.cleaned_data['dropoff_spot_other'], LANG_CN)

            experience.save()
        return HttpResponse(json.dumps({'success': True}), content_type='application/json')

def manage_listing_calendar(request, experience, context):
    if request.method == 'GET':
        return render_to_response('calendar_form.html', {}, {})
    elif request.method == 'POST':
        return HttpResponse(json.dumps({'success': True}), content_type='application/json')
    pass

def check_upload_filled(experience):
    result = ''
    # check pricing.
    if experience.price:
        result+='1'
    else:
        result+='0'
    #check overview.
    if experience.get_title(LANG_EN) and experience.get_description(LANG_EN):
        result+='1'
    else:
        result+='0'
    #check detail.
    if get_experience_activity(experience, LANG_EN) and get_experience_whatsincluded(experience, LANG_EN):
        result+='1'
    else:
        result+='0'
    #check photo.
    photos = Photo.objects.filter(experience_id = experience.id)
    for index in range(len(photos)):
        photo_index = photos[index].name.split('_')[-1].split('.')[0]
        if photo_index == '1':
            result+='1'

    if result.__len__() == 3:
        result+='0'
    #check location
    if get_experience_meetup_spot(experience, LANG_EN) and get_experience_dropoff_spot(experience, LANG_EN):
        result+='1'
    else:
        result+='0'
    return result

def manage_listing(request, exp_id, step, ):
    experience = get_object_or_404(Experience, pk=exp_id)
    if not request.user.is_superuser:
        if request.user.id != get_host(experience).id:
            raise Http404("Sorry, but you can only edit your own experience.")

    experience_title_cn = get_object_or_404(ExperienceTitle, experience_id=exp_id, language='zh')
    experience_title_en = get_object_or_404(ExperienceTitle, experience_id=exp_id, language='en')

    context = RequestContext(request)
    context['experience_title_cn'] = experience_title_cn
    context['experience_title_en'] = experience_title_en
    context['experience'] = experience
    context['experience_finished'] = check_upload_filled(experience)
    context['experience_status'] = experience.status

    if request.is_ajax():
        # Check submit operation.
        if 'submit_form' in request.POST:
            experience.status = 'Submitted'
            experience.save()
        if step == 'price':
            return manage_listing_price(request, experience, context)
        elif step == 'overview':
            return manage_listing_overview(request, experience, context)
        elif step == 'detail':
            return manage_listing_detail(request, experience, context)
        elif step == 'photo':
            return manage_listing_photo(request, experience, context)
        elif step == 'location':
            return manage_listing_location(request, experience, context)
        elif step == 'calendar':
            return manage_listing_calendar(request, experience, context)

    else:
        return render_to_response('manage_listing.html', context)

def manage_listing_continue(request, exp_id):
    exp = get_object_or_404(Experience, pk=exp_id)

    price_fields = [exp.duration, exp.guest_number_min, exp.guest_number_max, exp.type]
    lang = settings.LANGUAGES[0][0]
    overview_fields = [exp.get_title(lang), exp.get_description(lang), exp.language]
    detail_fields = [get_experience_activity(exp, lang), get_experience_interaction(exp, lang),
                     get_experience_dress(exp, lang)]
    location_fields = [exp.city, get_experience_meetup_spot(exp, lang)]

    if None in price_fields or "" in price_fields:
        return redirect(reverse('manage_listing', kwargs={'exp_id': exp.id, 'step': 'price'}))

    if None in overview_fields or "" in overview_fields:
        return redirect(reverse('manage_listing', kwargs={'exp_id': exp.id, 'step': 'overview'}))

    if None in detail_fields or "" in detail_fields:
        return redirect(reverse('manage_listing', kwargs={'exp_id': exp.id, 'step': 'detail'}))

    if exp.photo_set.count() == 0:
        return redirect(reverse('manage_listing', kwargs={'exp_id': exp.id, 'step': 'photo'}))

    whats_included_list = WhatsIncluded.objects.filter(experience=exp)
    included_list = whats_included_list.filter(included=True)
    not_included_list = whats_included_list.filter(included=False)

    for field in included_list:
        if field.details == "":
            return redirect(reverse('manage_listing', kwargs={'exp_id': exp.id, 'step': 'details'}))

    if None in location_fields or "" in location_fields:
        return redirect(reverse('manage_listing', kwargs={'exp_id': exp.id, 'step': 'location'}))

    return redirect(reverse('manage_listing', kwargs={'exp_id': exp.id, 'step': 'location'}))

def SearchView(request, city, start_date=datetime.utcnow().replace(tzinfo=pytz.UTC), end_date=datetime.max.replace(tzinfo=pytz.UTC), guest_number=None, language=None, keywords=None,
               is_kids_friendly=False, is_host_with_cars=False, is_private_tours=False,  type='s'):

    form = SearchForm()
    form.data = form.data.copy()
    form.data['city'] = city.title()
    form.data['all_tags'] = Tags
    if 'language' not in form.data:
        form.data['language'] = "English,Mandarin" if language is None else language

    if request.method == 'POST':
        form = SearchForm(request.POST)
        form.data = form.data.copy()
        form.data['all_tags'] = Tags
        if 'language' not in form.data:
            form.data['language'] = "English,Mandarin" if language is None else language

        if form.is_valid():
            city = form.cleaned_data['city']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            guest_number = form.cleaned_data['guest_number']
            language = form.cleaned_data['language']
            keywords = form.cleaned_data['tags']
            is_kids_friendly = form.cleaned_data['is_kids_friendly']
            is_host_with_cars = form.cleaned_data['is_host_with_cars']
            is_private_tours = form.cleaned_data['is_private_tours']

    rateList = []
    cityExperienceList = []
    cityExperienceReviewList = []
    formattedTitleList = []
    BGImageURLList = []
    profileImageURLList = []
    cityList= list(Location)
    city_display_name = None
    for i in range(len(cityList)):
        if cityList[i][0].lower() == city.lower():
            city_display_name = cityList[i][1]
            city = cityList[i][0]
            break

    if request.is_ajax():
        if type == 'product':
            experienceList = NewProduct.objects.filter(city__iexact=city, status__iexact="listed")
        else:
            experienceList = Experience.objects.filter(city__iexact=city, status__iexact="listed").exclude(
                type__iexact="itinerary")

        # Add all experiences that belong to the specified city to a new list
        # alongside a list with all the number of reviews
        # experienceList = Experience.objects.filter(city__iexact=city, status__iexact="listed").exclude(type__iexact="itinerary")

            if is_kids_friendly:
                experienceList = [exp for exp in experienceList if tagsOnly(_("Kids Friendly"), exp)]
            if is_host_with_cars:
                experienceList = [exp for exp in experienceList if tagsOnly(_("Host with Car"), exp)]
            if is_private_tours:
                experienceList = [exp for exp in experienceList if tagsOnly(_("Private group"), exp)]

        i = 0
        while i < len(experienceList):
            experience = experienceList[i]
            experience.commission = round(experience.commission/(1-experience.commission),3)+1

            if type == 'product':
                setProductDisplayPrice(experience)

            else:
                setExperienceDisplayPrice(experience)
                experience_tags = experience.get_tags(settings.LANGUAGES[0][0])
                if keywords is not None and len(keywords) > 0 and len(experience_tags) > 0:
                    tags = keywords.strip().split(",")
                    match = False
                    for tag in tags:
                        if tag.strip() in experience_tags:
                            match = True
                            break
                    if not match:
                        i += 1
                        continue

            if start_date is not None and experience.end_datetime < start_date :
                i += 1
                continue

            if end_date is not None and experience.start_datetime > end_date:
                i += 1
                continue

            if guest_number is not None and len(guest_number) > 0 and \
                    experience.guest_number_max  and experience.guest_number_max < int(guest_number):
                i += 1
                continue


            if language is not None and len(language) > 0 and experience.language is not None and len(experience.language) > 0:
                experience_language = experience.language.split(";")
                experience_language = [x.lower() for x in experience_language]
                languages = language.split(",")
                match = False
                for l in languages:
                    if l.lower() in experience_language:
                        match = True
                        break
                if not match:
                    i += 1
                    continue

            if not experience.currency:
                experience.currency = 'aud'
            experience.dollarsign = DollarSign[experience.currency.upper()]
            experience.currency = str(dict(Currency)[experience.currency.upper()])

            rate = 0.0
            counter = 0

            photoset = experience.photo_set.all()
            if type != 'product':
                image_url = get_host(experience).registereduser.image_url

                if photoset!= None and len(photoset) > 0 and image_url != None and len(image_url) > 0:
                    for review in experience.review_set.all():
                        rate += review.rate
                        counter += 1
                else:
                    rate = -1

                if counter > 0:
                    rate /= counter

                #find the correct index to insert --> sort the list by rate
                counter = 0
                if len(rateList) == 0:
                    rateList.append(rate)
                    counter = 0
                else:
                    for counter in range(0, len(rateList)):
                        if rateList[counter] < rate:
                            rateList.insert(counter, rate)
                            break
                        elif rateList[counter] > rate:
                            counter += 1
                            if counter == len(rateList):
                                rateList.append(rate)
                                break
                        else:
                            # == --> check instant booking time, unavailable time
                            if len(experience.instantbookingtimeperiod_set.all()) > 0:
                                #the exp has set instant booking
                                while counter < len(rateList) and rateList[counter] == rate and len(cityExperienceList[counter].instantbookingtimeperiod_set.all()) > 0:
                                    counter += 1
                                if counter == len(rateList):
                                    rateList.append(rate)
                                else:
                                    rateList.insert(counter, rate)
                                break
                            elif not len(experience.blockouttimeperiod_set.all()) > 0:
                                #the exp has neither set instant booking nor blockout time
                                while counter < len(rateList) and rateList[counter] == rate:
                                    counter += 1
                                if counter == len(rateList):
                                    rateList.append(rate)
                                else:
                                    rateList.insert(counter, rate)
                                break
                            else:
                                #the exp has set blockout time
                                while counter < len(rateList) and rateList[counter] == rate:
                                    if len(cityExperienceList[counter].instantbookingtimeperiod_set.all()) > 0 or len(cityExperienceList[counter].blockouttimeperiod_set.all()) > 0:
                                        counter += 1
                                    else:
                                        break
                                if counter == len(rateList):
                                    rateList.append(rate)
                                else:
                                    rateList.insert(counter, rate)
                                break

            cityExperienceList.insert(counter, experience)
            cityExperienceReviewList.insert(counter, getNReviews(experience.id))
            # Fetch BGImageURL
            BGImageURL = getBGImageURL(experience.id)
            if (BGImageURL):
                BGImageURLList.insert(counter, BGImageURL)
            else:
                BGImageURLList.insert(counter, "default_experience_background.jpg")

            if type != 'product':
                # Fetch profileImageURL
                profileImageURL = RegisteredUser.objects.get(user_id=get_host(experience).id).image_url
                if (profileImageURL):
                    profileImageURLList.insert(counter, profileImageURL)
                else:
                    profileImageURLList.insert(counter, "profile_default.jpg")

            # Format title & Description
            experience.description = experience.get_description(settings.LANGUAGES[0][0])
            t = experience.get_title(settings.LANGUAGES[0][0])


            if float(experience.duration).is_integer():
                experience.duration = int(experience.duration)

            if (t != None and len(t) > 40):
                formattedTitleList.insert(counter, t[:37] + "...")
            else:
                formattedTitleList.insert(counter, t)

            i += 1

        if not settings.DEVELOPMENT:
            mp = Mixpanel(settings.MIXPANEL_TOKEN)

            if request.user.is_authenticated():
                mp.track(request.user.email,"Viewed " + city.title() + " search page")
            #else:
            #    mp.track("","Viewed " + city.title() + " search page")

        template = 'experiences/experience_results.html'
    else:
        template = 'experiences/search_result.html'

    context = RequestContext(request, {
                            'city' : city,
                            'city_display_name':city_display_name if city_display_name is not None else city.title(),
                            'length':len(cityExperienceList),
                            'cityExperienceList' : itertools.zip_longest(cityExperienceList, formattedTitleList, BGImageURLList, profileImageURLList),
                            'cityList':cityList,
                            'user_email':request.user.email if request.user.is_authenticated() else None,
                            'locations' : Locations,
                            'LANGUAGE':settings.LANGUAGE_CODE,
                            'GEO_POSTFIX': GEO_POSTFIX,
                            'type': type,
        })
    return render_to_response(template, {'form': form}, context)

def userHasLeftReview (user, experience):
    hasLeftReview = False
    reviewsByUser = Review.objects.filter(user=user, experience=experience)
    if reviewsByUser:
        hasLeftReview = True
    return hasLeftReview

def review_experience (request, id=None):
    if id:
        if not request.user.is_authenticated():
            return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/?next=" + GEO_POSTFIX + "reviewexperience/"+str(id))

        # get experience object
        experience = get_object_or_404(Experience, pk=id)
        # get user
        user = request.user
        # check if the user booked this experience
        bookings = experience.booking_set.filter(experience_id=experience.id, user_id=user.id, status__iexact="accepted",
                                                 datetime__lt=datetime.utcnow().replace(tzinfo=pytz.UTC)+relativedelta(hours=-experience.duration)).order_by('-datetime')

        # Check review hasn't been left already
        hasLeftReview = False
        hasLeftReview = userHasLeftReview(user, experience)

        context = RequestContext(request, {})
        context['hasLeftReview'] = hasLeftReview

        if bookings:
            context['hasBookedExperience'] = True
        else:
            context['hasBookedExperience'] = False

        if (bookings and not hasLeftReview):
            context['experience'] = experience
            bookings[0].datetime = bookings[0].datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
            context['booking'] = bookings[0]

            if request.method == 'POST':
                form = ReviewForm(request.POST)

                if form.is_valid():
                    review = Review()
                    review.user = user
                    review.experience = experience
                    review.comment = form.cleaned_data['comment']
                    review.rate = form.cleaned_data['rate']
                    review.personal_comment = form.cleaned_data['personal_comment']
                    review.operator_comment = form.cleaned_data['operator_comment']
                    review.datetime = datetime.utcnow().replace(tzinfo=pytz.UTC)
                    review.save()

                    return render_to_response('experiences/review_experience_success.html', {'home_url':'http://'+settings.ALLOWED_HOSTS[0]+settings.GEO_POSTFIX}, context)
            else:
                form = ReviewForm()
        else:
            form = ReviewForm()

        context['LANGUAGE'] = settings.LANGUAGE_CODE
        return render_to_response('experiences/review_experience.html', {'form': form}, context)
    else:
        return HttpResponseRedirect(GEO_POSTFIX)

def get_experience_score(criteria_dict, experience_tags):
    '''
    @criteria_dict: a dict {}
    @experience_tag: a list []
    '''

    score = 0
    for tag in experience_tags:
        score += criteria_dict.get(tag, 0)
    return score

def get_itinerary(type, start_datetime, end_datetime, guest_number, city, language, keywords=None, mobile=False, sort=1):
    '''
    @sort, 1:most popular, 2:outdoor, 3:urban
    '''

    available_options = get_available_experiences(type, start_datetime, end_datetime, guest_number, city, language, keywords)
    itinerary = []
    dt = start_datetime

    city = city.lower().split(",")
    if not isEnglish(city[0]):
        for i in range(len(city)):
            city[i] = dict(Location_reverse).get(city[i]).lower()

    day_counter = 0

    if sort == 2:
        config = load_config(os.path.join(settings.PROJECT_ROOT, 'experiences/outdoor.yaml').replace('\\', '/'))
    elif sort == 3:
        config = load_config(os.path.join(settings.PROJECT_ROOT, 'experiences/urban.yaml').replace('\\', '/'))
    else:
        config = load_config(os.path.join(settings.PROJECT_ROOT, 'experiences/popularity.yaml').replace('\\', '/'))

    for experience in available_options:
        experience['popularity'] = get_experience_score(config, experience['tags'])*0.9 + experience['popularity']*0.1

    #available_options: per experience --> itinerary: per day
    while dt <= end_datetime:
        dt_string = dt.strftime("%Y/%m/%d")
        day_dict = {'date':dt_string, 'city':city[day_counter], 'experiences':[]}

        for experience in available_options:
            if experience['city'].lower() != city[day_counter]:
                continue

            if dt_string in experience['dates'] and len(experience['dates'][dt_string]) > 0:
                #check instant booking
                instant_booking = False
                for timeslot in experience['dates'][dt_string]:
                    if timeslot['instant_booking']:
                        instant_booking = True
                        break
                counter = 0
                insert = False

                exp_dict = experience
                exp_dict['instant_booking'] = instant_booking
                if not mobile:
                    exp_dict['timeslots'] = experience['dates'][dt_string]

                experience['dates'][dt_string] = {}

                while counter < len(day_dict['experiences']):#find the correct rank
                    if experience['popularity'] > day_dict['experiences'][counter]['popularity']:
                        day_dict['experiences'].insert(counter, exp_dict)
                        insert = True
                        break
                    elif experience['popularity'] == day_dict['experiences'][counter]['popularity']:
                        if instant_booking:
                            #same popularity, instant booking
                            index1 = counter
                            while counter < len(day_dict['experiences']) and experience['popularity'] == day_dict['experiences'][counter]['popularity'] and day_dict['experiences'][counter]['instant_booking']:
                                counter += 1
                            index2 = counter

                        else:
                            #same popularity, instant booking
                            while counter < len(day_dict['experiences']) and experience['popularity'] == day_dict['experiences'][counter]['popularity'] and day_dict['experiences'][counter]['instant_booking']:
                                counter += 1
                            index1 = counter
                            #same popularity, non instant booking
                            while counter < len(day_dict['experiences']) and experience['popularity'] == day_dict['experiences'][counter]['popularity']:
                                counter += 1
                            index2 = counter

                        counter = int((index2-index1)*random.uniform(0,1) + index1)

                        if counter < len(day_dict['experiences']):
                            day_dict['experiences'].insert(counter, exp_dict)
                        else:
                            day_dict['experiences'].append(exp_dict)
                        insert = True
                        break
                    else:
                        counter += 1
                if not insert:
                    day_dict['experiences'].append(exp_dict)

        itinerary.append(day_dict)
        dt += timedelta(days=1)
        day_counter += (1 if len(city) > 1 else 0)

    return itinerary

def custom_itinerary(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/?next=" + GEO_POSTFIX + "itinerary")

    context = RequestContext(request)
    context['locations'] = Locations
    context['LANGUAGE'] = settings.LANGUAGE_CODE
    form = CustomItineraryForm()

    if request.method == 'POST':
        form = CustomItineraryForm(request.POST)

        if 'Search' in request.POST:
            if form.is_valid():
                start_datetime = form.cleaned_data['start_datetime']
                end_datetime = form.cleaned_data['end_datetime']
                end_datetime = end_datetime.replace(hour=22)
                guest_number = form.cleaned_data['guest_number']
                city = form.cleaned_data['city']
                language = form.cleaned_data['language']
                tags = form.cleaned_data['tags']
                sort = int(form.cleaned_data['sort'])

                if isinstance(tags, list):
                    tags = ','.join(tags)
                elif not isinstance(tags,str):
                    raise TypeError("Wrong format: keywords. String or list expected.")

                itinerary = get_itinerary("ALL", start_datetime, end_datetime, guest_number, city, language, tags, False, sort)

                return render_to_response('experiences/custom_itinerary.html', {'form':form,'itinerary':itinerary}, context)
            else:
                return render_to_response('experiences/custom_itinerary.html', {'form':form}, context)
        else:
            #submit bookings
            if form.is_valid():
                itinerary = json.loads(form.cleaned_data['itinerary_string'])
                booking_form = ItineraryBookingForm(request.POST)
                booking_form.data = booking_form.data.copy()
                booking_form.data['user_id'] = request.user.id
                booking_form.data['experience_id'] = ""
                booking_form.data['date'] = ""
                booking_form.data['time'] = ""
                booking_form.data['status'] = "Requested"

                workbook = xlsxwriter.Workbook(os.path.join(os.path.join(settings.PROJECT_ROOT,'itineraries'), 'Itinerary.xlsx'))
                worksheet = workbook.add_worksheet()
                city = form.cleaned_data['city']
                city = city.split(',')
                row = -1
                last_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime("2000/01/01", "%Y/%m/%d"))
                i=-1
                week_day = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
                total_price = 0.0
                guest_number = 1

                for item in itinerary:
                    booking_form.data['experience_id'] += str(item['id']) + ";"
                    booking_form.data['date'] += str(item['date']) + ";"
                    booking_form.data['time'] += str(item['time']) + ";"
                    booking_form.data['guest_number'] = item['guest_number']

                    experience = AbstractExperience.objects.get(id=str(item['id']))
                    price = experience_fee_calculator(float(experience.price), experience.commission)
                    total_price += price*int(item['guest_number'])
                    guest_number = int(item['guest_number'])

                    #save to excel sheet
                    cell_format = workbook.add_format({'text_wrap': True})
                    current_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(str(item['date']), "%Y/%m/%d"))
                    if current_date > last_date:
                        #a new day
                        row += 1
                        i += 1
                        #date
                        col = 0
                        worksheet.write(row, col, str(item['date']))
                        #day of week
                        col += 1
                        worksheet.write(row, col, week_day[current_date.weekday()])
                        #number of people
                        col += 1
                        worksheet.write(row, col, item['guest_number'])
                        #accommdation
                        col += 1
                        worksheet.write(row, col, '')
                        #city
                        col += 1
                        worksheet.write(row, col, city[i])
                        #title, url
                        col += 1
                        worksheet.write(row, col, item['title'] + "\n" + "https://"+settings.ALLOWED_HOSTS[0]+"/experience/"+item['id'], cell_format)
                        #price pp
                        col += 1
                        worksheet.write(row, col, price)
                        last_date = current_date
                    else:
                        row += 1
                        col = 5
                        worksheet.write(row, col, item['title'] + "\n" + "https://"+settings.ALLOWED_HOSTS[0]+"/experience/"+item['id'], cell_format)
                        #price pp
                        col += 1
                        worksheet.write(row, col, price)

                row += 1
                col = 0
                worksheet.write(row, col, "Total price:")
                col += 1
                worksheet.write(row, col, total_price)
                col += 1
                worksheet.write(row, col, "Price per person:")
                col += 1
                worksheet.write(row, col, total_price/guest_number)
                workbook.close()
                return HttpResponseRedirect("https://"+settings.ALLOWED_HOSTS[0]+"/itineraries/Itinerary.xlsx")

                #return render(request, 'experiences/itinerary_booking_confirmation.html',
                #          {'form': booking_form,'itinerary':itinerary})

    return render_to_response('experiences/custom_itinerary.html', {'form':form}, context)

def itinerary_booking_confirmation(request):
    context = RequestContext(request)
    display_error = False

    if not request.user.is_authenticated():
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/")

    # A HTTP POST?
    if request.method == 'POST':
        form = ItineraryBookingForm(request.POST)
        #experience = Experience.objects.get(id=form.data['experience_id'])

        #guest_number = int(form.data['guest_number'])
        #subtotal_price = 0.0
        #if experience.dynamic_price and type(experience.dynamic_price) == str:
        #    price = experience.dynamic_price.split(',')
        #    if len(price)+experience.guest_number_min-2 == experience.guest_number_max:
        #    #these is comma in the end, so the length is max-min+2
        #        if guest_number <= experience.guest_number_min:
        #            subtotal_price = float(experience.price) * float(experience.guest_number_min)
        #        else:
        #            subtotal_price = float(price[guest_number-experience.guest_number_min]) * float(guest_number)
        #    else:
        #        #wrong dynamic settings
        #        subtotal_price = float(experience.price)*float(form.data['guest_number'])
        #else:
        #    subtotal_price = float(experience.price)*float(form.data['guest_number'])

        if 'Refresh' in request.POST:
            #get coupon information
            wrong_promo_code = False
            code = form.data['promo_code']
            dates = form.data['date'].split(";")
            times = form.data['time'].split(";")
            dates = [x for x in dates if x]
            times = [x for x in times if x]
            date_start = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(dates[0] + " " + times[0].split(":")[0].strip(), "%Y/%m/%d %H"))
            date_end = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(dates[len(dates)-1] + " " + times[len(dates)-1].split(":")[0].strip(), "%Y/%m/%d %H"))

            coupons = Coupon.objects.filter(promo_code__iexact = code,
                                            end_datetime__gt = date_end,
                                            start_datetime__lt = date_start)
            if not len(coupons):
                coupon = Coupon()
                wrong_promo_code = True
            else:
                #TODO
                wrong_promo_code = False

            #mp = Mixpanel(settings.MIXPANEL_TOKEN)
            #mp.track(request.user.email, 'Clicked on "Refresh"')

            return render_to_response('experiences/itinerary_booking_confirmation.html', {'form': form,}, context)

        else:
            #submit the form
            display_error = True
            if form.is_valid():
                return itinerary_booking_successful(request)

            else:
                return render_to_response('experiences/itinerary_booking_confirmation.html', {'form': form,
                                                                           'display_error':display_error,}, context)
    else:
        # If the request was not a POST
        #form = BookingConfirmationForm()
        return HttpResponseRedirect(GEO_POSTFIX)

def set_response_exp_includes(data, includes):
    for index in range(len(includes)):
        if includes[index].item == "Food":
            if includes[index].included:
                data['included_food'] = "Yes"
            else:
                data['included_food'] = "No"
        elif includes[index].item == "Transport":
            if includes[index].included:
                data['included_transport'] = "Yes"
            else:
                data['included_transport'] = "No"
        elif includes[index].item == "Ticket":
            if includes[index].included:
                data['included_ticket'] = "Yes"
            else:
                data['included_ticket'] = "No"

def set_response_exp_includes_detail(data, includes):
    for index in range(len(includes)):
        if includes[index].item == "Food":
            data['included_food_detail'] = includes[index].details
        elif includes[index].item == "Transport":
            data['included_transport_detail'] = includes[index].details
        elif includes[index].item == "Ticket":
            data['included_ticket_detail'] = includes[index].details

def set_response_exp_includes_detail_other_lang(data, includes):
    for index in range(len(includes)):
        if includes[index].item == "Food":
            data['included_food_detail_other'] = includes[index].details
        elif includes[index].item == "Transport":
            data['included_transport_detail_other'] = includes[index].details
        elif includes[index].item == "Ticket":
            data['included_ticket_detail_other'] = includes[index].details

#TODO: add the template
def itinerary_booking_successful(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/")

    return render(request,'experiences/itinerary_booking_successful.html',{})

def multi_day_trip(request):
    experienceList = Experience.objects.filter(status='Listed', type='ITINERARY')
    i=0
    while i < len(experienceList):
        experience = experienceList[i]

        setExperienceDisplayPrice(experience)

        experience.image = getBGImageURL(experience.id)

        if not experience.currency:
            experience.currency = 'aud'
        experience.dollarsign = DollarSign[experience.currency.upper()]
        experience.currency = str(dict(Currency)[experience.currency.upper()])

        # Format title & Description
        experience.description = experience.get_description(settings.LANGUAGES[0][0])
        t = experience.get_title(settings.LANGUAGES[0][0])
        if (t != None and len(t) > 30):
            experience.title = t[:27] + "..."
        else:
            experience.title = t
        i+=1
    template = "experiences/multi_day_trip.html"
    context = RequestContext(request, {
                            'experienceList' : experienceList,
                            'user_email':request.user.email if request.user.is_authenticated() else None,
                            'LANGUAGE':settings.LANGUAGE_CODE,
                            'GEO_POSTFIX': GEO_POSTFIX,
              })
    return render_to_response(template, {}, context)

@csrf_exempt
def unionpay_payment_callback(request):
    import logging
    logger = logging.getLogger("Tripalocal_V1")
    #logger.debug(request.POST)

    ret = request.POST

    if ret is not None:
        try:
            config = load_config(os.path.join(settings.PROJECT_ROOT, 'unionpay/settings.yaml').replace('\\', '/'))
            s = signer.Signer.getSigner(config)
            s.validate(ret)

            if ret.get('respCode', '') == '00':
                #success
                bk = Booking.objects.filter(booking_extra_information=ret['orderId'], status="requested")
                if bk is not None and len(bk)>0:
                    bk = bk[0]
                    bk.status="paid"
                    bk.save()

                    payment = bk.payment
                    payment.charge_id = ret['queryId']
                    payment.street1 = ret['txnTime']
                    payment.save()

                    experience = Experience.objects.get(id=bk.experience_id)
                    user = User.objects.get(id=bk.user_id)
                    bk.datetime = bk.datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
                    send_booking_email_verification(bk, experience, user, 
                                                    instant_booking(experience, bk.datetime.date(), bk.datetime.time()))
                    sms_notification(bk, experience, user, payment.phone_number)
                logger.debug("payment success:"+str(ret['orderId']))
                pass
            else:
                #failure
                #TODO
                #logger.debug("failure")
                pass
        except Exception as err:
            logger.debug(err)

@csrf_exempt
def unionpay_refund_callback(request):
    import logging
    logger = logging.getLogger("Tripalocal_V1")
    #logger.debug(request.POST)

    ret = request.POST

    if ret is not None:
        try:
            config = load_config(os.path.join(settings.PROJECT_ROOT, 'unionpay/settings.yaml').replace('\\', '/'))
            s = signer.Signer.getSigner(config)
            s.validate(ret)

            if ret.get('respCode', '') == '00':
                #success
                logger.debug("refund success:"+ret['queryId'])
                pass
            else:
                #failure
                #TODO
                #logger.debug("failure")
                pass
        except Exception as err:
            logger.debug(err)


def wechat_qr_payment(request):
    code_url = request.GET.get('code_url')
    out_trade_no = request.GET.get('out_trade_no')
    success_url = request.GET.get('success_url')
    return render_to_response('experiences/wechat_qr_payment.html',
                              {'code_url': code_url,
                               'out_trade_no': out_trade_no,
                               'success_url': success_url},
                              RequestContext(request))


def wechat_qr_payment_query(request, out_trade_no):
    order_query = OrderQuery(settings.WECHAT_APPID, settings.WECHAT_MCH_ID, settings.WECHAT_API_KEY)
    pay_info = order_query.post(out_trade_no)
    if pay_info['return_code'] == 'SUCCESS' and pay_info['result_code'] == 'SUCCESS':
        trade_state = pay_info['trade_state']
        if trade_state == 'SUCCESS':
            return HttpResponse(json.dumps({'order_paid': True}))
        else:
            return HttpResponse(json.dumps({'order_paid': False}))

    else:
        return HttpResponse(json.dumps({'order_paid': False}))
    # return render_to_response('experiences/wechat_qr_payment.html',
    #                           {'code_url': code_url,
    #                            'out_trade_no': out_trade_no},
    #                           RequestContext(request))
    pass


@csrf_exempt
def wechat_qr_payment_notify(request):
    if (request.body):
        notify_info = xmltodict.parse(request.body.decode("utf-8"))['xml']
        if (notify_info.get('return_code', None)) == 'SUCCESS':
            out_trade_no = notify_info['out_trade_no']
            transaction_id = notify_info['transaction_id']

            bks = Booking.objects.filter(booking_extra_information=out_trade_no, status="requested")
            if len(bks) > 0:
                bk = bks[0]
                bk.status = "paid"
                bk.save()

                payment = bk.payment
                payment.charge_id = transaction_id
                payment.save()

                experience = Experience.objects.get(id=bk.experience_id)
                user = User.objects.get(id=bk.user_id)
                bk.datetime = bk.datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
                send_booking_email_verification(bk, experience, user,
                                                instant_booking(experience, bk.datetime.date(), bk.datetime.time()))
                sms_notification(bk, experience, user, payment.phone_number)
            xml = dict_to_xml({'return_code': 'SUCCESS', 'return_msg': 'OK'})
            return HttpResponse(xml)
    else:
        return HttpResponse('')
