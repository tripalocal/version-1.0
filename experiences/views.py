from io import BytesIO
from urllib.parse import urlencode, unquote
from app.wechat_payment.api import UnifiedOrderPay, OrderQuery, Refund
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
import collections
from django.db.models import Q
from experiences.utils import *
from copy import deepcopy
from import_from_partners.utils import *
from django.contrib.auth import authenticate, login

MaxPhotoNumber=10
PROFILE_IMAGE_SIZE_LIMIT = 1048576
MaxIDImage=5

LANG_CN = settings.LANGUAGES[1][0]
LANG_EN = settings.LANGUAGES[0][0]
GEO_POSTFIX = settings.GEO_POSTFIX
TYPE_PUBLIC = ['NONPRIVATE','PublicProduct']

def set_initial_currency(request):
    if 'custom_currency' not in request.session:
        if settings.LANGUAGES[0][0] == "zh":
            request.session["custom_currency"] = "CNY"
            request.session["dollar_sign"] = "￥"
        else:
            #TODO
            request.session["custom_currency"] = "AUD"
            request.session["dollar_sign"] = "$"

def convert_experience_price(request, experience):
    if hasattr(request, 'session') and 'custom_currency' in request.session\
        and experience.currency.lower() != request.session['custom_currency'].lower():
        experience.price = convert_currency(experience.price, experience.currency, request.session['custom_currency'])

        if experience.dynamic_price and type(experience.dynamic_price) == str:
            price = experience.dynamic_price.split(',')
            if len(price)+experience.guest_number_min-2 == experience.guest_number_max:
            #these is comma in the end, so the length is max-min+2
                new_dynamic_price=""
                for i in range(len(price)-1):
                    price[i] = convert_currency(float(price[i]), experience.currency, request.session['custom_currency'])
                    new_dynamic_price += str(price[i]) + ","
                experience.dynamic_price = new_dynamic_price

        experience.currency = request.session['custom_currency']

    if hasattr(experience, "optiongroup_set") and len(experience.optiongroup_set.all()) > 0:
        optiongroup_set = []
        for option in experience.optiongroup_set.filter(language=settings.LANGUAGES[0][0]):
            og = {"name":option.name, "optionitem_set":[]}
            for item in option.optionitem_set.all():
                if hasattr(request, 'session') and 'custom_currency' in request.session and request.session['custom_currency'].lower() != "aud":
                    og["optionitem_set"].append({"name":item.name, "original_id":item.original_id, "price":convert_currency(item.price, "aud", request.session['custom_currency'])})
                else:
                    og["optionitem_set"].append({"name":item.name, "original_id":item.original_id, "price":item.price})
            optiongroup_set.append(og)
        return optiongroup_set
    else:
        return None

def next_time_slot(experience, repeat_cycle, repeat_frequency, repeat_extra_information, current_datetime, daylightsaving):
    #TODO:always return the next time slot in the future, even if "current_datetime" is earlier than now
    #daylightsaving: whether it was in daylightsaving when this blockout/instant booking record was created
    current_datetime_local = current_datetime.astimezone(pytz.timezone(experience.get_timezone()))

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

def sort_experiences(experiences, customer=None, preference=None):
    '''
    @customer: sort the experiences based on the auto-collected data of the customer
    @preference: sort the experiences based on the specified preference (a dict read from configuration files)
    otherwise, sort the experiences based on the overall reviews and pageview statistics
    '''
    pageview_max = 0
    match_max = 0
    bookings_max = 0
    rate_max = 0

    experiences = list(experiences)
    pageview_records = list(UserPageViewStatistics.objects.filter(experience__in=experiences))
    bookings = list(Booking.objects.filter(experience__in=experiences))

    for experience in experiences:
        #criterion 1: pageview (user only, or overall)
        if customer is not None:
            records = [r for r in pageview_records if r.user==customer and r.experience==experience]
        else:
            records = [r for r in pageview_records if r.experience.id==experience.id]

        experience.pageview = 0.0
        for r in records:
            experience.pageview += r.times_viewed * r.average_length
            if experience.pageview > pageview_max:
                pageview_max = experience.pageview

        #criterion 2: user preference
        if preference is not None:
            experience.match = get_experience_score(preference, experience.get_tags(settings.LANGUAGES[0][0]))
            if experience.match > match_max:
                match_max = experience.match

        #criterion 3: booking numbers
        bks = [b for b in bookings if b.experience_id == experience.id]
        if bks is not None:
            bks = len(bks)
        else:
            bks = 0
        experience.bookings = bks
        if bks > bookings_max:
            bookings_max = bks

        #criterion 4: reviews
        #put experiences without images to the end
        counter = 0
        experience.rate = 0.0
        photoset = experience.photo_set.all()
        if photoset!= None and len(photoset) > 0:
            for review in experience.review_set.all():
                experience.rate += review.rate
                counter += 1
        else:
            experience.rate = -1
        if counter > 0:
            experience.rate /= counter
        if experience.rate > rate_max:
            rate_max = experience.rate

    sorted = 0
    for experience in experiences:
        experience.popularity = 0.0
        #normalize
        #popularoity = a*pageview+b*match+c*bookings+d*review
        #sort by popularity
        if pageview_max > 0 and hasattr(experience, 'pageview'):
            experience.pageview = float(experience.pageview/pageview_max)

        if match_max > 0 and hasattr(experience, 'match'):
            experience.match = float(experience.match/match_max)

        if bookings_max > 0 and hasattr(experience, 'bookings'):
            experience.bookings = float(experience.bookings/bookings_max)

        if rate_max > 0 and hasattr(experience, 'rate'):
            experience.rate = float(experience.rate/rate_max)

        if customer:
            experience.popularity += 4*experience.pageview + 5*experience.match + 1*experience.bookings + 1*experience.rate
        else:
            experience.popularity += 1*experience.pageview + 10*experience.rate

        i=0
        for i in range(sorted+1):
            if experience.popularity > experiences[i].popularity:
                break
        if i != sorted:
            experiences.insert(i, experience)
            experiences.pop(sorted+1)

        sorted += 1

    return experiences

def experience_similarity(experience1, experience2):
    #TODO
    return 1

def resort_experiences(experiences, experiences_not_interested, experience_interested):
    #TODO
    return experiences

def search_experience(condition, language="zh", type="experience"):
    cursor = connections['default'].cursor()
    result = []
    cmds = ["select product_id from experiences_newproducti18n where language=%s and " + \
           "(title like %s or description like %s);",
           "select experience_id from experiences_experiencei18n where language=%s and " + \
           "(title like %s or description like %s);"]

    for cmd in cmds:
        cursor.execute(cmd, [language, condition, condition])
        ids = cursor._rows
        for id in ids:
            result.append(id[0])

    result = AbstractExperience.objects.filter(id__in=result)
    return result

def get_available_experiences(exp_type, start_datetime, end_datetime, city, guest_number=None, language=None, keywords=None, customer=None, preference=None, currency=None, skip_availability=False, from_id=None):
    #city/keywords is a string like A,B,C,
    available_options = []
    start_datetime = start_datetime.replace(hour=2)
    end_datetime = end_datetime.replace(hour=22)

    if not from_id:
        limit = 9999999999
        from_id_experience = 9999999999
        from_id_newprudoct = 9999999999
    else:
        limit=10
        try:
            from_id_experience = int(from_id.split(",")[0])
            from_id_newprudoct = int(from_id.split(",")[1])
        except Exception as err:
            from_id_experience = 9999999999
            from_id_newprudoct = 9999999999

    if city is not None and exp_type != 'itinerary':
        city = str(city).lower().split(",")

        if len(city) > 1 and (end_datetime-start_datetime).days+1 != len(city):
            raise TypeError("Wrong format: city, incorrect length")

        if not isEnglish(city[0]):
            for i in range(len(city)):
                city[i] = dict(Location_reverse).get(city[i]).lower()

    exp_type = exp_type.lower()
    if exp_type == 'all':
        experiences = list(Experience.objects.filter(id__lt = from_id_experience, status='Listed', city__in=city).exclude(type='ITINERARY').order_by('-id')) + \
                      list(NewProduct.objects.filter(id__lt = from_id_newprudoct, status='Listed', city__in=city).order_by('-id'))
    elif exp_type == 'newproduct':
        experiences = list(NewProduct.objects.filter(id__lt = from_id_newprudoct, status='Listed', city__in=city).order_by('-id'))
    else:
        experiences = list(Experience.objects.filter(id__lt = from_id_experience, status='Listed', city__in=city).order_by('-id'))
        if exp_type == 'itinerary':
            experiences = [e for e in experiences if e.type == 'ITINERARY']
        else:
            experiences = [e for e in experiences if e.type != 'ITINERARY']

    #experiences = sort_experiences(experiences, customer, preference)
    month_in_advance = 1

    #the number of experiences/newproducts selected for each city
    selected_experience = {}
    selected_newproduct = {}
    for i in range(len(city)):
        if city[i] not in selected_experience:
            selected_experience[city[i]]=0
            selected_newproduct[city[i]]=0

    for experience in experiences:
        done_experience = True
        done_newproduct = True
        for k, v in selected_experience.items():
            if v < limit:
                done_experience = False
                break
        for k, v in selected_newproduct.items():
            if v < limit:
                done_newproduct = False
                break

        if done_experience and done_newproduct:
            return available_options

        if done_experience and type(experience) == Experience:
            continue

        if done_newproduct and type(experience) == NewProduct:
            continue

        if selected_experience.get(experience.city.lower(), 0) >= limit and type(experience) == Experience:
            continue

        if selected_newproduct.get(experience.city.lower(), 0) >= limit and type(experience) == NewProduct:
            continue

        setattr(experience, 'popularity', 0)
        #new requirement: if the guest_number is smaller than the min value, increase the price per person instead of excluding the experience
        if guest_number is not None and (experience.guest_number_max < int(guest_number) or int(guest_number) <= 0):
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
            #new requirement: if the tags are not set for an experience, do not exclude it
            if experience_tags is not None and len(experience_tags) > 0:
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
        local_timezone = pytz.timezone(experience.get_timezone())

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

        host = experience.get_host()
        exp_price = float(experience.price)
        if int(guest_number) < experience.guest_number_min:
            exp_price = exp_price * float(experience.guest_number_min / int(guest_number))
        elif experience.dynamic_price != None and len(experience.dynamic_price.split(',')) == experience.guest_number_max - experience.guest_number_min + 2 :
            exp_price = float(experience.dynamic_price.split(",")[int(guest_number)-experience.guest_number_min])
        if currency is not None and currency != experience.currency:
            exp_price = convert_currency(exp_price, experience.currency, currency)
            experience.currency = currency

        photo_url = ''
        photos = experience.photo_set.all()
        if photos is not None and len(photos) > 0:
            photo_url = photos[0].directory+photos[0].name

        exp_information = experience.get_information(settings.LANGUAGES[0][0])
        experience_avail = {'id':experience.id, 'title': exp_information.title, 'rate': rate,
                            'duration':int(experience.duration) if float(experience.duration).is_integer() else experience.duration,
                            'city':experience.city, 'description':exp_information.description,
                            'language':experience.language, 'calendar_updated':calendar_updated,
                            'price':experience_fee_calculator(exp_price, experience.commission),
                            'currency':str(dict(Currency)[experience.currency.upper()]),
                            'dollarsign':DollarSign[experience.currency.upper()],'dates':{},
                            'photo_url':photo_url, 'type':experience.type , 'popularity':experience.popularity,
                            'tags':experience.get_tags(settings.LANGUAGES[0][0])}

        if type(experience) == Experience:
            experience_avail['meetup_spot'] = exp_information.meetup_spot
            experience_avail['host_image'] = host.registereduser.image_url
            experience_avail['host'] = host.first_name + ' ' + host.last_name

        blockout_start = []
        blockout_end = []
        blockout_index=0

        instantbooking_start = []
        instantbooking_end = []
        instantbooking_index=0

        if not skip_availability:
            blockouts = experience.blockouttimeperiod_set.filter(experience_id=experience.id)

            #calculate all the blockout time periods
            for blk in blockouts:
                if blk.start_datetime.astimezone(local_timezone).dst() != timedelta(0):
                    daylightsaving = True
                else:
                    daylightsaving = False

                if blk.repeat:
                    b_l = blk.end_datetime - blk.start_datetime
                    if not blk.repeat_end_date or blk.repeat_end_date > (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=month_in_advance)).date():
                        blk.repeat_end_date = (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=month_in_advance)).date()
                    while blk.start_datetime.date() <= blk.repeat_end_date:
                        blockout_index += 1
                        blockout_start.append(blk.start_datetime)
                        blockout_end.append(blk.start_datetime + b_l)

                        blk.start_datetime = next_time_slot(experience, blk.repeat_cycle, blk.repeat_frequency,
                                                            blk.repeat_extra_information, blk.start_datetime,daylightsaving)

                else:
                    blockout_index += 1
                    blockout_start.append(blk.start_datetime)
                    blockout_end.append(blk.end_datetime)

            blockout_start.sort()
            blockout_end.sort()

            instantbookings = experience.instantbookingtimeperiod_set.filter(experience_id=experience.id)

            #calculate all the instant booking time periods
            for ib in instantbookings :
                if ib.start_datetime.astimezone(local_timezone).dst() != timedelta(0):
                    daylightsaving = True
                else:
                    daylightsaving = False

                if ib.repeat:
                    ib_l = ib.end_datetime - ib.start_datetime
                    if not ib.repeat_end_date or ib.repeat_end_date > (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=month_in_advance)).date():
                        ib.repeat_end_date = (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=month_in_advance)).date()
                    while ib.start_datetime.date() <= ib.repeat_end_date:
                        instantbooking_index += 1
                        instantbooking_start.append(ib.start_datetime)
                        instantbooking_end.append(ib.start_datetime + ib_l)

                        ib.start_datetime = next_time_slot(experience, ib.repeat_cycle, ib.repeat_frequency,
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
            if pytz.utc.localize(datetime.utcnow()).astimezone(local_timezone).dst() != timedelta(0):
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

                if i == 0 or (hasattr(experience, 'type') and (experience.type in TYPE_PUBLIC) and i < experience.guest_number_max):
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
            if not skip_availability:
                sdt += timedelta(hours=1)
            else:
                sdt += timedelta(days=1)
        experience_avail['dates'] = OrderedDict(sorted(experience_avail['dates'].items(), key=lambda t: t[0]))
        available_options.append(experience_avail)
        if type(experience) == Experience:
            selected_experience[experience.city.lower()] += 1
        else:
            selected_newproduct[experience.city.lower()] += 1

    return available_options

class ExperienceListView(ListView):
    template_name = 'experiences/experience_list.html'
    #paginate_by = 9
    #context_object_name = 'experience_list'

    def get_queryset(self):
        if self.request.user.is_authenticated() and self.request.user.is_superuser:
            return Experience.objects.all#()
        else:
            return HttpResponseRedirect(GEO_POSTFIX + "admin/login/?next=" + GEO_POSTFIX + "experiencelist")

def getAvailableOptions(experience, available_options, available_date, from_datetime=None):

    top_instant_bookings = -1
    month_in_advance = 1

    last_sdt = pytz.timezone('UTC').localize(datetime.min)
    local_timezone = pytz.timezone(experience.get_timezone())


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
    #set the start time according to from_datetime, book_in_advance or 23 hours later
    if from_datetime is not None:
        sdt = from_datetime
    elif hasattr(experience, 'book_in_advance') and experience.book_in_advance is not None and experience.book_in_advance>0:
        sdt = datetime.utcnow().replace(tzinfo=pytz.UTC).replace(hour=22, minute=0, second=0, microsecond=0) + relativedelta(days=experience.book_in_advance-1)
    else:
        sdt = datetime.utcnow().replace(tzinfo=pytz.UTC).replace(minute=0, second=0, microsecond=0) + relativedelta(hours=+23)

    blockouts = experience.blockouttimeperiod_set.filter(experience_id=experience.id)
    blockout_start = []
    blockout_end = []
    blockout_index=0

    #calculate all the blockout time periods
    for blk in blockouts :
        if blk.start_datetime.astimezone(local_timezone).dst() != timedelta(0):
            daylightsaving = True
        else:
            daylightsaving = False

        if blk.repeat:
            b_l =  blk.end_datetime - blk.start_datetime
            if not blk.repeat_end_date or blk.repeat_end_date > (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=month_in_advance)).date():
                blk.repeat_end_date = (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=month_in_advance)).date()
            while blk.start_datetime.date() <= blk.repeat_end_date:
                blockout_index += 1
                blockout_start.append(blk.start_datetime)
                blockout_end.append(blk.start_datetime + b_l)

                blk.start_datetime = next_time_slot(experience, blk.repeat_cycle, blk.repeat_frequency,
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
        if ib.start_datetime.astimezone(local_timezone).dst() != timedelta(0):
            daylightsaving = True
        else:
            daylightsaving = False

        if ib.repeat:
            ib_l =  ib.end_datetime - ib.start_datetime
            if not ib.repeat_end_date or ib.repeat_end_date > (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=month_in_advance)).date():
                ib.repeat_end_date = (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=month_in_advance)).date()
            while ib.start_datetime.date() <= ib.repeat_end_date:
                instantbooking_index += 1
                instantbooking_start.append(ib.start_datetime)
                instantbooking_end.append(ib.start_datetime + ib_l)

                ib.start_datetime = next_time_slot(experience, ib.repeat_cycle, ib.repeat_frequency,
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
    if from_datetime is None:
        from_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC)
    while (sdt <= experience.end_datetime and sdt <= from_datetime + relativedelta(months=month_in_advance) ):
        #check if the date is blocked
        blocked = False
        #block 10pm-7am if repeated hourly
        sdt_local = sdt.astimezone(local_timezone)
        if pytz.utc.localize(datetime.utcnow()).astimezone(local_timezone).dst() != timedelta(0):
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

            if i == 0 or (hasattr(experience, 'type') and experience.type in TYPE_PUBLIC and i < experience.guest_number_max):
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
                            #'datetime': sdt_local,
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

def get_related_experiences(experience, request):
    related_experiences = []
    related_newproducts = []
    N=1
    cursor = connections['default'].cursor()
    #other experiences booked by those that booked this experience
    cursor.execute("select distinct experience_id from experiences_experience_guests where experience_id != %s and user_id in" +
                    "(select user_id from experiences_experience_guests where experience_id=%s)",
                            [experience.id, experience.id])
    ids = cursor._rows
    if ids and len(ids)>0:
        for id in ids:
            if len(related_experiences) < N:
                related_experiences.append(id[0])
            if len(related_newproducts) < N:
                related_newproducts.append(id[0])
        related_experiences = list(Experience.objects.filter(id__in=related_experiences).filter(city__iexact=experience.city))
        related_newproducts = list(NewProduct.objects.filter(id__in=related_newproducts).filter(city__iexact=experience.city))

    #other similar experiences based on tags
    if len(related_experiences)<N or len(related_newproducts)<N:
        cursor = connections['default'].cursor()
        cursor.execute("select experience_id from (select distinct experience_id, count(experiencetag_id)" +
                        "from experiences_experience_tags where experience_id!=%s and experiencetag_id in" +
                        "(SELECT experiencetag_id FROM experiences_experience_tags where experience_id=%s)" +
                        "group by experience_id order by count(experiencetag_id) desc) as t1", #LIMIT %s
                            [experience.id, experience.id])
        ids = cursor._rows
        r_ids = []
        for i in range(len(ids)):
            r_ids.append(ids[i][0])

        if len(related_experiences)<N:
            queryset = Experience.objects.filter(id__in=r_ids).filter(city__iexact=experience.city).filter(status__iexact="listed")
            for exp in queryset:
                if not any(x.id == exp.id for x in related_experiences):
                    related_experiences.append(exp)
                if len(related_experiences)>=N:
                    break

        if len(related_newproducts)<N:
            queryset = NewProduct.objects.filter(id__in=r_ids).filter(city__iexact=experience.city).filter(status__iexact="listed")
            for exp in queryset:
                if not any(x.id == exp.id for x in related_newproducts):
                    related_newproducts.append(exp)
                if len(related_newproducts)>=N:
                    break

    #random experiences
    if len(related_experiences)<N:
        queryset = Experience.objects.filter(city__iexact=experience.city).filter(status__iexact="listed").exclude(id=experience.id).order_by('?')[:N]
        for exp in queryset:
            related_experiences.append(exp)
            if len(related_experiences)>=N:
                break
    if len(related_newproducts)<N:
        queryset = NewProduct.objects.filter(city__iexact=experience.city).filter(status__iexact="listed").exclude(id=experience.id).order_by('?')[:N]
        for exp in queryset:
            related_newproducts.append(exp)
            if len(related_newproducts)>=N:
                break

    related_experiences += related_newproducts

    for i in range(0,len(related_experiences)):
        convert_experience_price(request, related_experiences[i])
        exp_information = related_experiences[i].get_information(settings.LANGUAGES[0][0])
        related_experiences[i].dollarsign = DollarSign[related_experiences[i].currency.upper()]
        related_experiences[i].currency = str(dict(Currency)[related_experiences[i].currency.upper()])
        related_experiences[i].title = exp_information.title
        related_experiences[i].description = exp_information.description
        setExperienceDisplayPrice(related_experiences[i])
        if float(related_experiences[i].duration).is_integer():
            related_experiences[i].duration = int(related_experiences[i].duration)
        if related_experiences[i].commission > 0.0:
            related_experiences[i].commission = related_experiences[i].commission/(1-related_experiences[i].commission)+1
        else:
            related_experiences[i].commission = settings.COMMISSION_PERCENT+1

    return related_experiences

def get_experience_popularity(experience):
    cursor = connections['default'].cursor()
    if type(experience) is Experience:
        table_name = "experiences_experience"
        if experience.type == "ITINERARY":
            target_type = "'ITINERARY'"
        else:
            target_type = "'PRIVATE', 'NONPRIVATE'"

        cursor.execute("SELECT experience_id, count(experience_id) FROM app_userpageviewrecord" + \
                            " where time_arrived >= NOW() - INTERVAL 30 DAY and (select type from " + table_name + \
                            " where abstractexperience_ptr_id=experience_id) in (" + \
                            target_type + ") group by experience_id order by count(experience_id) desc;")
    else:
        table_name = "experiences_newproduct"
        cursor.execute("SELECT experience_id, count(experience_id) FROM app_userpageviewrecord" + \
                            " where time_arrived >= NOW() - INTERVAL 30 DAY and experience_id in " + \
                            " (select abstractexperience_ptr_id from " + table_name + ")" + \
                            " group by experience_id order by count(experience_id) desc;")

    for i in range(int(cursor.rowcount)):
        if cursor._rows[i][0] == experience.id:
            break

    return 100 - 100*(i+1)/int(cursor.rowcount) if int(cursor.rowcount)>0 else 0

def set_option_items(partner_product_information, experience):
    options = json.loads(partner_product_information)
    item_options = {}
    for k, v in options.items():
        ois = OptionItem.objects.filter(original_id=k)
        for oi in ois:
            if oi.group.language == settings.LANGUAGES[0][0]:
                if oi.group.name not in item_options:
                    item_options[oi.group.name] = {}
                item_options[oi.group.name][oi.name] = v
                break
    return item_options

def checkout_as_guest(request):
    '''
    return an auto-created new user (just id) if the email is new, otherwise return the user associated with the email
    '''

    data = request.POST
    try:
        first_name = data['first_name']
        last_name = data['last_name']
        email = data['email']
        phone_number = data['phone_number']
        u = User.objects.filter(email=email)
        if len(u) > 0:
            u = u[0]
            if authenticate(username=u.username, password=u.username) is not None:
                u.first_name = first_name
                u.last_name = last_name
                u.registereduser.phone_number = phone_number
                u.save()
        else:
            username = first_name.lower()
            u = User.objects.filter(first_name__iexact = username)
            counter = len(u) if u is not None else 0
            counter += 1
            username = username + str(counter) if counter > 1 else username
            password = username
            u = User(first_name = first_name, last_name = last_name, email = email,username = username,
                        date_joined = datetime.utcnow().replace(tzinfo=pytz.UTC),
                        last_login = datetime.utcnow().replace(tzinfo=pytz.UTC))
            u.save()

            u.set_password(username)
            u.save()

            r = RegisteredUser(user = u, phone_number = phone_number)
            r.save()

            u = authenticate(username=username, password=password)
            login(request, u)
    except Exception as err:
        return {'success':False}

    return {'success':True, 'user_id':u.id}

class ExperienceDetailView(DetailView):
    model = AbstractExperience
    template_name = 'experiences/experience_detail.html'
    #context_object_name = 'experience'

    def post(self, request, *args, **kwargs):
        #if not request.user.is_authenticated():
        #    return HttpResponseForbidden()

        self.object = self.get_object()

        if request.method == 'POST':
            if 'guest' in request.POST:
                result = checkout_as_guest(request)
                return HttpResponse(json.dumps(result),content_type="application/json")
            elif 'login' in request.POST:
                try:
                    data = request.POST #request.query_params['data']

                    if "email" not in data or "password" not in data:
                        result = {"error":"Wrong username/password"} 
                        return HttpResponse(json.dumps(result), content_type="application/json")

                    email = data['email']
                    password = data['password']
                    username = User.objects.get(email=email).username

                    user = authenticate(username=username, password=password)
                    if user is not None: # and user.is_active:
                        login(request, user)
                        result = {'success':True, 'user_id':user.id}
                        return HttpResponse(json.dumps(result), content_type="application/json")
                    else:
                        result = {'success':False, "error":"Wrong username/password"}
                        return HttpResponse(json.dumps(result), content_type="application/json")

                except Exception as err:
                    #TODO
                    return HttpResponse(json.dumps({'success':False}), content_type="application/json")
            elif 'load_more' in request.POST:
                try:
                    data = request.POST
                    experience = AbstractExperience.objects.get(id=data["experience_id"])
                    max_date = data["max_date"]
                    max_date = pytz.timezone(experience.get_timezone()).localize(datetime.strptime(max_date, "%Y-%m-%d"))
                    available_options = []
                    available_date = ()
                    if type(experience) is NewProduct and experience.partner is not None and len(experience.partner) > 0:
                        if experience.partner == PARTNER_IDS["experienceoz"]:
                            for i in range(4): #7 days per time
                                now = max_date + timedelta(days=1+i*7)
                                now_string = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+now.strftime("%z")
                                now_string = now_string[:-2] + ":" + now_string[-2:]
                                original_id = str(experience.id)[:-(len(str(experience.partner))+1)]
                                available_date = get_experienceoz_availability(original_id, now_string, experience, available_options, available_date)
                        elif experience.partner == PARTNER_IDS["rezdy"]:
                            #TODO
                            pass
                    else:
                        available_date = getAvailableOptions(experience, available_options, available_date, from_datetime = (max_date+timedelta(days=1)).astimezone(pytz.timezone('UTC')))
                    available_date = list(map(lambda x: datetime.strptime(x[0], "%d/%m/%Y").strftime("%Y-%m-%d"), list(available_date)))
                    result = {'success':True, 'available_dates':available_date, 'available_options':available_options}
                    return HttpResponse(json.dumps(result), content_type="application/json")
                except Exception as err:
                    #TODO
                    return HttpResponse(json.dumps({'success':False}), content_type="application/json")

            form = BookingConfirmationForm(request.POST)
            form.data = form.data.copy()
            if request.user.is_authenticated():
                user = request.user
            else:
                user = User.objects.get(id=int(form.data['user_id']))
            form.data['user_id'] = user.id
            form.data['first_name'] = user.first_name
            form.data['last_name'] = user.last_name

            experience = AbstractExperience.objects.get(id=form.data['experience_id'])
            convert_experience_price(request, experience)
            experience.dollarsign = DollarSign[experience.currency.upper()]
            #experience.currency = str(dict(Currency)[experience.currency.upper()])#comment out on purpose --> stripe
            experience.title = experience.get_information(settings.LANGUAGES[0][0]).title
            experience_price = experience.price

            if float(experience.duration).is_integer():
                experience.duration = int(experience.duration)

            adult_number = int(form.data['adult_number'])
            child_number = int(form.data['child_number'])
            subtotal_price = get_total_price(experience, adult_number = adult_number, child_number = child_number,
                                             extra_information=form.data['partner_product_information'])

            COMMISSION_PERCENT = round(experience.commission/(1-experience.commission),3)

            item_options = None
            if 'partner_product_information' in form.data and len(form.data['partner_product_information'])>0 \
                and hasattr(experience, "partner") and experience.partner == PARTNER_IDS["experienceoz"]:
                item_options = set_option_items(form.data['partner_product_information'], experience)
                form.data['time'] = "09:00"

            return render(request, 'experiences/experience_booking_confirmation.html',
                          {'form': form, #'eid':self.object.id,
                           'experience': experience,
                           'experience_price': experience_price,
                           'adult_number':form.data['adult_number'],
                           'child_number':form.data['child_number'],
                           'date':form.data['date'],
                           'time':form.data['time'],
                           'subtotal_price':round(subtotal_price*(1.00+COMMISSION_PERCENT),0),
                           'service_fee':round(subtotal_price*(1.00+COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                           'total_price': experience_fee_calculator(subtotal_price, experience.commission),
                           'user_email':user.email,
                           'GEO_POSTFIX':settings.GEO_POSTFIX,
                           'LANGUAGE':settings.LANGUAGE_CODE,
                           'commission':COMMISSION_PERCENT + 1,
                           'item_options':item_options,
                           })

    def get_context_data(self, **kwargs):
        set_initial_currency(self.request)
        context = super(ExperienceDetailView, self).get_context_data(**kwargs)
        experience = context['experience'] if 'experience' in context else context['newproduct']
        if 'experience' not in context:
            context['experience'] = experience

        sdt = experience.start_datetime
        last_sdt = pytz.timezone('UTC').localize(datetime.min)
        local_timezone = pytz.timezone(experience.get_timezone())
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
            if self.request.user.id != experience.get_host().id:
                # other user, experience already expired
                context['expired'] = True
                return context
            else:
                # host, experience already expired
                context['host_only_expired'] = True
                return context

        if type(experience) is NewProduct and experience.partner is not None and len(experience.partner) > 0:
            if experience.partner == PARTNER_IDS["experienceoz"]:
                for i in range(4): #7 days per time
                    now = pytz.timezone(experience.get_timezone()).localize(datetime.now()) + timedelta(days=2+i*7)
                    now_string = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+now.strftime("%z")
                    now_string = now_string[:-2] + ":" + now_string[-2:]
                    original_id = str(experience.id)[:-(len(str(experience.partner))+1)]
                    available_date = get_experienceoz_availability(original_id, now_string, experience, available_options, available_date)
            elif experience.partner == PARTNER_IDS["rezdy"]:
                #TODO
                pass
        else:
            available_date = getAvailableOptions(experience, available_options, available_date)

        if len(available_date) == 0:
            experience.status="Unavailable"
            experience.save()

        context['available_options'] = available_options

        if not experience.status.lower() == "listed":
            owner_id = experience.get_host().id

            if self.request.user.id != owner_id and not self.request.user.is_superuser:
                # other user, experience not published
                context['listed'] = False
                return context
            else:
                # host, experience not published
                context['host_only_unlisted'] = True
                #return context

        context['experience_city'] = dict(Location).get(experience.city)

        uid = self.request.user.id if self.request.user.is_authenticated() else None
        context['form'] = BookingForm(available_date, experience.id, uid)
        context['available_dates'] = list(map(lambda x: datetime.strptime(x[0], "%d/%m/%Y").strftime("%Y-%m-%d"), list(available_date)))
        
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
            context["host_bio"] = get_user_bio(experience.get_host().registereduser, settings.LANGUAGES[0][0])
            host_image = experience.get_host().registereduser.image_url
            if host_image == None or len(host_image) == 0:
                context['host_image'] = "hosts/profile_default/" + random.choice(['1','2','3','4','5','6','7','8','9','a','b','c','d','e','f','g','h','i','j','k']) + ".svg"
            else:
                context['host_image'] = host_image

        context['in_wishlist'] = False
        wishlist = self.request.user.registereduser.wishlist.all() if self.request.user.is_authenticated() else None
        if wishlist and len(wishlist) > 0:
            for i in range(len(wishlist)):
                if wishlist[i].id == experience.id:
                    context['in_wishlist'] = True
                    break

        related_experiences = get_related_experiences(experience, self.request)

        related_experiences_added_to_wishlist = []

        cursor = connections['default'].cursor()
        if self.request.user.is_authenticated():
            for r in related_experiences:
                cursor.execute("select id from app_registereduser_wishlist where experience_id = %s and registereduser_id=%s",
                             [r.id,self.request.user.registereduser.id])
                wl = cursor._rows
                if wl and len(wl)>0:
                    related_experiences_added_to_wishlist.append(True)
                else:
                    related_experiences_added_to_wishlist.append(False)
        else:
            for r in related_experiences:
                related_experiences_added_to_wishlist.append(False)

        context['related_experiences'] = zip(related_experiences, related_experiences_added_to_wishlist)

        optiongroup_set = convert_experience_price(self.request, experience)
        if optiongroup_set:
            context["optiongroup_set"] = optiongroup_set
        experience.dollarsign = DollarSign[experience.currency.upper()]
        experience.currency = str(dict(Currency)[experience.currency.upper()])

        if type(experience) is Experience:
            exp_information = experience.get_information(settings.LANGUAGES[0][0])
            experience.title = exp_information.title
            experience.description = exp_information.description
            experience.activity = exp_information.activity
            experience.interaction = exp_information.interaction
            experience.dress = exp_information.dress
            experience.whatsincluded = experience.get_whatsincluded(settings.LANGUAGES[0][0])
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
                experience.notice = t.notice
                experience.service = t.service
                experience.location = t.location
                experience.background_info = t.background_info
                experience.schedule = t.schedule

        if experience.commission >= 0.0:
            experience.commission = round(experience.commission/(1-experience.commission),3)+1
        else:
            experience.commission = settings.COMMISSION_PERCENT+1

        context['GEO_POSTFIX'] = settings.GEO_POSTFIX
        context['LANGUAGE'] = settings.LANGUAGE_CODE
        context['wishlist_webservice'] = "https://" + settings.ALLOWED_HOSTS[0] + settings.GEO_POSTFIX + "service_wishlist/"

        #check whether the experience is among the top 50%, 80% most viewed in the past 30 days
        p = get_experience_popularity(experience)

        if p >= 80:
            top_20 = True
            top_50 = True
        elif p >= 50:
            top_20 = False
            top_50 = True
        else:
            top_20 = False
            top_50 = False

        context['top_20'] = top_20
        context['top_50'] = top_50

        #get coordinates
        coordinates = []
        if experience.coordinate_set is not None:
            for co in experience.coordinate_set.all():
                if co.order is not None and co.order >= 1:
                    coordinates.insert(co.order-1, [co.name if co.name is not None else '', co.latitude, co.longitude])
                else:
                    coordinates.append([co.name if co.name is not None else '', co.latitude, co.longitude])

        context['coordinates'] = coordinates

        context['host'] = experience.get_host()

        #update page view statistics
        if self.request.user.is_staff:
            #ignore page views by staff
            return context
        elif self.request.user.is_authenticated():
            user = self.request.user
        else:
            #annoymous visiters are treated as user 1
            user = User.objects.get(id=1)

        pageview = update_pageview_statistics(user.id, experience.id)
        context["pageview_detail_id"] = pageview[1][0]
        time_arrived = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        context['time_arrived'] = time_arrived
        context['pageview_webservice'] = "https://" + settings.ALLOWED_HOSTS[0] + settings.GEO_POSTFIX + "service_pageview/"
        return context

def update_pageview_statistics(user_id, experience_id, length = None, detail_id = None):
    '''
    @length, detail_id None: arrive, times_viewed++; not None: leave, update average_length
    '''
    if (length and not detail_id) or (not length and detail_id):
        return

    if length and float(length) < 0:
        length = 0

    try:
        record = UserPageViewStatistics.objects.get(user_id=user_id, experience_id = experience_id)
    except UserPageViewStatistics.DoesNotExist:
        record = UserPageViewStatistics(user_id = user_id, experience_id = experience_id,
                                        times_viewed = 0, average_length = 0.0)

    if length and detail_id:
        #leave an experience page
        try:
            length = float(length)
            if length > 300:
                length = 300 if user_id != 1 else 0
            if length > 0:
                record.average_length = float((record.average_length * (record.times_viewed-1) + length) / record.times_viewed)

            detail = UserPageViewRecord.objects.get(id = detail_id)
            detail.time_left = pytz.timezone("UTC").localize(datetime.utcnow())
        except BaseException:
            #TODO
            pass
    else:
        #arrive at an experience page
        record.times_viewed += 1
        detail = UserPageViewRecord(user_id=user_id, experience_id=experience_id,
                                    time_arrived=pytz.timezone("UTC").localize(datetime.utcnow()))

    record.save()
    detail.save()

    return ((record.id, record.times_viewed), (detail.id, detail.time_arrived, detail.time_left))

EXPERIENCE_IMAGE_SIZE_LIMIT = 2097152

@csrf_exempt
def experience_booking_successful(request, user_id=None, booking_id=None, guest_number=None, booking_datetime=None, price_paid=None, is_instant_booking=False, *args, **kwargs):
    #if not request.user.is_authenticated():
    #    return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/")

    if (request.GET is None or len(request.GET) == 0) and (booking_id is None or user_id is None):
        return HttpResponseRedirect(GEO_POSTFIX)

    if not request.user.is_authenticated():
        user = User.objects.get(id=int(user_id))
        #return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/")
    else:
        user = request.user

    data = request.GET
    if booking_id is not None:
        booking = Booking.objects.get(id=booking_id)
        experience = booking.experience
    elif data is not None:
        booking = Booking.objects.get(id=data['booking_id'])
        experience = booking.experience
        guest_number = int(data['guest_number'])
        booking_datetime = pytz.timezone(experience.get_timezone()).localize(datetime.strptime(data['booking_datetime'], "%Y-%m-%d%H:%M"))
        price_paid = float(data['price_paid'])
        is_instant_booking = True if data['is_instant_booking'] == "True" else False

    #if the product is from experienceOz
    #call makePurchase API, and then Receipt API
    purchase_id = None
    bk_total_price = None
    link = None
    if hasattr(experience, "partner") and experience.partner == "001":
        bk_dt_string = booking.datetime.strftime("%Y-%m-%d%z")
        bk_dt_string = bk_dt_string[:-2]+":"+bk_dt_string[-2:]
        phone_number = "123456789"
        if len(booking.payment.phone_number.split(",")[0]) > 0:
            phone_number = booking.payment.phone_number.split(",")[0]
        elif len(booking.payment.phone_number.split(",")) > 1:
            phone_number = booking.payment.phone_number.split(",")[1]
        purchase = experienceoz_makepurchase(user.first_name, user.last_name, phone_number, "billing@tripalocal.com", "Australia", "3066",
                                    experience, bk_dt_string, booking.partner_product, booking.note)
        if purchase.get("success", False):
            purchase_id = purchase["purchase_id"]
            bk_total_price = purchase["price"]
            booking.whats_included = purchase_id
            booking.save()
        else:
            raise Exception("Errors in calling makePurchase API")

        receipt = experienceoz_receipt(booking)
        if receipt.get("success", False):
            link = unquote(receipt["link"])

    if not settings.DEVELOPMENT:
        try:
            mp = Mixpanel(settings.MIXPANEL_TOKEN)
            mp.track(request.user.email, 'Sent request to '+ experience.get_host().first_name)
        except Exception as err:
            pass

    template = 'experiences/experience_booking_successful_requested.html'
    if is_instant_booking:
        template = 'experiences/experience_booking_successful_confirmed.html'

    experience.title = experience.get_information(settings.LANGUAGES[0][0]).title

    return render(request,template,{'experience': experience,
                                    'price_paid':price_paid,
                                    'guest_number':guest_number,
                                    'booking_datetime':booking_datetime,
                                    'user':request.user,
                                    'experience_url':'http://' + settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                    'link':link,
                                    'GEO_POSTFIX':settings.GEO_POSTFIX,
                                    'LANGUAGE':settings.LANGUAGE_CODE})

def experience_booking_confirmation(request):
    # Get the context from the request.
    context = RequestContext(request)
    set_initial_currency(request)
    display_error = False

    # A HTTP POST?
    if request.method == 'POST':
        form = BookingConfirmationForm(request.POST)
        if not request.user.is_authenticated():
            user = User.objects.get(id=int(form.data['user_id']))
            #return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/")
        else:
            user = request.user

        form.data = form.data.copy()
        form.data['custom_currency'] = request.session['custom_currency']
        experience = AbstractExperience.objects.get(id=form.data['experience_id'])
        convert_experience_price(request, experience)
        experience.dollarsign = DollarSign[experience.currency.upper()]
        #experience.currency = str(dict(Currency)[experience.currency.upper()])#comment out on purpose --> stripe
        exp_information = experience.get_information(settings.LANGUAGES[0][0])
        if type(experience) == Experience:
            experience.title = exp_information.title
            experience.meetup_spot = exp_information.meetup_spot
        else:
            experience.title = exp_information.title

        adult_number = int(form.data['adult_number'])
        child_number = int(form.data['child_number'])
        experience_price = experience.price
        subtotal_price = get_total_price(experience, adult_number = adult_number, child_number = child_number,
                                         extra_information=form.data['partner_product_information'], language=request.LANGUAGE_CODE)

        COMMISSION_PERCENT = round(experience.commission/(1-experience.commission),3)
        total_price = experience_fee_calculator(subtotal_price, experience.commission)
        subtotal_price = round(subtotal_price*(1.00+COMMISSION_PERCENT),0)

        item_options = None
        if 'partner_product_information' in form.data and len(form.data['partner_product_information'])>0 \
            and hasattr(experience, "partner") and experience.partner == PARTNER_IDS["experienceoz"]:
            item_options = set_option_items(form.data['partner_product_information'], experience)

        local_timezone = pytz.timezone(experience.get_timezone())
        if 'Refresh' in request.POST:
            #get coupon information
            wrong_promo_code = False
            code = form.data['promo_code']
            bk_dt = local_timezone.localize(datetime.strptime(form.data['date'].strip()+form.data['time'].strip(),"%Y-%m-%d%H:%M"))
            coupons = Coupon.objects.filter(promo_code__iexact = code,
                                            end_datetime__gt = bk_dt,
                                            start_datetime__lt = bk_dt)
            if not len(coupons):
                coupon = Coupon()
                wrong_promo_code = True
            else:
                valid = check_coupon(coupons[0], experience.id, adult_number+child_number,
                                     extra_information=form.data['partner_product_information'])
                if not valid['valid']:
                    coupon = Coupon()
                    wrong_promo_code = True
                else:
                    coupon = coupons[0]
                    total_price = valid['new_price']

            if not settings.DEVELOPMENT:
                try:
                    mp = Mixpanel(settings.MIXPANEL_TOKEN)
                    mp.track(user.email, 'Clicked on "Refresh"')
                except Exception as err:
                    pass

            return render_to_response('experiences/experience_booking_confirmation.html', {'form': form,
                                                                           'user_email':user.email,
                                                                           'wrong_promo_code':wrong_promo_code,
                                                                           'coupon':coupon,
                                                                           'experience': experience,
                                                                           'adult_number':form.data['adult_number'],
                                                                           'child_number':form.data['child_number'],
                                                                           'date':form.data['date'],
                                                                           'time':form.data['time'],
                                                                           'subtotal_price':subtotal_price,
                                                                           'experience_price':experience_price,
                                                                           'service_fee':round(subtotal_price*(1.00+COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                                                                           'total_price': total_price,
                                                                           'commission':1 + COMMISSION_PERCENT,
                                                                           'GEO_POSTFIX':settings.GEO_POSTFIX,
                                                                           'LANGUAGE':settings.LANGUAGE_CODE,
                                                                           'item_options':item_options,}, context)

        elif 'Stripe' in request.POST or 'stripeToken' in request.POST:
            #submit the form
            display_error = True
            if form.is_valid():
                if request.user.is_authenticated():
                    request.user.registereduser.phone_number = form.cleaned_data['phone_number']
                    request.user.registereduser.save()

                if form.cleaned_data['status'] == 'accepted':
                    return experience_booking_successful(request, user.id,
                                                         form.cleaned_data['booking_id'],
                                                         int(form.data['adult_number'])+int(form.data['child_number']),
                                                         datetime.strptime(form.data['date'] + " " + form.data['time'], "%Y-%m-%d %H:%M"),
                                                         form.cleaned_data['price_paid'], True)
                else:
                    return experience_booking_successful(request, user.id,
                                                         form.cleaned_data['booking_id'],
                                                         int(form.data['adult_number'])+int(form.data['child_number']),
                                                         datetime.strptime(form.data['date'] + " " + form.data['time'], "%Y-%m-%d %H:%M"),
                                                         form.cleaned_data['price_paid'])

            else:
                return render_to_response('experiences/experience_booking_confirmation.html', {'form': form,
                                                                           'user_email':user.email,
                                                                           'display_error':display_error,
                                                                           'experience': experience,
                                                                           'adult_number':form.data['adult_number'],
                                                                           'child_number':form.data['child_number'],
                                                                           'date':form.data['date'],
                                                                           'time':form.data['time'],
                                                                           'subtotal_price':subtotal_price,
                                                                           'experience_price':experience_price,
                                                                           'service_fee':round(subtotal_price*(1.00+COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                                                                           'total_price': total_price,
                                                                           'commission':1 + COMMISSION_PERCENT,
                                                                           'GEO_POSTFIX':settings.GEO_POSTFIX,
                                                                           'LANGUAGE':settings.LANGUAGE_CODE,
                                                                           'item_options':item_options,}, context)
        elif 'UnionPay' in request.POST:
            display_error = True
            order_id = make_order_id('Tripalocal')
            form.data = form.data.copy()
            form.data['booking_extra_information'] = order_id
            if form.is_valid():
                config = load_config(os.path.join(settings.PROJECT_ROOT, 'unionpay/settings.yaml').replace('\\', '/'))
                bk_date = local_timezone.localize(datetime.strptime(form.data['date'].strip(), "%Y-%m-%d"))
                bk_time = local_timezone.localize(datetime.strptime(form.data['time'].split(":")[0].strip(), "%H"))
                total_price = form.cleaned_data['price_paid'] if form.cleaned_data['price_paid'] != -1.0 else total_price

                if total_price > 0.0:
                    #not free
                    response = client.UnionpayClient(config).pay(int(total_price*100),order_id, channel_type='07',#currency_code=CurrencyCode[experience.currency.upper()],
                                                                 front_url='http://' + settings.ALLOWED_HOSTS[0] + '/experience_booking_successful/?user_id=' + str(user.id)
                                                                 + '&booking_id=' + str(form.cleaned_data['booking_id'])
                                                                 + '&guest_number=' + str(adult_number+child_number)
                                                                 + '&booking_datetime=' + form.data['date'].strip()+form.data['time'].strip()
                                                                 + '&price_paid=' + str(total_price)
                                                                 + '&is_instant_booking=' + str(instant_booking(experience,bk_date,bk_time)))
                    return HttpResponse(response)
                else:
                    #free
                    return experience_booking_successful(request, user.id,
                                                         form.cleaned_data['booking_id'],
                                                         adult_number+child_number,
                                                         datetime.strptime(form.data['date'] + " " + form.data['time'], "%Y-%m-%d %H:%M"),
                                                         form.cleaned_data['price_paid'],
                                                         instant_booking(experience,bk_date,bk_time))

            else:
                return render_to_response('experiences/experience_booking_confirmation.html', {'form': form,
                                                                           'user_email':user.email,
                                                                           'display_error':display_error,
                                                                           'experience': experience,
                                                                           'adult_number':form.data['adult_number'],
                                                                           'child_number':form.data['child_number'],
                                                                           'date':form.data['date'],
                                                                           'time':form.data['time'],
                                                                           'subtotal_price':subtotal_price,
                                                                           'experience_price':experience_price,
                                                                           'service_fee':round(subtotal_price*(1.00+COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                                                                           'total_price': total_price,
                                                                           'commission':1 + COMMISSION_PERCENT,
                                                                           'GEO_POSTFIX':settings.GEO_POSTFIX,
                                                                           'LANGUAGE':settings.LANGUAGE_CODE,
                                                                           'item_options':item_options,}, context)

        elif 'WeChat' in request.POST:
            display_error = True
            unified_pay = UnifiedOrderPay(settings.WECHAT_APPID, settings.WECHAT_MCH_ID, settings.WECHAT_API_KEY)
            from app.views import create_wx_trade_no
            out_trade_no = create_wx_trade_no(settings.WECHAT_MCH_ID)
            notify_url = request.build_absolute_uri(reverse('wechat_qr_payment_notify'))
            form.data = form.data.copy()
            form.data['booking_extra_information'] = out_trade_no

            if form.is_valid():
                bk_date = local_timezone.localize(datetime.strptime(form.data['date'].strip(), "%Y-%m-%d"))
                bk_time = local_timezone.localize(datetime.strptime(form.data['time'].split(":")[0].strip(), "%H"))
                total_price = form.cleaned_data['price_paid'] if form.cleaned_data['price_paid'] != -1.0 else total_price

                if total_price > 0.0:
                    #not free
                    price = int(convert_currency(total_price, experience.currency, "CNY") * 100)
                    pay_info = unified_pay.post(experience.get_information(settings.LANGUAGES[0][0]).title, out_trade_no,
                                                str(price), "127.0.0.1", notify_url)
                    if pay_info['return_code'] == 'SUCCESS' and pay_info['result_code'] == 'SUCCESS':
                        code_url = pay_info['code_url']
                        success_url = 'http://' + settings.ALLOWED_HOSTS[0] \
                                      + '/experience_booking_successful/?user_id=' + str(user.id) \
                                      + '&booking_id=' + str(form.cleaned_data['booking_id']) \
                                      + '&guest_number=' + str(adult_number+child_number) \
                                      + '&booking_datetime=' + form.data['date'].strip() + form.data['time'].strip() \
                                      + '&price_paid=' + str(total_price) + '&is_instant_booking=' \
                                      + str(instant_booking(experience, bk_date, bk_time))

                        return redirect(url_with_querystring(reverse('wechat_qr_payment'), code_url=code_url,
                                                             out_trade_no=out_trade_no, success_url=success_url))
                    else:
                        return HttpResponse('<html><body>WeChat Payment Error.</body></html>')
                else:
                    #free
                    return experience_booking_successful(request, user.id,
                                                         form.cleaned_data['booking_id'],
                                                         adult_number+child_number,
                                                         datetime.strptime(form.data['date'] + " " + form.data['time'], "%Y-%m-%d %H:%M"),
                                                         form.cleaned_data['price_paid'],
                                                         instant_booking(experience,bk_date,bk_time))

            else:
                return render_to_response('experiences/experience_booking_confirmation.html', {'form': form,
                                                                           'user_email':user.email,
                                                                           'display_error':display_error,
                                                                           'experience': experience,
                                                                           'adult_number':form.data['adult_number'],
                                                                           'child_number':form.data['child_number'],
                                                                           'date':form.data['date'],
                                                                           'time':form.data['time'],
                                                                           'subtotal_price':subtotal_price,
                                                                           'experience_price':experience_price,
                                                                           'service_fee':round(subtotal_price*(1.00+COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                                                                           'total_price': total_price,
                                                                           'commission':1 + COMMISSION_PERCENT,
                                                                           'GEO_POSTFIX':settings.GEO_POSTFIX,
                                                                           'LANGUAGE':settings.LANGUAGE_CODE,
                                                                           'item_options':item_options,}, context)

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
    dirname = 'experiences/' + str(experience.id) + '/'

    photos = Photo.objects.filter(name=filename)
    if len(photos) != 0:
        ph = photos[0]
        photos[0].image.delete()
    else:
        ph = Photo(name=filename, directory=dirname, experience=experience)

    ph.image = photo
    ph.save()

    #add watermark
    f = storage.open(dirname + filename, 'rb')
    im = PIL.Image.open(f)
    add_watermark(f, im, extension, dirname, filename)

    #create the corresponding thumbnail (force .jpg)
    basewidth = 400
    thumb_file_name = 'thumbnails/experiences/experience' + str(experience.id) + '_' + str(index) + '.jpg'

    if storage.exists(thumb_file_name):
        storage.delete(thumb_file_name)
    try:
        f = storage.open(dirname + filename, 'rb')
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
    set_exp_title_all_langs(experience, title, lan, lan2)

    #save description
    set_exp_desc_all_langs(experience, description, lan ,lan2)

    #save activity
    set_exp_activity_all_langs(experience, activity, lan, lan2)

    #save interaction
    set_exp_interaction_all_langs(experience, interaction, lan, lan2)

    #save dress
    set_exp_dress_all_langs(experience, dress, lan, lan2)

    #save meetup_spot
    set_exp_meetup_spot_all_langs(experience, meetup_spot, lan, lan2)

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
            host = experience.get_host()
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
            exp_information = experience.get_information(settings.LANGUAGES[0][0])
            data = {"id":experience.id,
                "host":experience.get_host().email,
                "host_first_name":experience.get_host().first_name,
                "host_last_name":experience.get_host().last_name,
                "host_bio": get_user_bio(registerUser, settings.LANGUAGES[0][0]),
                "host_image":registerUser.image,
                "host_image_url":registerUser.image_url,
                "language":experience.language,
                "start_datetime":experience.start_datetime,
                "end_datetime":experience.end_datetime,
                #"repeat_cycle":experience.repeat_cycle,
                #"repeat_frequency":experience.repeat_frequency,
                "phone_number":registerUser.phone_number,
                "title":exp_information.title,
                "summary":exp_information.description,
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
                "activity":exp_information.activity,
                "interaction":exp_information.interaction,
                "dress_code":exp_information.dress,
                "suburb":experience.city,
                "meetup_spot":exp_information.meetup_spot,
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
                                        id=int(form.data['id']),
                                        start_datetime = pytz.timezone(experience.get_timezone()).localize(datetime.strptime("2015-01-01 00:00", "%Y-%m-%d %H:%M")).astimezone(pytz.timezone('UTC')),#form.data['start_datetime']
                                        end_datetime = pytz.timezone(experience.get_timezone()).localize(datetime.strptime("2025-01-01 00:00", "%Y-%m-%d %H:%M")).astimezone(pytz.timezone('UTC')),#form.data['end_datetime']
                                        repeat_cycle = "Hourly",
                                        repeat_frequency = 1,
                                        guest_number_min = int(form.data['guest_number_min']),
                                        guest_number_max = int(form.data['guest_number_max']),
                                        price = float(form.data['price']),
                                        currency = form.data['currency'].lower(),
                                        duration = float(form.data['duration']),
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

                        photo = user.userphoto_set.filter(name__startswith=filename)
                        if not len(photo)>0:
                            photo = UserPhoto(name = filename, directory = 'hosts_id/' + str(user.id) + '/',
                                          image = 'hosts_id/' + str(user.id) + '/' + filename, user = user)
                        else:
                            photo = photo[0]
                            photo.image.delete()
                        photo.image = request.FILES['host_id_photo_'+str(index)]
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

            return HttpResponseRedirect(GEO_POSTFIX + 'admin/experiences/experience/'+str(experience.id))

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

        experience = AbstractExperience.objects.get(id=booking.experience_id)
        exp_information = experience.get_information(settings.LANGUAGES[0][0])
        experience.title = exp_information.title
        if type(experience) == Experience:
            experience.meetup_spot = exp_information.meetup_spot
        else:
            experience.meetup_spot = exp_information.location
        if not experience.get_host().id == user.id and not user.is_superuser:
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

            exp_title = experience.get_information(settings.LANGUAGE_CODE).title
            if booking.payment:
                customer_phone_num = booking.payment.phone_number
            else:
                customer_phone_num = booking.user.registereduser.phone_number
            exp_datetime_local = booking.datetime.astimezone(tzlocal())
            exp_datetime_local_str = exp_datetime_local.strftime(_("%H:%M %d %b %Y")).format(*'年月日')

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
                if booking.total_price:
                    refund_amount = booking.total_price
                else:
                    if booking.adult_number:
                        subtotal_price = get_total_price(experience, adult_number=booking.adult_number,
                                                         child_number=booking.children_number, 
                                                         extra_information=booking.partner_product)
                    else:
                        subtotal_price = get_total_price(experience, booking.guest_number, extra_information=booking.partner_product)

                    #refund_amount does not include process fee: the transaction can't be undone
                    COMMISSION_PERCENT = round(experience.commission/(1-experience.commission),3)
                    refund_amount = subtotal_price*(1+COMMISSION_PERCENT)

                    if extra_fee <= -1:
                        refund_amount = subtotal_price*(1+COMMISSION_PERCENT) + extra_fee
                    if extra_fee < 0 and extra_fee > -1:
                        refund_amount = subtotal_price*(1+COMMISSION_PERCENT) * (1+extra_fee)

                if payment.charge_id.startswith('ch_'):
                    #stripe
                    refund_amount = round(refund_amount, 0)
                    success, response = payment.refund(charge_id=payment.charge_id, amount=int(refund_amount*100))
                elif booking.booking_extra_information and booking.booking_extra_information.startswith("Tripalocal"):
                    #union pay
                    refund_amount = round(convert_currency(refund_amount, experience.currency, "CNY"), 0)
                    config = load_config(os.path.join(settings.PROJECT_ROOT, 'unionpay/settings.yaml').replace('\\', '/'))
                    response = client.UnionpayClient(config).refund(int(refund_amount*100),
                                                         payment.booking.booking_extra_information.replace("Tripalocal","UPRefund"),
                                                         payment.charge_id, '000201', '07')

                    success = True if response['respCode'] == '00' else False
                    if success:
                        booking.refund_id=response['queryId']
                        booking.save()
                elif booking.booking_extra_information and booking.booking_extra_information.startswith("wx"):
                    #wechat
                    refund_amount = round(convert_currency(refund_amount, experience.currency, "CNY"), 0)
                    rf = Refund(settings.WECHAT_APPID, settings.WECHAT_MCH_ID, settings.WECHAT_API_KEY)
                    try:
                        response = rf.post(booking.booking_extra_information, booking.booking_extra_information,
                                           str(int(refund_amount*100)), str(int(refund_amount*100)), "CNY", settings.WECHAT_MCH_ID,
                                           settings.WECHAT_PAYMENT_CERT)
                        success = True if response['return_code'] == 'SUCCESS' and response['result_code'] == 'SUCCESS' else False
                    except Exception as e:
                        success = False
                        import logging
                        logger = logging.getLogger("Tripalocal_V1")
                        logger.error(e)
                    if success:
                        booking.refund_id=response['refund_id']
                        booking.save()
                else:
                    success = False
            else:
                success = True

            if success:
                booking.status = "rejected"
                booking.save()

                #send SMS
                exp_title = experience.get_information(settings.LANGUAGE_CODE).title
                if booking.payment:
                    customer_phone_num = booking.payment.phone_number
                else:
                    customer_phone_num = booking.user.registereduser.phone_number
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

#TODO move to models
# Takes the experience primary key and returns the number of reviews it has received.
def getNReviews(experienceKey):
    #nReviews = 0
    reviewList = Review.objects.filter(experience_id=experienceKey)
    #for review in reviewList:
    #    if (review.experience.id == experienceKey):
    #        nReviews += 1

    return len(reviewList)

def tagsOnly(tag, exp):
    experience_tags = exp.get_tags(settings.LANGUAGES[0][0])
    return tag in experience_tags

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

            experience.save()
            return HttpResponse(json.dumps({'success': True}), content_type='application/json')

def manage_listing_overview(request, experience, context):
    if request.method == 'GET':
        data = {}
        exp_information = experience.get_information(LANG_EN)
        data['title'] = exp_information.title
        data['summary'] = exp_information.description
        data['language'] = experience.language

        exp_information = experience.get_information(LANG_CN)
        data['title_other'] = exp_information.title
        data['summary_other'] = exp_information.description

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
        exp_information = experience.get_information(LANG_EN)
        data['activity'] = exp_information.activity
        data['interaction'] = exp_information.interaction
        data['dress_code'] = exp_information.dress

        exp_information = experience.get_information(LANG_CN)
        data['activity_other'] = exp_information.activity
        data['interaction_other'] = exp_information.interaction
        data['dress_code_other'] = exp_information.dress

        includes = experience.get_whatsincluded(LANG_EN)
        set_response_exp_includes_detail(data, includes)
        set_response_exp_includes(data, includes)
        includes_other_lang = experience.get_whatsincluded(LANG_CN)
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
                    try:
                        saveExperienceImage(experience, file, extension, index)
                    except Exception as err:
                        return HttpResponse(json.dumps({'success': False}), content_type='application/json')

            experience.save()
        return HttpResponse(json.dumps({'success': True}), content_type='application/json')

def manage_listing_location(request, experience, context):
    if request.method == 'GET':
        data = {}
        exp_information = experience.get_information(LANG_EN)
        data['meetup_spot'] =  exp_information.meetup_spot
        data['dropoff_spot'] =  exp_information.dropoff_spot

        exp_information = experience.get_information(LANG_CN)
        data['meetup_spot_other'] =  exp_information.meetup_spot
        data['dropoff_spot_other'] =  exp_information.dropoff_spot
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
    exp_information = experience.get_information(LANG_EN)
    if exp_information.title and exp_information.description:
        result+='1'
    else:
        result+='0'
    #check detail.
    if exp_information.activity and experience.get_whatsincluded(LANG_EN):
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
    if exp_information.meetup_spot and exp_information.dropoff_spot:
        result+='1'
    else:
        result+='0'
    return result

def manage_listing(request, exp_id, step, ):
    experience = get_object_or_404(Experience, pk=exp_id)
    if not request.user.is_superuser:
        if request.user.id != experience.get_host().id:
            raise Http404("Sorry, but you can only edit your own experience.")

    experience_title_cn = experience.get_information("zh").title
    experience_title_en = experience.get_information("en").title

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
    exp_information = exp.get_information(lang)
    overview_fields = [exp_information.title, exp_information.description, exp.language]
    detail_fields = [exp_information.activity, exp_information.interaction,
                     exp_information.dress]
    location_fields = [exp.city, exp_information.meetup_spot]

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
               is_kids_friendly=False, is_host_with_cars=False, is_private_tours=False,  type='product'):
    set_initial_currency(request)
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

    #for issue 208
    city_search = [city]
    for state, cities in Location_relation.items():
        if city in cities:
            city_search = [state, city]
            break

    if request.is_ajax():
        if type == 'product':
            experienceList = NewProduct.objects.filter(city__in=city_search, status__iexact="listed")
        else:
            experienceList = Experience.objects.filter(city__in=city_search, status__iexact="listed").exclude(
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

        experienceList = sort_experiences(experienceList)
        i = 0
        counter = 0
        while i < len(experienceList):
            experience = experienceList[i]
            convert_experience_price(request, experience)
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

            #hide the duration if the product is from partners, as it might be set incorrectly
            if hasattr(experience, "partner") and experience.partner is not None and len(experience.partner)>0:
                experience.show_duration = False
            else:
                experience.show_duration = True

            if not experience.currency:
                experience.currency = 'aud'
            experience.dollarsign = DollarSign[experience.currency.upper()]
            experience.currency = str(dict(Currency)[experience.currency.upper()])

            cityExperienceList.insert(counter, experience)
            cityExperienceReviewList.insert(counter, getNReviews(experience.id))
            # Fetch BGImageURL
            BGImageURL = experience.get_background_image()
            if (BGImageURL):
                BGImageURLList.insert(counter, BGImageURL)
            else:
                BGImageURLList.insert(counter, "default_experience_background.jpg")

            if type != 'product':
                # Fetch profileImageURL
                profileImageURL = RegisteredUser.objects.get(user_id=experience.get_host().id).image_url
                if (profileImageURL):
                    profileImageURLList.insert(counter, profileImageURL)
                else:
                    profileImageURLList.insert(counter, "hosts/profile_default/" + random.choice(['1','2','3','4','5','6','7','8','9','a','b','c','d','e','f','g','h','i','j','k']) + ".svg")

            # Format title & Description
            exp_information = experience.get_information(settings.LANGUAGES[0][0])
            experience.description = exp_information.description
            t = exp_information.title

            if float(experience.duration).is_integer():
                experience.duration = int(experience.duration)

            if (t != None and len(t) > 40):
                formattedTitleList.insert(counter, t[:37] + "...")
            else:
                formattedTitleList.insert(counter, t)

            i += 1
            counter += 1

        if not settings.DEVELOPMENT:
            try:
                mp = Mixpanel(settings.MIXPANEL_TOKEN)

                if request.user.is_authenticated():
                    mp.track(request.user.email,"Viewed " + city.title() + " search page")
                #else:
                #    mp.track("","Viewed " + city.title() + " search page")
            except Exception as err:
                pass

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
            bookings[0].datetime = bookings[0].datetime.astimezone(pytz.timezone(experience.get_timezone()))
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

def get_itinerary(type, start_datetime, end_datetime, guest_number, city, language, keywords=None, mobile=False, sort=1, age_limit=1, customer=None, currency=None, skip_availability=False, from_id=None):
    '''
    @sort, 1:most popular, 2:outdoor, 3:urban
    '''

    if sort == 2:
        config = load_config(os.path.join(settings.PROJECT_ROOT, 'experiences/itinerary_configuration/outdoor.yaml').replace('\\', '/'))
    elif sort == 3:
        config = load_config(os.path.join(settings.PROJECT_ROOT, 'experiences/itinerary_configuration/urban.yaml').replace('\\', '/'))
    else:
        config = load_config(os.path.join(settings.PROJECT_ROOT, 'experiences/itinerary_configuration/popularity.yaml').replace('\\', '/'))

    if age_limit == 2:
        config.update(load_config(os.path.join(settings.PROJECT_ROOT, 'experiences/itinerary_configuration/not_for_elderly.yaml').replace('\\', '/')))
    elif age_limit == 3:
        config.update(load_config(os.path.join(settings.PROJECT_ROOT, 'experiences/itinerary_configuration/not_for_children.yaml').replace('\\', '/')))
    elif age_limit == 4:
        config.update(load_config(os.path.join(settings.PROJECT_ROOT, 'experiences/itinerary_configuration/not_for_elderly.yaml').replace('\\', '/')))
        config.update(load_config(os.path.join(settings.PROJECT_ROOT, 'experiences/itinerary_configuration/not_for_children.yaml').replace('\\', '/')))

    available_options = get_available_experiences(type, start_datetime, end_datetime, city, guest_number, language, keywords, customer=customer, preference=config, currency=currency, skip_availability=skip_availability, from_id=from_id)
    itinerary = []
    dt = start_datetime

    city = city.lower().split(",")
    if not isEnglish(city[0]):
        for i in range(len(city)):
            city[i] = dict(Location_reverse).get(city[i]).lower()

    day_counter = 0

    #available_options: per experience --> itinerary: per day
    while dt <= end_datetime:
        dt_string = dt.strftime("%Y/%m/%d")
        day_dict = {'date':dt_string, 'city':city[day_counter], 'experiences':[]}

        for experience in available_options:
            if experience['type'] != 'ITINERARY' and experience['city'].lower() != city[day_counter]:
                continue

            if dt_string in experience['dates']: #and len(experience['dates'][dt_string]) > 0:
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

def custom_itinerary_request(request):
    context = RequestContext(request)
    context['LANGUAGE'] = settings.LANGUAGE_CODE
    form = CustomItineraryRequestForm()

    if request.method == 'POST':
        data = request.POST
        email = data.get('email')
        message = "<h1>Custom itinerary request</h1>" + \
                "<p>" + data.get('name') + " has requested an itinerary for " + \
                data.get('guests_adults') + " adults, " + data.get('guests_children') + " children and " + data.get('guests_infants') + " infants;" + \
                " from " +  data.get('start_date') + " to " + data.get('end_date') + " with the \
                following destinations: " + data.get('destinations') + ".</p>" + \
                "<p>Interests include: " + data.get('interests') + ".</p>" + \
                "<h3>What's included</h3>" + \
                "<p>Budget: $" + data.get('budget') + "</p>" + \
                "<p>Accommodation: " + data.get('accommodation') + "</p>" + \
                "<p>Car driver: " + data.get('car_driver') + "</p>" + \
                "<p>National flight: " + data.get('national_flight') + "</p>" + \
                "<p>Service language: " + data.get('service_language') + "</p>" + \
                "<h3>Requirements</h3><p>" + data.get('requirements') + "</p>" + \
                "<h3>Contact details</h3>" + \
                "<p>Wechat: " + data.get('wechat') + "</p>" + \
                "<p>Email: " + data.get('email') + "</p>" + \
                "<p>Mobile: " + data.get('mobile') + "</p>"
        mail.send(
            sender = 'admin@tripalocal.com',
            recipients = ['enquiries@tripalocal.com'],
            subject="Itinerary request from " + email,
            html_message=message,
            priority='now',
        )
    return render_to_response('experiences/custom_itinerary_request.html', {'form':form}, context)

def custom_itinerary(request, id=None, operation=None):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/?next=" + GEO_POSTFIX + "itinerary")

    context = RequestContext(request)
    context['location'] = Location
    context['location_keys'] = list(dict(Location).keys())
    context['LANGUAGE'] = settings.LANGUAGE_CODE
    context['guest_num_range'] = range(0,20)
    form = CustomItineraryForm()
    #set_initial_currency(request)
    #force using AUD
    request.session['custom_currency'] = "AUD"
    request.session['dollar_sign'] = "$"

    if operation == 'new':
        ci = CustomItinerary()
        while True:
            current = datetime.now()
            if current.hour>20:
                current = current.replace(hour=20)
            new_id = current.strftime("%H%M%S") + email_account_generator(size=4,chars=string.digits)
            if len(CustomItinerary.objects.filter(id=new_id)) == 0:
                break
        ci.id = new_id
        ci.user = request.user
        ci.title = ""
        ci.submitted_datetime = pytz.timezone("UTC").localize(datetime.utcnow())
        ci.start_datetime = pytz.timezone("UTC").localize(datetime.utcnow())
        ci.end_datetime = pytz.timezone("UTC").localize(datetime.utcnow())
        ci.cities = "Melbourne"
        ci.save()

        #add a booking for the new itinerary
        booking = Booking(user = request.user, experience=Experience.objects.get(id=1), guest_number = 1, adult_number = 1, children_number = 0,
                        datetime = datetime.utcnow().replace(tzinfo=pytz.UTC),
                        submitted_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC), status="draft", custom_itinerary=ci)
        booking.save()
        return HttpResponseRedirect(GEO_POSTFIX+"itinerary/edit/"+str(ci.id)+"/")

    if request.method == 'POST':
        if 'Add' in request.POST:
            #add a new item
            item = request.POST
            np = NewProduct(price=item.get('price', 0), fixed_price=item.get('fixed_price', 0),
                            price_min=item.get('price-min'), price_max=item.get('price-max'), fixed_price_min=item.get('fixed_price-min'), fixed_price_max=item.get('fixed_price-max'),
                            commission=0.0, currency=request.session["custom_currency"].lower(), type=item['type'].title(),
                            city=item.get('location', ""), duration=1, guest_number_min=1, guest_number_max=10, status="Unlisted",
                            start_datetime = pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone(settings.TIME_ZONE)),
                            end_datetime = pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone(settings.TIME_ZONE)) + timedelta(weeks=520))
            np.save()
            np.suppliers.add(Provider.objects.get(id=1))
            npi18n = NewProductI18n(product=np, title=item.get('title',""), notice=item.get('notes', ""),
                                    description=item.get('details', ""), location=item.get('location', ""))
            npi18n.save()
            if len(request.FILES) > 0:
                photo = request.FILES['file']
                content_type = photo.content_type.split('/')[0]
                if content_type == "image":
                    if photo._size > EXPERIENCE_IMAGE_SIZE_LIMIT:
                        raise forms.ValidationError(_('Image size exceeds the limit'))
                else:
                    raise forms.ValidationError(_('File type is not supported'))

                name, extension = os.path.splitext(photo.name)
                extension = extension.lower()
                if extension in ('.bmp', '.png', '.jpeg', '.jpg') :
                    saveExperienceImage(np, photo, extension, 1)

            #issue 423: when an air ticket item or transfer item is created in a city, please duplicate it in all cities
            if np.type in ("Flight", "Transfer"):
                np_list = []
                np_list.append(np)
                for city in Location:
                    if city[0] != np.city:
                        np_copy = deepcopy(np)
                        np_copy.id += 10
                        while len(NewProduct.objects.filter(id = np_copy.id)) > 0:
                            np_copy.id += 10
                        np_copy.city = city[0]
                        np_copy.save()
                        np_copy.suppliers.add(Provider.objects.get(id=1))
                        np_list.append(np_copy)
                        npi18n_copy = deepcopy(npi18n)
                        npi18n_copy.id += 10
                        while len(NewProductI18n.objects.filter(id = npi18n_copy.id)) > 0:
                            npi18n_copy.id += 10
                        npi18n_copy.product = np_copy
                        npi18n_copy.location = city[0]
                        npi18n_copy.save()
                        if len(request.FILES) > 0:
                            saveExperienceImage(np_copy, photo, extension, 1)

                for i in range(len(np_list)):
                    for j in range(len(np_list)):
                        if i!= j: # and np_list[j] not in np_list[i].related_products.all():
                            np_list[i].related_products.add(np_list[j])

            return HttpResponse(json.dumps({'new_product_id':np.id}),content_type="application/json")

        if 'Edit' in request.POST:
            #edit an item
            item = request.POST
            np = NewProduct.objects.get(id=item.get('id'))
            np.price_min = item.get('price-min')
            np.price_max = item.get('price-max')
            np.fixed_price_min = item.get('fixed_price-min')
            np.fixed_price_max = item.get('fixed_price-max')
            np.price = item.get('price', 0)
            np.fixed_price = item.get('fixed_price', 0)
            np.city = item.get('location', "")
            #np.currency=request.session["custom_currency"].lower()
            np.save()

            npi18n = np.newproducti18n_set.all()[0]
            npi18n.title=item.get('title',"")
            npi18n.description=item.get('details', "")
            npi18n.location=item.get('location', "")
            npi18n.notice=item.get('notes', "")
            npi18n.save()

            if len(request.FILES) > 0:
                for p in np.photo_set.all():
                    p.delete()
                photo = request.FILES['file']
                content_type = photo.content_type.split('/')[0]
                if content_type == "image":
                    if photo._size > EXPERIENCE_IMAGE_SIZE_LIMIT:
                        raise forms.ValidationError(_('Image size exceeds the limit'))
                else:
                    raise forms.ValidationError(_('File type is not supported'))

                name, extension = os.path.splitext(photo.name)
                extension = extension.lower()
                if extension in ('.bmp', '.png', '.jpeg', '.jpg') :
                    saveExperienceImage(np, photo, extension, 1)

            #issue 423:  if one instance of these product is modified, please update all products in all cities
            if np.type in ("Flight", "Transfer"):
                for rp in np.related_products.all():
                    rp.price = np.price
                    rp.fixed_price = np.fixed_price
                    rp.save()

                    npi18n_r = rp.newproducti18n_set.all()[0]
                    npi18n_r.title = npi18n.title
                    npi18n_r.description = npi18n.description
                    npi18n_r.notice = npi18n.notice
                    npi18n_r.save()
                    if len(request.FILES) > 0:
                        for ph in rp.photo_set.all():
                            ph.delete()
                        saveExperienceImage(rp, photo, extension, 1)

            return HttpResponse(json.dumps({'new_product_id':np.id}),content_type="application/json")

        if 'Delete' in request.POST:
            #delete an item
            item = request.POST
            np = NewProduct.objects.filter(id=item.get('id'))
            if len(np) > 0:
                np[0].delete()
            return HttpResponse(json.dumps({'success':True}),content_type="application/json")

        form = CustomItineraryForm(request.POST)

        if 'Search' in request.POST and 'itinerary_string' not in request.POST:
            if form.is_valid():
                start_datetime = form.cleaned_data['start_datetime']
                end_datetime = form.cleaned_data['end_datetime']
                end_datetime = end_datetime.replace(hour=22)
                adult_number = int(form.cleaned_data['adult_number'])
                children_number = int(form.cleaned_data['children_number'])
                city = form.cleaned_data['city']
                language = form.cleaned_data['language']
                tags = form.cleaned_data['tags']
                sort = int(form.cleaned_data['sort'])
                age_limit = int(form.cleaned_data['age_limit'])
                from_id = form.cleaned_data['from_id']

                if isinstance(tags, list):
                    tags = ','.join(tags)
                elif not isinstance(tags,str):
                    raise TypeError("Wrong format: keywords. String or list expected.")

                customer = request.user if request.user.is_authenticated() else None
                currency = request.session['custom_currency'].lower() if hasattr(request, 'session') and 'custom_currency' in request.session else None
                itinerary = get_itinerary("ALL", start_datetime, end_datetime, adult_number + children_number, city, language, tags,
                                          False, sort, age_limit, customer, currency, skip_availability=True, from_id=from_id)
                if not ('ProductOnly' in request.POST and request.POST['ProductOnly']=='true'):
                    #get flight, transfer, ...
                    city_list = str(city).split(",")
                    context['flight'] = []
                    context['transfer'] = []
                    context['accommodation'] = []
                    context['restaurant'] = []
                    context['suggestion'] = []
                    context['pricing'] = []
                
                    types = ["Flight", "Transfer", "Accommodation", "Restaurant", "Suggestion", "Pricing"]
                    pds = list(NewProduct.objects.filter(type__in=types, city__in=city_list).order_by('-id'))
                    for pd in pds:
                        information = pd.get_information(settings.LANGUAGES[0][0])
                        pd.title = information.title
                        pd.details = information.description
                        pd.notes = information.notice
                        pd.location = pd.city
                        if 'custom_currency' in request.session and request.session["custom_currency"].lower() != pd.currency.lower():
                            pd.price = convert_currency(pd.price, pd.currency, request.session["custom_currency"])
                            pd.fixed_price = convert_currency(pd.fixed_price, pd.currency, request.session["custom_currency"])
                            pd.price_min = convert_currency(pd.price_min, pd.currency, request.session["custom_currency"])
                            pd.price_max = convert_currency(pd.price_max, pd.currency, request.session["custom_currency"])
                            pd.fixed_price_min = convert_currency(pd.fixed_price_min, pd.currency, request.session["custom_currency"])
                            pd.fixed_price_max = convert_currency(pd.fixed_price_max, pd.currency, request.session["custom_currency"])
                        if pd.city in city_list:
                            if pd.type == 'Flight':
                                context['flight'].append(pd)
                            elif pd.type == 'Transfer':
                                context['transfer'].append(pd)
                            elif pd.type == 'Accommodation':
                                context['accommodation'].append(pd)
                            elif pd.type == 'Restaurant':
                                context['restaurant'].append(pd)
                            elif pd.type == 'Suggestion':
                                context['suggestion'].append(pd)
                            elif pd.type == 'Pricing':
                                context['pricing'].append(pd)
                context["adult_number"] = adult_number
                context["children_number"] = children_number
                return render_to_response('experiences/custom_itinerary_left_section.html', {'form':form,'itinerary':itinerary}, context)
            else:
                return render_to_response('experiences/custom_itinerary_left_section.html', {'form':form}, context)
        else:
            #submit bookings
            if form.is_valid():
                itinerary = json.loads(form.cleaned_data['itinerary_string'])

                #save custom itinerary
                if id is not None:
                    ci = CustomItinerary.objects.get(id=id)
                    if ci.status.lower() == "paid":
                        #cannot edit a paid itinerary
                        return HttpResponseRedirect(GEO_POSTFIX+"itinerary/"+str(ci.id)+"/")
                    for bking in ci.booking_set.all():
                        bking.delete()
                else:
                    ci = CustomItinerary()
                    while True:
                        current = datetime.now()
                        if current.hour>20:
                            current = current.replace(hour=20)
                        new_id = current.strftime("%H%M%S") + email_account_generator(size=4,chars=string.digits)
                        if len(CustomItinerary.objects.filter(id=new_id)) == 0:
                            break
                    ci.id = new_id
                ci.user = request.user
                ci.title = form.cleaned_data['title']
                ci.start_datetime = form.cleaned_data['start_datetime']
                ci.end_datetime = form.cleaned_data['end_datetime']
                ci.submitted_datetime = pytz.timezone("UTC").localize(datetime.utcnow())
                ci.cities = form.cleaned_data['cities_string']
                if "ready" in request.POST:
                    ci.status = "ready"
                ci.save()

                for item in itinerary:
                    experience = AbstractExperience.objects.get(id=str(item['id']))
                    adult_number = int(item['adult_number'])
                    children_number = int(item['children_number'])
                    total_price = item['total_price']
                    whats_included = item['whats_included']

                    #save the custom itinerary as draft
                    local_timezone = pytz.timezone(experience.get_timezone())
                    bk_date = local_timezone.localize(datetime.strptime(str(item['date']), "%Y-%m-%d"))
                    bk_time = local_timezone.localize(datetime.strptime(str(item['time']).split(":")[0].strip(), "%H"))

                    booking = Booking(user = request.user, experience= experience, guest_number = adult_number + children_number, adult_number = adult_number, whats_included=whats_included, total_price = total_price, children_number = children_number,
                                    datetime = local_timezone.localize(datetime(bk_date.year, bk_date.month, bk_date.day, bk_time.hour, bk_time.minute)).astimezone(pytz.timezone("UTC")),
                                    submitted_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC), status="draft", custom_itinerary=ci)
                    booking.save()

                if "draft" in request.POST:
                    return HttpResponseRedirect(GEO_POSTFIX+"itinerary/preview/"+str(ci.id)+"/")
                else:
                    return HttpResponseRedirect(GEO_POSTFIX+"itinerary/"+str(ci.id)+"/")

                #return render(request, 'experiences/itinerary_booking_confirmation.html',
                #          {'form': booking_form,'itinerary':itinerary})

    else:
        all = CustomItinerary.objects.filter(Q(cities__isnull=True) | Q(cities__exact=''))
        for a in all:
            a.cities = ''
            last_d = pytz.timezone("UTC").localize(datetime.utcnow()).replace(hour=14, minute=0, second=0, microsecond=0)
            for b in a.booking_set.order_by('datetime').all():
                if b.datetime.replace(hour=14, minute=0, second=0, microsecond=0) != last_d:
                    a.cities += b.experience.city + ","
                    last_d = b.datetime.replace(hour=14, minute=0, second=0, microsecond=0)
            if len(list(filter(None, a.cities.split(',')))) != (a.end_datetime - a.start_datetime).days + 1:
                a.status= "deleted"
            a.save()
        context["adult_number"] = 1
        context["children_number"] = 0
        if id is not None:
            existing_ci = CustomItinerary.objects.get(id=id)
            #itinerary will be in the format of[{'city':'', 'dates':{'date1':[], 'date2':[], ...}}, ...]
            itinerary = []
            last_city = ""
            all_bookings = list(existing_ci.booking_set.order_by('datetime').all())
            start_date = all_bookings[0].datetime.astimezone(pytz.timezone(all_bookings[0].experience.get_timezone()))
            form.initial["title"] = existing_ci.title
            form.initial["start_datetime"] = pytz.timezone("UTC").localize(datetime.utcnow()) + timedelta(weeks=520)
            cities_list = list(filter(None, existing_ci.cities.split(',')))

            # Construct skeleton of itinerary
            for day, city in enumerate(cities_list):
                if city != last_city:
                    itinerary.append(OrderedDict())
                    itinerary[-1]['city'] = city
                    itinerary[-1]['dates'] = OrderedDict()
                if (start_date + timedelta(days=day)).strftime("%Y-%m-%d") not in itinerary[-1]['dates']:
                    itinerary[-1]['dates'][(start_date + timedelta(days=day)).strftime("%Y-%m-%d")] = []
                last_city = city

            # remove consecutive duplicate cities from cities_list
            last_city=""
            tmp = []
            for city in cities_list:
                if last_city != city:
                    tmp.append(city)
                last_city = city
            cities_list = tmp

            city_index = 0
            for bking in all_bookings:
                if bking.adult_number is not None and bking.adult_number > 0:
                    form.initial["adult_number"] = bking.adult_number
                else:
                    form.initial["adult_number"] = bking.guest_number
                context["adult_number"] = form.initial["adult_number"]
                if bking.children_number is not None and bking.children_number > 0:
                    form.initial["children_number"] = bking.children_number
                else:
                    form.initial["children_number"] = 0
                context["children_number"] = form.initial["children_number"]

                if bking.datetime.astimezone(pytz.timezone(bking.experience.get_timezone())) < form.initial["start_datetime"]:
                    form.initial["start_datetime"] = bking.datetime.astimezone(pytz.timezone(bking.experience.get_timezone()))

                exp_information = bking.experience.get_information(settings.LANGUAGES[0][0])
                bking.experience.title = exp_information.title
                bking.experience.description = exp_information.description

                exp_price = float(bking.experience.price)
                if bking.experience.dynamic_price != None and \
                   len(bking.experience.dynamic_price.split(',')) == bking.experience.guest_number_max - bking.experience.guest_number_min + 2 :
                    exp_price = float(bking.experience.dynamic_price.split(",")[bking.guest_number-bking.experience.guest_number_min])

                bking.experience.fixed_price = experience_fee_calculator(bking.experience.fixed_price, bking.experience.commission)
                bking.experience.price = experience_fee_calculator(exp_price, bking.experience.commission)
                bking.experience.dollarsign = DollarSign[bking.experience.currency.upper()]
                bking.experience.currency = str(dict(Currency)[bking.experience.currency.upper()])
                if float(bking.experience.duration).is_integer():
                    bking.experience.duration = int(bking.experience.duration)

                key = bking.datetime.astimezone(pytz.timezone(bking.experience.get_timezone()))
                while cities_list[city_index] != bking.experience.city:
                    city_index += 1
                itinerary[city_index]['dates'][key.strftime("%Y-%m-%d")].append(bking.experience)

            context['existing_itinerary'] = itinerary

    return render_to_response('experiences/custom_itinerary.html', {'form':form}, context)

def itinerary_detail(request,id=None,preview=None):
    if id is None:
        return HttpResponseRedirect(GEO_POSTFIX)

    context = RequestContext(request)
    set_initial_currency(request)
    if request.method == 'POST':
        form = ItineraryBookingForm(request.POST)
        form.data = form.data.copy()
        form.data["user_id"] = request.user.id
        form.data["itinerary_id"] = id
        form.data["first_name"] = request.user.first_name
        form.data["last_name"] = request.user.last_name
        form.data["custom_currency"] = request.session['custom_currency']

        itinerary = CustomItinerary.objects.get(id=id)
        currency = request.session['custom_currency']
        subtotal_price = itinerary.get_price(currency)
        service_fee = 0
        total_price = subtotal_price + service_fee
        number = itinerary.get_guest_number()
        price_pp = total_price/number[0]
        cover_photo = ""
        for item in itinerary.booking_set.order_by('datetime').all():
            if item.experience.photo_set.all():
                cover_photo = item.experience.photo_set.all()[0]
                break

        return render_to_response('experiences/itinerary_booking_confirmation.html',
                                  {'form':form, "itinerary":itinerary,
                                   "adult_number":number[1],
                                   "children_number":number[2],
                                   "length":itinerary.get_length(),
                                   "price_pp":price_pp, "subtotal_price":subtotal_price,
                                   "service_fee":service_fee, "total_price":total_price,
                                   "currency": currency, "dollarsign": DollarSign[currency.upper()],
                                   "cover_photo": cover_photo,
                                   "LANGUAGE":settings.LANGUAGE_CODE,"GEO_POSTFIX":GEO_POSTFIX},
                                   context)
    else:
        ci = CustomItinerary.objects.get(id=id)
        currency = request.session['custom_currency']
        price = ci.get_price(currency)
        if pytz.timezone("UTC").localize(datetime.utcnow()) > timedelta(days=7) + ci.submitted_datetime:
            full_price = True
        else:
            full_price = False
        discount_deadline = ci.submitted_datetime + timedelta(days=7)

        all_bookings = list(ci.booking_set.order_by('datetime').all())
        ci_timezone = all_bookings[0].experience.get_timezone()

        if ci.start_datetime:
            start_datetime = all_bookings[0].datetime.astimezone(pytz.timezone(ci_timezone))
        else:
            start_datetime = pytz.timezone("UTC").localize(datetime.utcnow())
        if ci.cities:
            end_datetime = start_datetime + timedelta(days=(len(list(filter(None, ci.cities.split(','))))-1))
        else:
            end_datetime = pytz.timezone("UTC").localize(datetime.utcnow())

        itinerary = {"title":ci.title, "days":{}, "status":ci.status}
        for item in all_bookings:
            exp_information = item.experience.get_information(settings.LANGUAGES[0][0])
            item.experience.title = exp_information.title
            item.experience.description = exp_information.description
            item.experience.whatsincluded = item.whats_included
            item.experience.city = _(item.experience.city)
            if settings.LANGUAGE_CODE == "zh-CN":
                key = item.datetime.astimezone(pytz.timezone(item.experience.get_timezone())).strftime(_("%d %b %Y")).format(*'年月日')
            else:
                key = item.datetime.astimezone(pytz.timezone(item.experience.get_timezone())).strftime("%Y-%m-%d")
            if key not in itinerary["days"]:
                itinerary["days"].update({key:[]})
            itinerary["days"][key].append(item.experience)

            if start_datetime > item.datetime:
                start_datetime = item.datetime.astimezone(pytz.timezone(item.experience.get_timezone()))
            if end_datetime < item.datetime:
                end_datetime = item.datetime.astimezone(pytz.timezone(item.experience.get_timezone()))

        for date in daterange(start_datetime, end_datetime):
            if settings.LANGUAGE_CODE == "zh-CN":
                date = date.astimezone(pytz.timezone(ci_timezone)).strftime(_("%d %b %Y")).format(*'年月日')
            else:
                date = date.astimezone(pytz.timezone(ci_timezone)).strftime("%Y-%m-%d")
            if date not in itinerary["days"]:
                itinerary["days"].update({date:[]})

        itinerary["days"] = OrderedDict(sorted(itinerary["days"].items(), key=lambda t: t[0]))
        cover_photo = ""
        for key, value in itinerary["days"].items():
            for item in value:
                if item.photo_set.all():
                    cover_photo = item.photo_set.all()[0]
                    break
            else:
                continue
            break
        guest_number = ci.get_guest_number()
        if settings.LANGUAGE_CODE == "zh-CN":
            start_date = start_datetime.strftime(_("%d %b %Y")).format(*'年月日')
            end_date = end_datetime.strftime(_("%d %b %Y")).format(*'年月日')
            discount_deadline = discount_deadline.strftime(_("%d %b %Y")).format(*'年月日')
        else:
            start_date = start_datetime.strftime("%d/%m/%Y")
            end_date = end_datetime.strftime("%d/%m/%Y")
            discount_deadline = discount_deadline.strftime("%d/%m/%Y")

        return render_to_response('experiences/itinerary_detail.html',
                                  {'itinerary':itinerary, "itinerary_id":ci.id,
                                   "guest_number":guest_number[0],
                                   "adult_number":guest_number[1],
                                   "children_number":guest_number[2],
                                   "start_date":start_date,
                                   "end_date":end_date,
                                   "discount_deadline":discount_deadline,
                                   "price":price,
                                   "full_price":full_price,
                                   "cover_photo":cover_photo,
                                   "preview":preview,
                                   'LANGUAGE':settings.LANGUAGE_CODE,
                                   "GEO_POSTFIX":GEO_POSTFIX},
                                   context)

def itinerary_booking_confirmation(request):
    context = RequestContext(request)
    set_initial_currency(request)
    display_error = False

    if not request.user.is_authenticated():
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/")

    # A HTTP POST?
    if request.method == 'POST':
        form = ItineraryBookingForm(request.POST)

        if 'Stripe' in request.POST or 'stripeToken' in request.POST:
            #submit the form
            display_error = True
            form.data = form.data.copy()
            form.data['custom_currency'] = request.session['custom_currency']
            itinerary = CustomItinerary.objects.get(id=form.data['itinerary_id'])
            form.data['price_paid'] = itinerary.get_price(request.session['custom_currency'])
            if form.is_valid():
                request.user.registereduser.phone_number = form.cleaned_data['phone_number']
                request.user.registereduser.save()

                return itinerary_booking_successful(request, str(form.cleaned_data["itinerary_id"]))
            else:
                #this should not happen, because all required fields were already set
                return render_to_response('experiences/itinerary_booking_confirmation.html', {'form': form,
                                                                        'display_error':display_error,}, context)
        elif 'UnionPay' in request.POST:
            display_error = True
            order_id = make_order_id('Tripalocal')
            form.data = form.data.copy()
            form.data['booking_extra_information'] = order_id
            if form.is_valid():
                config = load_config(os.path.join(settings.PROJECT_ROOT, 'unionpay/settings.yaml').replace('\\', '/'))
                itinerary = CustomItinerary.objects.get(id=form.cleaned_data['itinerary_id'])
                total_price = itinerary.get_price(request.session['custom_currency'])

                if total_price > 0.0:
                    #not free
                    response = client.UnionpayClient(config).pay(int(total_price*100),order_id, channel_type='07',#currency_code=CurrencyCode[experience.currency.upper()],
                                                                 front_url='http://' + settings.ALLOWED_HOSTS[0] + '/itinerary_booking_successful/?itinerary_id=' + str(form.cleaned_data["itinerary_id"]))
                    return HttpResponse(response)
                else:
                    #free
                    return itinerary_booking_successful(request, str(form.cleaned_data["itinerary_id"]))

            else:
                #this should not happen, because all required fields were already set
                return render_to_response('experiences/itinerary_booking_confirmation.html', {'form': form}, context)

        elif 'WeChat' in request.POST:
            display_error = True
            unified_pay = UnifiedOrderPay(settings.WECHAT_APPID, settings.WECHAT_MCH_ID, settings.WECHAT_API_KEY)
            from app.views import create_wx_trade_no
            out_trade_no = create_wx_trade_no(settings.WECHAT_MCH_ID)
            notify_url = request.build_absolute_uri(reverse('wechat_qr_payment_notify'))
            form.data = form.data.copy()
            form.data['booking_extra_information'] = out_trade_no

            if form.is_valid():
                itinerary = CustomItinerary.objects.get(id=form.cleaned_data['itinerary_id'])
                total_price = itinerary.get_price(request.session['custom_currency'])
                currency = request.session['custom_currency']

                if total_price > 0.0:
                    #not free
                    itinerary = CustomItinerary.objects.get(id=form.cleaned_data["itinerary_id"])
                    title = itinerary.title if itinerary.title is not None and len(itinerary.title) > 0 else str(itinerary.id)
                    price = int(convert_currency(total_price, currency, "CNY") * 100)
                    pay_info = unified_pay.post(title, out_trade_no,
                                                str(price), "127.0.0.1", notify_url)
                    if pay_info['return_code'] == 'SUCCESS' and pay_info['result_code'] == 'SUCCESS':
                        code_url = pay_info['code_url']
                        success_url = 'http://' + settings.ALLOWED_HOSTS[0] \
                                      + '/itinerary_booking_successful/?itinerary_id=' + str(form.cleaned_data["itinerary_id"])

                        return redirect(url_with_querystring(reverse('wechat_qr_payment'), code_url=code_url,
                                                             out_trade_no=out_trade_no, success_url=success_url))
                    else:
                        return HttpResponse('<html><body>WeChat Payment Error.</body></html>')
                else:
                    #free
                    return itinerary_booking_successful(request, str(form.cleaned_data["itinerary_id"]))

            else:
                #this should not happen, because all required fields were already set
                return render_to_response('experiences/itinerary_booking_confirmation.html', {'form': form}, context)

        else:
            #TODO
            #submit name missing in IE
            return HttpResponseRedirect(GEO_POSTFIX)
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

def itinerary_booking_successful(request, itinerary_id):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/")

    return HttpResponseRedirect(GEO_POSTFIX + "itinerary/" + itinerary_id)

def itinerary_tool(request, id=None):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/?next=" + GEO_POSTFIX + "itinerary")

    context = RequestContext(request)
    if request.method == 'POST':
        data = request.POST
        title = data.get('title')
        itinerary = json.loads(data.get('dates'))
        bookings = json.loads(data.get('bookings'))['bookings']
        start_date = data.get('start_date')
        guests = data.get('guests')
        profit = data.get('profit')
        ci = CustomItinerary.objects.get(id=id)
        if ci.status.lower() == "paid":
            # cannot edit a paid itinerary
            return HttpResponseRedirect(GEO_POSTFIX + "itinerary/" + str(ci.id) + "/")
        for booking in ci.booking_set.all():
            booking.delete()
        for date, fields in itinerary.items():
            for field, value in fields.items():
                if not isinstance(value, str):
                    for item in value['items']:
                        experience = AbstractExperience.objects.get(id=str(item['id']))
                        #save the custom itinerary as draft
                        local_timezone = pytz.timezone(experience.get_timezone())
                        bk_date = local_timezone.localize(datetime.strptime(str(date), "%Y-%m-%d"))
                        guest_number = [booking['guests'] for booking in bookings if booking['id'] == item['id']]
                        if not guest_number:
                            guest_number = 1
                        else:
                            guest_number = int(guest_number[0])
                        booking = Booking(user = request.user, experience = experience, guest_number = guest_number, total_price = (experience.price * guest_number),
                                        datetime = local_timezone.localize(datetime(bk_date.year, bk_date.month, bk_date.day)).astimezone(pytz.timezone("UTC")),
                                        submitted_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC), status="draft", custom_itinerary=ci)
                        booking.save()
        ci.submitted_datetime = pytz.timezone("UTC").localize(datetime.utcnow())
        ci.title = title
        ci.guests = guests
        ci.profit = profit
        ci.start_datetime = pytz.timezone("UTC").localize(datetime.strptime(start_date, "%Y-%m-%d"))
        ci.save()
        return HttpResponse(json.dumps({'success': 'OK'}), content_type="application/json")
    else:
        ci = CustomItinerary.objects.get(id=id)
        bookings = list(ci.booking_set.order_by('datetime').all()) 
        itinerary = {}
        items = []
        for booking in bookings:
            title = booking.experience.get_information(settings.LANGUAGES[0][0]).title
            type = booking.experience.type.lower()
            if type == 'suggestion' or type == 'privateproduct' or type == 'publicproduct' or type == 'private' or type == 'public':
                type = 'experiences'
            if type == 'flight' or type == 'transfer':
                type = 'transport'
            city = booking.experience.city
            key = booking.datetime.astimezone(pytz.timezone(booking.experience.get_timezone())).strftime('%Y-%m-%d')

            if key not in itinerary:
                itinerary.update({key: {'city': city, 'experiences': { 'items': [], 'host': '', 'display': 'NORMAL' }, 'transport': {'items': [], 'host': '', 'display': 'NORMAL'}, 'accommodation': {'items': [], 'host': '', 'display': 'NORMAL'}, 'restaurants': {'items': [], 'host': '', 'display': 'NORMAL'}}})

            itinerary[key][type]['items'].append({'id': booking.experience.id, 'title': title})
            items.append({'id': booking.experience.id, 'title': title, 'price': int(booking.experience.price), 'guests': booking.guest_number}) 
        context['itinerary'] = json.dumps(itinerary)
        context['itinerary_id'] = id
        context['bookings'] = items
        context['guests'] = ci.guests
        if ci.profit is None:
            context['profit'] = 15
        else:
            context['profit'] = ci.profit
        context['title'] = ci.title
        context['start_date'] = ci.start_datetime.strftime('%Y-%m-%d')
        return render_to_response('experiences/itinerary_tool.html', {}, context)

def campaign(request):
    set_initial_currency(request)
    # NOTE: in the future, we should define these topics globally
    family = AbstractExperience.objects.filter(id__in=[464,2041,26580013,44940013,60230013,33070013,44560013,51790013,87840013,69,408,2551,2671,1571,2561,21580013,31630013,31650013,70550013,76380013,56490013,87350013,1611,20910013,40440013,72360013,70950013,70970013,75690013,84090013,5170013,41390013,58900013,83950013,56280013,56260013,56290013,64060013,63690013,64780013,64770013,64760013,64740013,69540013,75360013,75920013,75900013,85970013,10320013,12200013,58480013,67140013,67120013,67110013,2371,45990013,64040013,64310013,64180013,65340013,56380013,64300013,44110013,75770013,84620013,73960013,81420013,68710013])
    romance = AbstractExperience.objects.filter(id__in=[25730013,25720013,25710013,43650013,43660013,52230013,60430013,40770013,40750013,40740013,40700013,88030013,302,71,28680013,55270013,58330013,70570013,76380013,19940013,20770013,20780013,20810013,20850013,24730013,58760013,58660013,62840013,84100013,58750013,89110013,89100013,41400013,54680013,58910013,62200013,82660013,82670013,62630013,87830013,87870013,73050013,83650013,83670013,83340013,84340013,89060013,39860013,44110013,62260013,63980013,63970013,34600013,34590013,62340013,73630013,83290013,83790013,77420013,83110013,38000013,75180013,65080013,73970013,81350013,81400013,81440013,81410013,84120013,56150013])
    culture = AbstractExperience.objects.filter(id__in=[68690013,52490013,52480013,52500013,64160013,72460013,1981,2021,2,54,106,1591,1971,24460013,88880013,23250013,24180013,55260013,73610013,81360013,45490013,45450013,68970013,32,37,19980013,45030013,52470013,58630013,62850013,48380013,52070013,52120013,55790013,12200013,12210013,67130013,80330013,12180013,12220013,12230013,7420013,65370013,65350013,83660013,82090013,77330013,32550013,40510013,67760013,42410013,81390013,81380013,69140013])
    outdoor = AbstractExperience.objects.filter(id__in=[69530013,75120013,26680013,51780013,51770013,70180013,70190013,70200013,33140013,33110013,44570013,44950013,83100013,87980013,87920013,88020013,88000013,41170013,87210013,209,981,1581,2571,2581,2591,2421,42590013,34220013,73940013,78130013,87340013,87320013,87360013,2351,1651,56350013,60340013,62640013,62860013,73270013,73490013,88560013,80740013,83980013,83970013,18380013,32110013,32150013,67380013,75530013,830013,25100013,41360013,41370013,45090013,45110013,46820013,56270013,61480013,66610013,5220013,45130013,53520013,64050013,64100013,78190013,84130013,84830013,84820013,10320013,58130013,58180013,58420013,58490013,58520013,58510013,80250013,10880013,29640013,58190013,58570013,64320013,64140013,64070013,65380013,64150013,73070013,83850013,35220013,44230013,59830013,63980013,65510013,73870013,74660013,82550013,82560013,33800013,33790013,61970013,83520013,83480013,40530013,56590013,56370013,85480013,68410013,68390013,68580013,38650013,32390013,69570013,66020013,66580013,69000013,56100013,78200013,78230013])
    extreme = AbstractExperience.objects.filter(id__in=[85620013,85610013,85600013,45370013,45380013,45390013,79520013,81670013,84000013,87880013,88010013,852,2441,862,882,24140013,57140013,72180013,34350013,87250013,2291,2381,2411,17260013,70980013,78960013,81510013,84510013,1031,1641,700013,5380013,5390013,25560013,29210013,29220013,29280013,40120013,40130013,40140013,8980013,20250013,64020013,84550013,84570013,86510013,89460013,89450013,89440013,89430013,2081,9280013,10930013,11100013,29620013,29730013,58010013,58230013,80300013,58020013,80320013,10920013,11120013,10900013,10890013,53500013,58200013,77090013,86590013,51180013,51170013,48070013,48060013,62900013,65300013,69420013,69400013,72370013,83860013,58940013,74620013,74510013,74650013,77270013,77280013,77310013,78400013,87190013,80210013,80180013,37640013,43780013,43790013,81370013,89200013])
    photography = AbstractExperience.objects.filter(id__in=[75160013,81800013,33000013,44920013,33020013,33080013,44960013,40810013,87990013,41180013,882,1581,1681,2421,2531,23290013,24140013,24180013,29400013,31630013,69170013,78130013,87340013,2351,2681,1651,20880013,20910013,40440013,73270013,72290013,83990013,58770013,87510013,87500013,1621,67400013,67390013,830013,25100013,29210013,29220013,40120013,40130013,40140013,41360013,41370013,41380013,41420013,5230013,64090013,68000013,82590013,84550013,9280013,29620013,29730013,58010013,80310013,37810013,58210013,65300013,48030013,48080013,48030013,82080013,16460013,44230013,37090013,38930013,77210013,77230013,83900013,40510013,69220013,69230013,85260013,42450013,42440013,42410013,73950013,32380013,32480013,32500013,32510013,41340013,43780013,43790013,68990013,56120013,78320013,81370013])
    topics = [family, romance, culture, outdoor, extreme, photography]
    for experienceList in topics:
        i=0
        while i < len(experienceList):
            experience = experienceList[i]

            setExperienceDisplayPrice(experience)

            experience.image = experience.get_background_image()

            if float(experience.duration).is_integer():
                experience.duration = int(experience.duration)

            experience.city = dict(Location).get(experience.city, experience.city)

            if not experience.currency:
                experience.currency = 'aud'
            convert_experience_price(request, experience)
            experience.dollarsign = DollarSign[experience.currency.upper()]
            experience.currency = str(dict(Currency)[experience.currency.upper()])
            if experience.commission > 0.0:
                experience.commission = round(experience.commission/(1-experience.commission),3)+1
            else:
                experience.commission = settings.COMMISSION_PERCENT+1

            # Format title & Description
            exp_information = experience.get_information(settings.LANGUAGES[0][0])
            experience.description = exp_information.description
            t = exp_information.title
            if (t != None and len(t) > 30):
                experience.title = t[:27] + "..."
            else:
                experience.title = t
            i+=1
    titles = [_('Bring the Kids'), _('Honeymoon'), _('Local Culture'), _('Outdoor'), _('Extreme Experiences'), _('Photography Worthy')]
    urls = ['family', 'romance', 'culture', 'outdoor', 'extreme', 'photography']
    context = RequestContext(request, {
        'topicList': zip(titles, topics, urls),
        'GEO_POSTFIX': settings.GEO_POSTFIX,
        'LANGUAGE': settings.LANGUAGE_CODE
    })
    return render_to_response('app/campaign.html', context)

def topic_family(request):
    set_initial_currency(request)
    experienceList = AbstractExperience.objects.filter(id__in=[464,2041,26580013,44940013,60230013,33070013,44560013,51790013,87840013,69,408,2551,2671,1571,2561,21580013,31630013,31650013,70550013,76380013,56490013,87350013,1611,20910013,40440013,72360013,70950013,70970013,75690013,84090013,5170013,41390013,58900013,83950013,56280013,56260013,56290013,64060013,63690013,64780013,64770013,64760013,64740013,69540013,75360013,75920013,75900013,85970013,10320013,12200013,58480013,67140013,67120013,67110013,2371,45990013,64040013,64310013,64180013,65340013,56380013,64300013,44110013,75770013,84620013,73960013,81420013,68710013])
    i=0
    while i < len(experienceList):
        experience = experienceList[i]

        setExperienceDisplayPrice(experience)

        experience.image = experience.get_background_image()

        if float(experience.duration).is_integer():
            experience.duration = int(experience.duration)

        experience.city = dict(Location).get(experience.city, experience.city)

        if not experience.currency:
            experience.currency = 'aud'
        convert_experience_price(request, experience)
        experience.dollarsign = DollarSign[experience.currency.upper()]
        experience.currency = str(dict(Currency)[experience.currency.upper()])
        if experience.commission > 0.0:
            experience.commission = round(experience.commission/(1-experience.commission),3)+1
        else:
            experience.commission = settings.COMMISSION_PERCENT+1

        # Format title & Description
        exp_information = experience.get_information(settings.LANGUAGES[0][0])
        experience.description = exp_information.description
        t = exp_information.title
        if (t != None and len(t) > 30):
            experience.title = t[:27] + "..."
        else:
            experience.title = t
        i+=1
    template = "experiences/topic_family.html"
    context = RequestContext(request, {
                            'experienceList' : experienceList,
                            'user_email':request.user.email if request.user.is_authenticated() else None,
                            'LANGUAGE':settings.LANGUAGE_CODE,
                            'GEO_POSTFIX': GEO_POSTFIX,
              })
    return render_to_response(template, {}, context)

def topic_romance(request):
    set_initial_currency(request)
    experienceList = AbstractExperience.objects.filter(id__in=[25730013,25720013,25710013,43650013,43660013,52230013,60430013,40770013,40750013,40740013,40700013,88030013,302,71,28680013,55270013,58330013,70570013,76380013,19940013,20770013,20780013,20810013,20850013,24730013,58760013,58660013,62840013,84100013,58750013,89110013,89100013,41400013,54680013,58910013,62200013,82660013,82670013,62630013,87830013,87870013,73050013,83650013,83670013,83340013,84340013,89060013,39860013,44110013,62260013,63980013,63970013,34600013,34590013,62340013,73630013,83290013,83790013,77420013,83110013,38000013,75180013,65080013,73970013,81350013,81400013,81440013,81410013,84120013,56150013])
    i=0
    while i < len(experienceList):
        experience = experienceList[i]

        setExperienceDisplayPrice(experience)

        experience.image = experience.get_background_image()

        if float(experience.duration).is_integer():
            experience.duration = int(experience.duration)

        experience.city = dict(Location).get(experience.city, experience.city)

        if not experience.currency:
            experience.currency = 'aud'
        convert_experience_price(request, experience)
        experience.dollarsign = DollarSign[experience.currency.upper()]
        experience.currency = str(dict(Currency)[experience.currency.upper()])

        if experience.commission > 0.0:
            experience.commission = round(experience.commission/(1-experience.commission),3)+1
        else:
            experience.commission = settings.COMMISSION_PERCENT+1

        # Format title & Description
        exp_information = experience.get_information(settings.LANGUAGES[0][0])
        experience.description = exp_information.description
        t = exp_information.title
        if (t != None and len(t) > 30):
            experience.title = t[:27] + "..."
        else:
            experience.title = t
        i+=1
    template = "experiences/topic_romance.html"
    context = RequestContext(request, {
                            'experienceList' : experienceList,
                            'user_email':request.user.email if request.user.is_authenticated() else None,
                            'LANGUAGE':settings.LANGUAGE_CODE,
                            'GEO_POSTFIX': GEO_POSTFIX,
              })
    return render_to_response(template, {}, context)

def topic_culture(request):
    set_initial_currency(request)
    experienceList = AbstractExperience.objects.filter(id__in=[68690013,52490013,52480013,52500013,64160013,72460013,1981,2021,2,54,106,1591,1971,24460013,88880013,23250013,24180013,55260013,73610013,81360013,45490013,45450013,68970013,32,37,19980013,45030013,52470013,58630013,62850013,48380013,52070013,52120013,55790013,12200013,12210013,67130013,80330013,12180013,12220013,12230013,7420013,65370013,65350013,83660013,82090013,77330013,32550013,40510013,67760013,42410013,81390013,81380013,69140013])
    i=0
    while i < len(experienceList):
        experience = experienceList[i]

        setExperienceDisplayPrice(experience)

        experience.image = experience.get_background_image()

        if float(experience.duration).is_integer():
            experience.duration = int(experience.duration)

        experience.city = dict(Location).get(experience.city, experience.city)

        if not experience.currency:
            experience.currency = 'aud'
        convert_experience_price(request, experience)
        experience.dollarsign = DollarSign[experience.currency.upper()]
        experience.currency = str(dict(Currency)[experience.currency.upper()])
        if experience.commission > 0.0:
            experience.commission = round(experience.commission/(1-experience.commission),3)+1
        else:
            experience.commission = settings.COMMISSION_PERCENT+1

        # Format title & Description
        exp_information = experience.get_information(settings.LANGUAGES[0][0])
        experience.description = exp_information.description
        t = exp_information.title
        if (t != None and len(t) > 30):
            experience.title = t[:27] + "..."
        else:
            experience.title = t
        i+=1
    template = "experiences/topic_culture.html"
    context = RequestContext(request, {
                            'experienceList' : experienceList,
                            'user_email':request.user.email if request.user.is_authenticated() else None,
                            'LANGUAGE':settings.LANGUAGE_CODE,
                            'GEO_POSTFIX': GEO_POSTFIX,
              })
    return render_to_response(template, {}, context)

def topic_outdoor(request):
    set_initial_currency(request)
    experienceList = AbstractExperience.objects.filter(id__in=[69530013,75120013,26680013,51780013,51770013,70180013,70190013,70200013,33140013,33110013,44570013,44950013,83100013,87980013,87920013,88020013,88000013,41170013,87210013,209,981,1581,2571,2581,2591,2421,42590013,34220013,73940013,78130013,87340013,87320013,87360013,2351,1651,56350013,60340013,62640013,62860013,73270013,73490013,88560013,80740013,83980013,83970013,18380013,32110013,32150013,67380013,75530013,830013,25100013,41360013,41370013,45090013,45110013,46820013,56270013,61480013,66610013,5220013,45130013,53520013,64050013,64100013,78190013,84130013,84830013,84820013,10320013,58130013,58180013,58420013,58490013,58520013,58510013,80250013,10880013,29640013,58190013,58570013,64320013,64140013,64070013,65380013,64150013,73070013,83850013,35220013,44230013,59830013,63980013,65510013,73870013,74660013,82550013,82560013,33800013,33790013,61970013,83520013,83480013,40530013,56590013,56370013,85480013,68410013,68390013,68580013,38650013,32390013,69570013,66020013,66580013,69000013,56100013,78200013,78230013])
    i=0
    while i < len(experienceList):
        experience = experienceList[i]

        setExperienceDisplayPrice(experience)

        experience.image = experience.get_background_image()

        if float(experience.duration).is_integer():
            experience.duration = int(experience.duration)

        experience.city = dict(Location).get(experience.city, experience.city)

        if not experience.currency:
            experience.currency = 'aud'
        convert_experience_price(request, experience)
        experience.dollarsign = DollarSign[experience.currency.upper()]
        experience.currency = str(dict(Currency)[experience.currency.upper()])
        if experience.commission > 0.0:
            experience.commission = round(experience.commission/(1-experience.commission),3)+1
        else:
            experience.commission = settings.COMMISSION_PERCENT+1

        # Format title & Description
        exp_information = experience.get_information(settings.LANGUAGES[0][0])
        experience.description = exp_information.description
        t = exp_information.title
        if (t != None and len(t) > 30):
            experience.title = t[:27] + "..."
        else:
            experience.title = t
        i+=1
    template = "experiences/topic_outdoor.html"
    context = RequestContext(request, {
                            'experienceList' : experienceList,
                            'user_email':request.user.email if request.user.is_authenticated() else None,
                            'LANGUAGE':settings.LANGUAGE_CODE,
                            'GEO_POSTFIX': GEO_POSTFIX,
              })
    return render_to_response(template, {}, context)

def topic_extreme(request):
    set_initial_currency(request)
    experienceList = AbstractExperience.objects.filter(id__in=[85620013,85610013,85600013,45370013,45380013,45390013,79520013,81670013,84000013,87880013,88010013,852,2441,862,882,24140013,57140013,72180013,34350013,87250013,2291,2381,2411,17260013,70980013,78960013,81510013,84510013,1031,1641,700013,5380013,5390013,25560013,29210013,29220013,29280013,40120013,40130013,40140013,8980013,20250013,64020013,84550013,84570013,86510013,89460013,89450013,89440013,89430013,2081,9280013,10930013,11100013,29620013,29730013,58010013,58230013,80300013,58020013,80320013,10920013,11120013,10900013,10890013,53500013,58200013,77090013,86590013,51180013,51170013,48070013,48060013,62900013,65300013,69420013,69400013,72370013,83860013,58940013,74620013,74510013,74650013,77270013,77280013,77310013,78400013,87190013,80210013,80180013,37640013,43780013,43790013,81370013,89200013])
    i=0
    while i < len(experienceList):
        experience = experienceList[i]

        setExperienceDisplayPrice(experience)

        experience.image = experience.get_background_image()

        if float(experience.duration).is_integer():
            experience.duration = int(experience.duration)

        experience.city = dict(Location).get(experience.city, experience.city)

        if not experience.currency:
            experience.currency = 'aud'
        convert_experience_price(request, experience)
        experience.dollarsign = DollarSign[experience.currency.upper()]
        experience.currency = str(dict(Currency)[experience.currency.upper()])
        if experience.commission > 0.0:
            experience.commission = round(experience.commission/(1-experience.commission),3)+1
        else:
            experience.commission = settings.COMMISSION_PERCENT+1

        # Format title & Description
        exp_information = experience.get_information(settings.LANGUAGES[0][0])
        experience.description = exp_information.description
        t = exp_information.title
        if (t != None and len(t) > 30):
            experience.title = t[:27] + "..."
        else:
            experience.title = t
        i+=1
    template = "experiences/topic_extreme.html"
    context = RequestContext(request, {
                            'experienceList' : experienceList,
                            'user_email':request.user.email if request.user.is_authenticated() else None,
                            'LANGUAGE':settings.LANGUAGE_CODE,
                            'GEO_POSTFIX': GEO_POSTFIX,
              })
    return render_to_response(template, {}, context)

def topic_photography(request):
    set_initial_currency(request)
    experienceList = AbstractExperience.objects.filter(id__in=[75160013,81800013,33000013,44920013,33020013,33080013,44960013,40810013,87990013,41180013,882,1581,1681,2421,2531,23290013,24140013,24180013,29400013,31630013,69170013,78130013,87340013,2351,2681,1651,20880013,20910013,40440013,73270013,72290013,83990013,58770013,87510013,87500013,1621,67400013,67390013,830013,25100013,29210013,29220013,40120013,40130013,40140013,41360013,41370013,41380013,41420013,5230013,64090013,68000013,82590013,84550013,9280013,29620013,29730013,58010013,80310013,37810013,58210013,65300013,48030013,48080013,48030013,82080013,16460013,44230013,37090013,38930013,77210013,77230013,83900013,40510013,69220013,69230013,85260013,42450013,42440013,42410013,73950013,32380013,32480013,32500013,32510013,41340013,43780013,43790013,68990013,56120013,78320013,81370013])
    i=0
    while i < len(experienceList):
        experience = experienceList[i]

        setExperienceDisplayPrice(experience)

        experience.image = experience.get_background_image()

        if float(experience.duration).is_integer():
            experience.duration = int(experience.duration)

        experience.city = dict(Location).get(experience.city, experience.city)

        if not experience.currency:
            experience.currency = 'aud'
        convert_experience_price(request, experience)
        experience.dollarsign = DollarSign[experience.currency.upper()]
        experience.currency = str(dict(Currency)[experience.currency.upper()])
        if experience.commission > 0.0:
            experience.commission = round(experience.commission/(1-experience.commission),3)+1
        else:
            experience.commission = settings.COMMISSION_PERCENT+1

        # Format title & Description
        exp_information = experience.get_information(settings.LANGUAGES[0][0])
        experience.description = exp_information.description
        t = exp_information.title
        if (t != None and len(t) > 30):
            experience.title = t[:27] + "..."
        else:
            experience.title = t
        i+=1
    template = "experiences/topic_photography.html"
    context = RequestContext(request, {
                            'experienceList' : experienceList,
                            'user_email':request.user.email if request.user.is_authenticated() else None,
                            'LANGUAGE':settings.LANGUAGE_CODE,
                            'GEO_POSTFIX': GEO_POSTFIX,
              })
    return render_to_response(template, {}, context)

def multi_day_trip(request):
    experienceList = Experience.objects.filter(status='Listed', type='ITINERARY')
    i=0
    while i < len(experienceList):
        experience = experienceList[i]

        setExperienceDisplayPrice(experience)

        experience.image = experience.get_background_image()

        if not experience.currency:
            experience.currency = 'aud'
        experience.dollarsign = DollarSign[experience.currency.upper()]
        experience.currency = str(dict(Currency)[experience.currency.upper()])

        # Format title & Description
        exp_information = experience.get_information(settings.LANGUAGES[0][0])
        experience.description = exp_information.description
        t = exp_information.title
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
                    payment.street2 = ret['txnTime']
                    payment.save()

                    experience = AbstractExperience.objects.get(id=bk.experience_id)
                    user = User.objects.get(id=bk.user_id)
                    bk.datetime = bk.datetime.astimezone(pytz.timezone(experience.get_timezone()))
                    send_booking_email_verification(bk, experience, user,
                                                    instant_booking(experience, bk.datetime.date(), bk.datetime.time()))
                    sms_notification(bk, experience, user, payment.phone_number)
                else:
                    itinerary = CustomItinerary.objects.filter(note=ret['orderId'])
                    if itinerary is not None and len(itinerary)>0:
                        itinerary = itinerary[0]
                        itinerary.status = "paid"
                        itinerary.save()

                        payment = itinerary.payment
                        payment.charge_id = ret['queryId']
                        payment.street2 = ret['txnTime']
                        payment.save()

                        #issue 284
                        mail.send(subject=_('[Tripalocal] Your booking request has been sent'),
                                  message='',
                                  sender=Aliases.objects.filter(destination__contains=user.email)[0].mail,
                                  recipients = ['order@tripalocal.com'],
                                  priority='now',
                                  html_message=loader.render_to_string('experiences/email_product_requested.html',
                                                                        {'product_title': itinerary.title,
                                                                        'product_url':settings.DOMAIN_NAME + '/itinerary/' + str(itinerary.id),
                                                                        'booking':bk,
                                                                        'LANGUAGE':settings.LANGUAGE_CODE}))

                logger.debug("payment success:"+str(ret['orderId']))
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
    if pay_info.get("return_code","") == 'SUCCESS' and pay_info.get("result_code","") == 'SUCCESS':
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

                experience = AbstractExperience.objects.get(id=bk.experience_id)
                user = User.objects.get(id=bk.user_id)
                bk.datetime = bk.datetime.astimezone(pytz.timezone(experience.get_timezone()))
                send_booking_email_verification(bk, experience, user,
                                                instant_booking(experience, bk.datetime.date(), bk.datetime.time()))
                sms_notification(bk, experience, user, payment.phone_number)
            else:
                itinerary = CustomItinerary.objects.filter(note=out_trade_no)
                if itinerary is not None and len(itinerary)>0:
                    itinerary = itinerary[0]
                    itinerary.status = "paid"
                    itinerary.save()

                    payment = itinerary.payment
                    payment.charge_id = transaction_id
                    payment.save()
            xml = dict_to_xml({'return_code': 'SUCCESS', 'return_msg': 'OK'})
            return HttpResponse(xml)
    else:
        return HttpResponse('')
