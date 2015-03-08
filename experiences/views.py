from django.shortcuts import render, get_object_or_404, render_to_response
from django.db.models import Q
from experiences.models import Experience, WhatsIncluded, Photo, BlockOutTimePeriod, InstantBookingTimePeriod
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.contrib.formtools.wizard.views import SessionWizardView, NamedUrlSessionWizardView
from experiences.forms import *
from datetime import *
import pytz, string, os, json, math, PIL, xlsxwriter
from django.template import RequestContext, loader
from experiences.models import Experience, Booking, Payment
from django.contrib.auth.models import User
from Tripalocal_V1 import settings
from decimal import Decimal
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile, File
from django.contrib import messages
from tripalocal_messages.models import Aliases
from experiences.models import Review, Photo, Coupon, BlockOutTimePeriod, InstantBookingTimePeriod, WhatsIncluded
from app.forms import SubscriptionForm
from mixpanel import Mixpanel
from dateutil.relativedelta import relativedelta
from django.db import connections
from app.models import RegisteredUser
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.files.storage import FileSystemStorage
from PIL import Image
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from post_office import mail
from collections import OrderedDict

MaxPhotoNumber=10

def experience_fee_calculator(price):
    if type(price)==int or type(price) == float:
        return round(price*(1.00+settings.COMMISSION_PERCENT)*(1.00+settings.STRIPE_PRICE_PERCENT) + settings.STRIPE_PRICE_FIXED,2)

    return price

def next_time_slot(repeat_cycle, repeat_frequency, repeat_extra_information, current_datetime):
    current_datetime_local = current_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))

    if pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone(settings.TIME_ZONE)).dst() != timedelta(0):#daylight saving
        if not current_datetime_local.dst() != timedelta(0):# not daylight saving
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

def experience_availability(request):
    if not request.user.is_authenticated() or not request.user.is_staff:
        return HttpResponseRedirect("/")

    context = RequestContext(request)
    form = ExperienceAvailabilityForm()

    if request.method == 'POST':
        form = ExperienceAvailabilityForm(request.POST)

        if form.is_valid():   
            end_datetime = form.cleaned_data['end_datetime'] if 'end_datetime' in form.cleaned_data and form.cleaned_data['end_datetime'] != None else pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime('2015-04-06 00:00', "%Y-%m-%d %H:%M"))
            local_timezone = pytz.timezone(settings.TIME_ZONE)
            available_options = []
            #add title
            dict = {'id':'Id', 'title':'Title', 'host':'Host', 'dates':{}}
            sdt = form.cleaned_data['start_datetime'] if 'start_datetime' in form.cleaned_data and form.cleaned_data['start_datetime'] != None else pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime('2015-03-06 00:00', "%Y-%m-%d %H:%M"))
            while (sdt <= end_datetime):
                dict['dates'][sdt.astimezone(local_timezone).strftime("%Y/%m/%d")] = [{'time_string':sdt.astimezone(local_timezone).strftime("%m/%d")}]
                sdt += relativedelta(days=1)
            dict['dates'] = OrderedDict(sorted(dict['dates'].items(), key=lambda t: t[0]))
            available_options.append(dict)

            experiences = Experience.objects.filter(status='Listed')
            for experience in experiences:
                sdt = form.cleaned_data['start_datetime'] if 'start_datetime' in form.cleaned_data and form.cleaned_data['start_datetime'] != None else pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime('2015-03-06 00:00', "%Y-%m-%d %H:%M"))
                last_sdt = pytz.timezone('UTC').localize(datetime.min)

                host = experience.hosts.all()[0]
                experience_avail = {'id':experience.id, 'title': experience.title, 'host':host.first_name + ' ' + host.last_name, 'dates':{}}

                blockouts = experience.blockouttimeperiod_set.filter(experience_id=experience.id)
                blockout_start = []
                blockout_end = []
                blockout_index=0
                #calculate all the blockout time periods
                for blk in blockouts :
                    if blk.repeat:
                        b_l =  blk.end_datetime - blk.start_datetime
                        if not blk.repeat_end_date or blk.repeat_end_date > (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date():
                            blk.repeat_end_date = (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date()
                        while blk.start_datetime.date() <= blk.repeat_end_date:
                            blockout_index += 1
                            blockout_start.append(blk.start_datetime)
                            blockout_end.append(blk.start_datetime + b_l)

                            blk.start_datetime = next_time_slot(blk.repeat_cycle, blk.repeat_frequency, blk.repeat_extra_information, blk.start_datetime)

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
                    if ib.repeat:
                        ib_l =  ib.end_datetime - ib.start_datetime
                        if not ib.repeat_end_date or ib.repeat_end_date > (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date():
                            ib.repeat_end_date = (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date()
                        while ib.start_datetime.date() <= ib.repeat_end_date:
                            instantbooking_index += 1
                            instantbooking_start.append(ib.start_datetime)
                            instantbooking_end.append(ib.start_datetime + ib_l)

                            ib.start_datetime = next_time_slot(ib.repeat_cycle, ib.repeat_frequency, ib.repeat_extra_information, ib.start_datetime)

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
                    if pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone(settings.TIME_ZONE)).dst() != timedelta(0):#daylight saving
                        if not sdt_local.dst() != timedelta(0):# not daylight saving
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
                                i += experience.guest_number_max #change from bking.guest_number to experience.guest_number_max

                        if i==0: #< experience.guest_number_max :
                            if experience.repeat_cycle != "" or (sdt_local.time().hour > 7 and sdt_local.time().hour <22):
                                istant_booking = False
                                #instantbooking_start, instantbooking_end are sorted, sdt keeps increasing
                                #instantbooking_i: skip the periods already checked
                                for ib_i in range(instantbooking_i, instantbooking_index):
                                    if (instantbooking_start[ib_i] <= sdt and sdt <= instantbooking_end[ib_i]): # and (instantbooking_start[ib_i] <= sdt+relativedelta(hours=+experience.duration) and sdt+relativedelta(hours=+experience.duration) <= instantbooking_end[ib_i]):
                                        istant_booking = True
                                        break
                                    if sdt+relativedelta(hours=+experience.duration) < instantbooking_start[ib_i]:
                                        #no need to check further slots after the current one
                                        break 
                                    if sdt > instantbooking_start[ib_i]:
                                        instantbooking_i += 1

                                dict = {'available_seat': experience.guest_number_max - i, 
                                        'time_string': sdt_local.strftime("%H"), 
                                        'instant_booking': istant_booking}
                                experience_avail['dates'][sdt_local.strftime("%Y/%m/%d")].append(dict)

                    sdt += timedelta(hours=1)
                experience_avail['dates'] = OrderedDict(sorted(experience_avail['dates'].items(), key=lambda t: t[0]))
                available_options.append(experience_avail)

            workbook = xlsxwriter.Workbook(os.path.join(os.path.join(settings.PROJECT_ROOT,'xls'), 'Experience availability.xlsx'))
            worksheet = workbook.add_worksheet()

            row = 0
            for experience in available_options:
                col = 0
                worksheet.write(row, col, experience['id'])
                col += 1
                worksheet.write(row, col, experience['title'])
                col += 1
                worksheet.write(row, col, experience['host'])
                col += 1
                for date, slots in experience['dates'].items():
                    str=''
                    for slot in slots:
                        str += slot['time_string']
                        if 'instant_booking' in slot and slot['instant_booking']:
                            str += '(I)'
                        str += ' '
                    worksheet.write(row, col, str)
                    col += 1
                row += 1
            workbook.close()

            return render_to_response('experience_availability.html', {'form':form,'available_options':available_options}, context)

    return render_to_response('experience_availability.html', {'form':form}, context)

class ExperienceListView(ListView):
    template_name = 'experience_list.html'
    #paginate_by = 9
    #context_object_name = 'experience_list'

    def get_queryset(self):
        if self.request.user.is_authenticated() and self.request.user.is_superuser:
            return Experience.objects.all#()
        else:
            return HttpResponseRedirect("/admin/login/?next=/experiencelist") #self.request.user.experience_hosts.all()

class ExperienceDetailView(DetailView):
    model = Experience
    template_name = 'experience_detail.html'
    #context_object_name = 'experience'

    def post(self, request, *args, **kwargs):
        #if not request.user.is_authenticated():
        #    return HttpResponseForbidden()

        self.object = self.get_object()
        
        if request.method == 'POST':
            form = BookingConfirmationForm(request.POST)
            form.data = form.data.copy()
            form.data['user_id'] = request.user.id;
            experience = Experience.objects.get(id=form.data['experience_id'])
            experience_price = experience.price

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

            return render(request, 'experience_booking_confirmation.html', 
                          {'form': form, #'eid':self.object.id, 
                           'experience': experience,
                           'experience_price': experience_price,
                           'guest_number':form.data['guest_number'],
                           'date':form.data['date'],
                           'time':form.data['time'],
                           'subtotal_price':round(subtotal_price*(1.00+settings.COMMISSION_PERCENT),2),
                           'service_fee':round(subtotal_price*(1.00+settings.COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                           'total_price': experience_fee_calculator(subtotal_price)
                           })

    def get_context_data(self, **kwargs):
        context = super(ExperienceDetailView, self).get_context_data(**kwargs)
        experience = context['experience']
        sdt = experience.start_datetime
        last_sdt = pytz.timezone('UTC').localize(datetime.min)
        local_timezone = pytz.timezone(settings.TIME_ZONE)
        available_options = []
        available_date = ()

        if experience.end_datetime < datetime.utcnow().replace(tzinfo=pytz.UTC):
            if self.request.user.id != experience.hosts.all()[0].id:
                # other user, experience already expired
                context['expired'] = True
                return context
            else:
                # host, experience already expired
                context['host_only_expired'] = True
                return context

        if not experience.status.lower() == "listed":
            if self.request.user.id != experience.hosts.all()[0].id:
                # other user, experience not published
                context['listed'] = False
                return context
            else:
                # host, experience not published
                context['host_only_unlisted'] = True
                return context

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
        sdt = datetime.utcnow().replace(tzinfo=pytz.UTC).replace(minute=0, second=0, microsecond=0) + relativedelta(hours=+6)

        blockouts = experience.blockouttimeperiod_set.filter(experience_id=experience.id)
        blockout_start = []
        blockout_end = []
        blockout_index=0
        #calculate all the blockout time periods
        for blk in blockouts :
            if blk.repeat:
                b_l =  blk.end_datetime - blk.start_datetime
                if not blk.repeat_end_date or blk.repeat_end_date > (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date():
                    blk.repeat_end_date = (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date()
                while blk.start_datetime.date() <= blk.repeat_end_date:
                    blockout_index += 1
                    blockout_start.append(blk.start_datetime)
                    blockout_end.append(blk.start_datetime + b_l)

                    blk.start_datetime = next_time_slot(blk.repeat_cycle, blk.repeat_frequency, blk.repeat_extra_information, blk.start_datetime)

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
            if ib.repeat:
                ib_l =  ib.end_datetime - ib.start_datetime
                if not ib.repeat_end_date or ib.repeat_end_date > (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date():
                    ib.repeat_end_date = (datetime.utcnow().replace(tzinfo=pytz.UTC) + relativedelta(months=+2)).date()
                while ib.start_datetime.date() <= ib.repeat_end_date:
                    instantbooking_index += 1
                    instantbooking_start.append(ib.start_datetime)
                    instantbooking_end.append(ib.start_datetime + ib_l)

                    ib.start_datetime = next_time_slot(ib.repeat_cycle, ib.repeat_frequency, ib.repeat_extra_information, ib.start_datetime)

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
            if pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone(settings.TIME_ZONE)).dst() != timedelta(0):#daylight saving
                if not sdt_local.dst() != timedelta(0):# not daylight saving
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
                        i += experience.guest_number_max #change from bking.guest_number to experience.guest_number_max

                if i == 0: #< experience.guest_number_max :
                    if experience.repeat_cycle != "" or (sdt_local.time().hour > 7 and sdt_local.time().hour <22):
                        istant_booking = False
                        #instantbooking_start, instantbooking_end are sorted, sdt keeps increasing
                        #instantbooking_i: skip the periods already checked
                        for ib_i in range(instantbooking_i, instantbooking_index):
                            if (instantbooking_start[ib_i] <= sdt and sdt <= instantbooking_end[ib_i]):# and (instantbooking_start[ib_i] <= sdt+relativedelta(hours=+experience.duration) and sdt+relativedelta(hours=+experience.duration) <= instantbooking_end[ib_i]):
                                istant_booking = True
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
                                'instant_booking': istant_booking}
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

        context['available_options'] = available_options
        context['form'] = BookingForm(available_date, experience.id)

        WhatsIncludedList = WhatsIncluded.objects.filter(experience=experience)
        included_list = WhatsIncludedList.filter(included=True)
        not_included_list = WhatsIncludedList.filter(included=False)
        context['included_list'] = included_list
        context['not_included_list'] = not_included_list
        
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

        host_image = experience.hosts.all()[0].registereduser.image_url
        if host_image == None or len(host_image) == 0:
            context['host_image'] = 'profile_default.jpg'
        else:
            context['host_image'] = host_image

        return context

FORMS = (("experience", ExperienceForm),
         ("calendar", ExperienceCalendarForm),
         ("price",ExperiencePriceForm),
         ("overview",ExperienceOverviewForm),
         ("detail",ExperienceDetailForm),
         ("photo",ExperiencePhotoForm),
         ("location",ExperienceLocationForm),
         ) #("summary",ExperienceSummaryForm)

TEMPLATES = {"experience": "add_experience_experience.html",
             "calendar": "add_experience_calendar.html",
             "price":"add_experience_price.html",
             "overview":"add_experience_overview.html",
             "detail":"add_experience_detail.html",
             "photo":"add_experience_photo.html",
             "location":"add_experience_location.html"
             } #"summary":"add_experience_summary.html"

EXPERIENCE_IMAGE_SIZE_LIMIT = 2097152

#def login_check(user):
#    return user.is_authenticated()

def initializeExperience(experience, data):
    data.clear()

    cursor = connections['cndb'].cursor()
    row = cursor.execute("select title, description, activity, interaction, dress, meetup_spot from experiences_experience where id = %s", [experience.id]).fetchone()
    
    if row:
        data['title_other'] = row[0]
        data['summary_other'] = row[1]
        data['activity_other'] = row[2] 
        data['interaction_other'] = row[3]
        data['dress_code_other'] = row[4]
        data['meetup_spot_other'] = row[5]

    rows = cursor.execute("select item, details from experiences_whatsincluded where experience_id = %s", [experience.id]).fetchall()
    if rows:
        for index in range(len(rows)):
            if rows[index][0] == "Food":
                data['included_food_detail_other'] = rows[index][1]
            elif rows[index][0] == "Transport":
                data['included_transport_detail_other'] = rows[index][1]
            elif rows[index][0] == "Ticket":
                data['included_ticket_detail_other'] = rows[index][1]

    data['id'] = experience.id
    if experience.type != None:
        data['type'] = experience.type.upper()
    else:
        data['type'] = experience.type
    data['title'] = experience.title
    data['max_guest_number'] = experience.guest_number_max
    data['location'] = experience.city

    data['start_datetime'] = experience.start_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
    data['end_datetime'] = experience.end_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
    blockouts = BlockOutTimePeriod.objects.filter(experience_id = experience.id)
    for index in range(len(blockouts)):
        data['blockout_start_datetime_'+str(index+1)] = blockouts[index].start_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
        data['blockout_end_datetime_'+str(index+1)] = blockouts[index].end_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
        data['blockout_repeat_'+str(index+1)] = blockouts[index].repeat
        data['blockout_repeat_cycle_'+str(index+1)] = blockouts[index].repeat_cycle
        data['blockout_repeat_frequency_'+str(index+1)] = blockouts[index].repeat_frequency
        data['blockout_repeat_end_date_'+str(index+1)] = blockouts[index].repeat_end_date
        data['blockout_repeat_extra_information_'+str(index+1)] = blockouts[index].repeat_extra_information

    instant_bookings = InstantBookingTimePeriod.objects.filter(experience_id = experience.id)
    for index in range(len(instant_bookings)):
        data['instant_booking_start_datetime_'+str(index+1)] = instant_bookings[index].start_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
        data['instant_booking_end_datetime_'+str(index+1)] = instant_bookings[index].end_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
        data['instant_booking_repeat_'+str(index+1)] = instant_bookings[index].repeat
        data['instant_booking_repeat_cycle_'+str(index+1)] = instant_bookings[index].repeat_cycle
        data['instant_booking_repeat_frequency_'+str(index+1)] = instant_bookings[index].repeat_frequency
        data['instant_booking_repeat_end_date_'+str(index+1)] = instant_bookings[index].repeat_end_date
        data['instant_booking_repeat_extra_information_'+str(index+1)] = instant_bookings[index].repeat_extra_information

    data['duration'] = experience.duration
    data['min_guest_number'] = experience.guest_number_min
    #data['max_guest_number'] = experience.guest_number_max
    data['price'] = experience.price
    data['dynamic_price'] = experience.dynamic_price
    if experience.price != None:
        data['price_with_booking_fee'] = round(float(experience.price)*(1.00+settings.COMMISSION_PERCENT),2)
    else:
        data['price_with_booking_fee'] = ''
    includes = WhatsIncluded.objects.filter(experience_id = experience.id)
    for index in range(len(includes)):
        if includes[index].item == "Food":
            if includes[index].included:
                data['included_food'] = "Yes"
            else:
                data['included_food'] = "No"
            data['included_food_detail'] = includes[index].details
        elif includes[index].item == "Transport":
            if includes[index].included:
                data['included_transport'] = "Yes"
            else:
                data['included_transport'] = "No"
            data['included_transport_detail'] = includes[index].details
        elif includes[index].item == "Ticket":
            if includes[index].included:
                data['included_ticket'] = "Yes"
            else:
                data['included_ticket'] = "No"
            data['included_ticket_detail'] = includes[index].details

    data['summary'] = experience.description
    data['language'] = experience.language
    data['activity'] = experience.activity
    data['interaction'] = experience.interaction
    data['dress_code'] = experience.dress

    photos = Photo.objects.filter(experience_id = experience.id)
    for index in range(len(photos)):
        #photos[index].name.split('.')[0].split('_')[1] instead of str(index+1)
        data['experience_photo_' + photos[index].name.split('.')[0].split('_')[1]] = photos[index]

    data['meetup_spot'] = experience.meetup_spot
    data['suburb'] = experience.city

def save_exit_experience(wizard):
    for step_name in ['experience','calendar','price','overview','detail','photo','location']:
        if 'wizard_save_exit_'+ step_name in wizard.request.POST and step_name + '-changed_steps' in wizard.request.POST and wizard.request.POST[step_name + '-changed_steps'].find('experience') == -1:
            return False

    return True

def save_exit_price(wizard):
    #if "save and exit" is clicked, skip the remaining steps
    #for save_exit in ['wizard_save_exit_calendar']:
    #    if save_exit in wizard.request.POST:
    #        return False
    for step_name in ['experience','calendar','price','overview','detail','photo','location']:
        if 'wizard_save_exit_'+ step_name in wizard.request.POST and step_name + '-changed_steps' in wizard.request.POST and wizard.request.POST[step_name + '-changed_steps'].find('price') == -1:
            return False

    return True

def save_exit_overview(wizard):
    #if "save and exit" is clicked, skip the remaining steps
    #for save_exit in ['wizard_save_exit_calendar','wizard_save_exit_price']:
    #    if save_exit in wizard.request.POST:
    #        return False
    for step_name in ['experience','calendar','price','overview','detail','photo','location']:
        if 'wizard_save_exit_'+ step_name in wizard.request.POST and step_name + '-changed_steps' in wizard.request.POST and wizard.request.POST[step_name + '-changed_steps'].find('overview') == -1:
            return False

    return True

def save_exit_detail(wizard):
    #if "save and exit" is clicked, skip the remaining steps
    #for save_exit in ['wizard_save_exit_calendar','wizard_save_exit_price','wizard_save_exit_overview']:
    #    if save_exit in wizard.request.POST:
    #        return False
    for step_name in ['experience','calendar','price','overview','detail','photo','location']:
        if 'wizard_save_exit_'+ step_name in wizard.request.POST and step_name + '-changed_steps' in wizard.request.POST and wizard.request.POST[step_name + '-changed_steps'].find('detail') == -1:
            return False

    return True

def save_exit_photo(wizard):
    #if "save and exit" is clicked, skip the remaining steps
    #for save_exit in ['wizard_save_exit_calendar','wizard_save_exit_price','wizard_save_exit_overview','wizard_save_exit_detail']:
    #    if save_exit in wizard.request.POST:
    #        return False
    for step_name in ['experience','calendar','price','overview','detail','photo','location']:
        if 'wizard_save_exit_'+ step_name in wizard.request.POST and step_name + '-changed_steps' in wizard.request.POST and wizard.request.POST[step_name + '-changed_steps'].find('photo') == -1:
            return False

    return True

def save_exit_location(wizard):
    #if "save and exit" is clicked, skip the remaining steps
    #for save_exit in ['wizard_save_exit_calendar','wizard_save_exit_price','wizard_save_exit_overview','wizard_save_exit_detail','wizard_save_exit_photo']:
    #    if save_exit in wizard.request.POST:
    #        return False
    for step_name in ['experience','calendar','price','overview','detail','photo','location']:
        if 'wizard_save_exit_'+ step_name in wizard.request.POST and step_name + '-changed_steps' in wizard.request.POST and wizard.request.POST[step_name + '-changed_steps'].find('location') == -1:
            return False

    return True

#@user_passes_test(login_check, login_url='/accounts/login?next=/addexperience')
class ExperienceWizard(NamedUrlSessionWizardView):
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp'))

    #template_name = 'add_experience_experience.html'
    form_list = [ExperienceForm, ExperienceCalendarForm, ExperiencePriceForm, ExperienceOverviewForm, 
                 ExperienceDetailForm, ExperiencePhotoForm, ExperienceLocationForm] # , ExperienceSummaryForm

    #form_list = (('start',ExperienceForm), ('calendar', ExperienceCalendarForm), ('price', ExperiencePriceForm), ('overview', ExperienceOverviewForm), 
    #             ('detail', ExperienceDetailForm), ('photo', ExperiencePhotoForm), ('location', ExperienceLocationForm),)

    def dispatch(self, request, *args, **kwargs):
        #if edit
        if self.request.resolver_match.url_name.startswith('experience_edit'):
            #id only exists in the first step
            id = self.request.GET.get('id')
            if id:
                experience = get_object_or_404(Experience, pk=id)
                if not experience.hosts.all()[0] == self.request.user and not self.request.user.is_superuser:
                    #the user is neither the host nor a superuser
                    return HttpResponseRedirect("/")

                #if kwargs['step'] != "experience":
                #    #not start from the first step
                #    return HttpResponseRedirect("/editexperience/experience?id="+id)
            elif not len(self.initial_dict):
                return HttpResponseRedirect("/")

        return super(ExperienceWizard, self).dispatch(request, *args, **kwargs)

    def post(self, *args, **kwargs):
        for save_exit in ['wizard_save_exit_calendar','wizard_save_exit_price','wizard_save_exit_overview','wizard_save_exit_detail','wizard_save_exit_photo','wizard_save_exit_location']:
            if save_exit in self.request.POST:
                kwargs['step'] = 'done'
                self.kwargs['step'] = 'done'

                form = self.get_form(data=self.request.POST, files=self.request.FILES)
                if form.is_valid():
                    self.storage.set_step_data(self.steps.current, self.process_step(form))
                    self.storage.set_step_files(self.steps.current, self.process_step_files(form))
                    return self.render_done(form, **kwargs)

        if self.request.resolver_match.url_name.startswith('experience_edit'):
            #only allow "jumps" when editing
            next_step = self.request.POST.get('wizard_next_step', None)  # get the step name
            form = self.get_form(data=self.request.POST, files=self.request.FILES)

            #if current step is the last step, and the user clicks on a previous step, 
            #save the form and go to the previous step, instead of submiting the form 
            if self.steps.current == self.steps.last and next_step and next_step in self.get_form_list():
                if form.is_valid():
                    self.storage.set_step_data(self.steps.current, self.process_step(form))
                    self.storage.set_step_files(self.steps.current, self.process_step_files(form))
                    return self.render_goto_step(next_step)

            return super(ExperienceWizard, self).post(*args, **kwargs)
        else:
            return super(ExperienceWizard, self).post(*args, **kwargs)

    #def render_done(self, form, **kwargs):
    #    """
    #    When rendering the done view, we have to redirect first (if the URL
    #    name doesn't fit).
    #    """
    #    if kwargs.get('step', None) != self.done_step_name:
    #        return redirect(self.get_step_url(self.done_step_name))
    #    return super(ExperienceWizard, self).render_done(form, **kwargs)

    def get_next_step(self, step=None):
        return self.request.POST.get('wizard_next_step', super(ExperienceWizard, self).get_next_step(step))

        ##next_step = self.request.POST.get('wizard_next_step', None)

        ##if step is None:
        ##    step = self.steps.current
        ##form_list = self.get_form_list()
        ##keys = list(form_list.keys())
        ##if next_step != None:
        ##    key = next_step
        ##else:
        ##    key = keys.index(step) + 1
        ##if len(keys) > key:
        ##    return keys[key]
        ##return None

    def get_context_data(self, form, **kwargs):
        context = super(ExperienceWizard, self).get_context_data(form=form, **kwargs)
        context.update({'language': "en"})
        #if edit
        if self.request.resolver_match.url_name.startswith('experience_edit'):
            context.update({'edit': True})
        else:
            context.update({'edit': False})

        return context

    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def get_form(self, step=None, data=None, files=None):
        #clear previously unsubmitted data
        if self.request.path.find('editexperience') > 0:
            if self.kwargs['step'] != 'done' and data and not ('id' in self.initial_dict and self.kwargs['step']+'-id' in data and str(self.initial_dict['id']) == data[self.kwargs['step']+'-id']):
                data = None
            if self.request.GET and 'id' in self.request.GET and 'id' in self.initial_dict and self.request.GET['id'] != str(self.initial_dict['id']):
                data = None
        elif self.request.path.find('addexperience') > 0:
            if self.kwargs['step'] != 'done' and data and self.kwargs['step']+'-id' in data and data[self.kwargs['step']+'-id']:
                data = None

        if step:
            step_files = self.storage.get_step_files(step)
        else:
            step_files = self.storage.current_step_files

        if step_files and files:
            for key, value in step_files.items():
                if key in files and files[key] is not None:
                    step_files[key] = files[key]
        elif files:
            step_files = files

        return super(ExperienceWizard, self).get_form(step, data, step_files)

        # this runs for the step it's on as well as for the step before
    def get_form_initial(self, step):
        #current_step = self.storage.current_step

        #if edit
        if self.request.resolver_match.url_name.startswith('experience_edit'):
            #id only exists in the first step
            id = self.request.GET.get('id')
            if id: #not self.initial_dict or
                experience = get_object_or_404(Experience, pk=id)
                if self.initial_dict:
                    self.initial_dict.clear()
                initializeExperience(experience, self.initial_dict)
                
        #override the initial values with inputs from previous steps
        if step == 'price':
            prev_data = self.storage.get_step_data('experience')
            if prev_data:
                duration = prev_data.get('experience-duration','')
                self.initial_dict['duration'] = duration
                if self.request.resolver_match.url_name.startswith('experience_add'):
                    return self.initial_dict.get(step, {'duration': duration})
        elif step == 'overview':
            prev_data = self.storage.get_step_data('experience')
            if prev_data:
                title = prev_data.get('experience-title','')
                self.initial_dict['title'] = title
                if self.request.resolver_match.url_name.startswith('experience_add'):
                    return self.initial_dict.get(step, {'title': title})
        elif step == 'photo':
            data = {}
            prev_files = self.storage.get_step_files('photo')
            if prev_files:
                for i in range(1,MaxPhotoNumber+1):
                    if 'photo-experience_photo_' + str(i) in prev_files:
                        data['experience_photo_' + str(i)] = prev_files['photo-experience_photo_' + str(i)]
                        self.initial_dict['experience_photo_' + str(i)] = prev_files['photo-experience_photo_' + str(i)]
            if self.request.resolver_match.url_name.startswith('experience_add'):
                return self.initial_dict.get(step, data)
        elif step == 'location':
            prev_data = self.storage.get_step_data('experience')
            if prev_data:
                suburb = prev_data.get('experience-location','')
                self.initial_dict['suburb'] = suburb
                if self.request.resolver_match.url_name.startswith('experience_add'):
                    return self.initial_dict.get(step, {'suburb': suburb})
        
        visited_steps = ''
        for step_name in ['experience','calendar','price','overview','detail','photo','location']:
            prev_data = self.storage.get_step_data(step_name)
            steps = prev_data.get(step_name+'-changed_steps','') if prev_data != None else None
            if steps != None and len(steps)>len(visited_steps):
                visited_steps = steps

        self.initial_dict['changed_steps']=visited_steps

        return self.initial_dict #self.initial_dict.get(step, {})

    def done(self, form_list, **kwargs):
        f=[]

        type= self.initial_dict['type'] if 'type' in self.initial_dict else None
        title= self.initial_dict['title'] if 'title' in self.initial_dict else None
        duration= self.initial_dict['duration'] if 'duration' in self.initial_dict else None
        suburb= self.initial_dict['suburb'] if 'suburb' in self.initial_dict else None
        if 'experience' in kwargs['form_dict']:
            prev_data = kwargs['form_dict']['experience'].cleaned_data
            type = prev_data.get('type', None)
            title = prev_data.get('title', None)
            duration = prev_data.get('duration', None)
            suburb = prev_data.get('location', None)

        blockout = {}
        instant_booking = {}
        if self.request.resolver_match.url_name.startswith('experience_edit'):
            #calendar is skipped when adding experience
            prev_data = kwargs['form_dict']['calendar'].cleaned_data
            start_datetime = prev_data['start_datetime']
            end_datetime = prev_data['end_datetime']
            for i in range(1,6):
                blockout['blockout_start_datetime_'+str(i)] = prev_data['blockout_start_datetime_'+str(i)]
                blockout['blockout_end_datetime_'+str(i)] = prev_data['blockout_end_datetime_'+str(i)]
                blockout['blockout_repeat_'+str(i)] = prev_data['blockout_repeat_'+str(i)]
                blockout['blockout_repeat_cycle_'+str(i)] = prev_data['blockout_repeat_cycle_'+str(i)]
                blockout['blockout_repeat_frequency_'+str(i)] = prev_data['blockout_repeat_frequency_'+str(i)]
                blockout['blockout_repeat_extra_information_'+str(i)] = prev_data['blockout_repeat_extra_information_'+str(i)]
                blockout['blockout_repeat_end_date_'+str(i)] = prev_data['blockout_repeat_end_date_'+str(i)]
                if blockout['blockout_repeat_'+str(i)]:
                    #for daily and weekly repeated time slot, the start and end hours must be in the same day
                    if blockout['blockout_repeat_cycle_'+str(i)] != 'Monthly' and blockout['blockout_start_datetime_'+str(i)].date() != blockout['blockout_end_datetime_'+str(i)].date():
                        blockout['blockout_end_datetime_'+str(i)] = blockout['blockout_start_datetime_'+str(i)].replace(hour=23, minute=59)
                    #for monthly repeated time slot, the start and end days must be in the same month
                    if blockout['blockout_repeat_cycle_'+str(i)] == 'Monthly' and blockout['blockout_start_datetime_'+str(i)].month != blockout['blockout_end_datetime_'+str(i)].month:
                        blockout['blockout_end_datetime_'+str(i)] = (blockout['blockout_end_datetime_'+str(i)]-timedelta(days=blockout['blockout_end_datetime_'+str(i)].day)).replace(hour=23, minute=59)
                    if blockout['blockout_repeat_cycle_'+str(i)] == 'Weekly':
                        days= ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                        if blockout['blockout_repeat_extra_information_'+str(i)] == None:
                            blockout['blockout_repeat_extra_information_'+str(i)] = days[blockout['blockout_start_datetime_'+str(i)].weekday()]+';'
                        elif not days[blockout['blockout_start_datetime_'+str(i)].weekday()] in blockout['blockout_repeat_extra_information_'+str(i)].split(';'):
                            blockout['blockout_repeat_extra_information_'+str(i)] += days[blockout['blockout_start_datetime_'+str(i)].weekday()]+';'

                instant_booking['instant_booking_start_datetime_'+str(i)] = prev_data['instant_booking_start_datetime_'+str(i)]
                instant_booking['instant_booking_end_datetime_'+str(i)] = prev_data['instant_booking_end_datetime_'+str(i)]
                instant_booking['instant_booking_repeat_'+str(i)] = prev_data['instant_booking_repeat_'+str(i)]
                instant_booking['instant_booking_repeat_cycle_'+str(i)] = prev_data['instant_booking_repeat_cycle_'+str(i)]
                instant_booking['instant_booking_repeat_frequency_'+str(i)] = prev_data['instant_booking_repeat_frequency_'+str(i)]
                instant_booking['instant_booking_repeat_extra_information_'+str(i)] = prev_data['instant_booking_repeat_extra_information_'+str(i)]
                instant_booking['instant_booking_repeat_end_date_'+str(i)] = prev_data['instant_booking_repeat_end_date_'+str(i)]
                if instant_booking['instant_booking_repeat_'+str(i)]:
                    if instant_booking['instant_booking_repeat_cycle_'+str(i)] != 'Monthly' and instant_booking['instant_booking_start_datetime_'+str(i)].date() != instant_booking['instant_booking_end_datetime_'+str(i)].date():
                        instant_booking['instant_booking_end_datetime_'+str(i)] = instant_booking['instant_booking_start_datetime_'+str(i)].replace(hour=23, minute=59)
                    #for monthly repeated time slot, the start and end days must be in the same month
                    if instant_booking['instant_booking_repeat_cycle_'+str(i)] == 'Monthly' and instant_booking['instant_booking_start_datetime_'+str(i)].month != instant_booking['instant_booking_end_datetime_'+str(i)].month:
                        instant_booking['instant_booking_end_datetime_'+str(i)] = (instant_booking['instant_booking_end_datetime_'+str(i)]-timedelta(days=instant_booking['instant_booking_end_datetime_'+str(i)].day)).replace(hour=23, minute=59)
                    if instant_booking['instant_booking_repeat_cycle_'+str(i)] == 'Weekly':
                        days= ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                        if instant_booking['instant_booking_repeat_extra_information_'+str(i)] == None:
                            instant_booking['instant_booking_repeat_extra_information_'+str(i)] = days[instant_booking['instant_booking_start_datetime_'+str(i)].weekday()]+';'
                        elif not days[instant_booking['instant_booking_start_datetime_'+str(i)].weekday()] in instant_booking['instant_booking_repeat_extra_information_'+str(i)].split(';'):
                            instant_booking['instant_booking_repeat_extra_information_'+str(i)] += days[instant_booking['instant_booking_start_datetime_'+str(i)].weekday()]+';'

        min_guest_number = self.initial_dict['min_guest_number'] if 'min_guest_number' in self.initial_dict else 1
        max_guest_number = self.initial_dict['max_guest_number'] if 'max_guest_number' in self.initial_dict else 10
        price = self.initial_dict['price'] if 'price' in self.initial_dict else 0
        price_with_booking_fee = self.initial_dict['price_with_booking_fee'] if 'price_with_booking_fee' in self.initial_dict else 0
        dynamic_price = self.initial_dict['dynamic_price'] if 'dynamic_price' in self.initial_dict else None
        if 'price' in kwargs['form_dict']:
            prev_data = kwargs['form_dict']['price'].cleaned_data
            duration = prev_data['duration']
            min_guest_number = prev_data['min_guest_number']
            max_guest_number = prev_data['max_guest_number']
            if min_guest_number!=None and max_guest_number!=None and min_guest_number > max_guest_number:
                temp = max_guest_number
                max_guest_number = min_guest_number
                min_guest_number = temp
            price = prev_data['price']
            price_with_booking_fee = prev_data['price_with_booking_fee']
            dynamic_price = prev_data['dynamic_price']

        summary = self.initial_dict['summary'] if 'summary' in self.initial_dict else None
        language = self.initial_dict['language'] if 'language' in self.initial_dict else None
        title_other = self.initial_dict['title_other'] if 'title_other' in self.initial_dict else None
        summary_other = self.initial_dict['summary_other'] if 'summary_other' in self.initial_dict else None
        if 'overview' in kwargs['form_dict']:
            prev_data = kwargs['form_dict']['overview'].cleaned_data
            title = prev_data['title']
            summary = prev_data['summary']
            language = prev_data['language']
            title_other = prev_data['title_other']
            if not title_other:
                title_other = title
            summary_other = prev_data['summary_other']
            if not summary_other:
                summary_other = summary

        activity = self.initial_dict['activity'] if 'activity' in self.initial_dict else None
        interaction = self.initial_dict['interaction'] if 'interaction' in self.initial_dict else None
        dress_code = self.initial_dict['dress_code'] if 'dress_code' in self.initial_dict else None
        included_food = self.initial_dict['included_food'] if 'included_food' in self.initial_dict else None
        included_food_detail = self.initial_dict['included_food_detail'] if 'included_food_detail' in self.initial_dict else None
        included_transport = self.initial_dict['included_transport'] if 'included_transport' in self.initial_dict else None
        included_transport_detail = self.initial_dict['included_transport_detail'] if 'included_transport_detail' in self.initial_dict else None
        included_ticket = self.initial_dict['included_ticket'] if 'included_ticket' in self.initial_dict else None
        included_ticket_detail = self.initial_dict['included_ticket_detail'] if 'included_ticket_detail' in self.initial_dict else None
        activity_other = self.initial_dict['activity_other'] if 'activity_other' in self.initial_dict else None
        interaction_other = self.initial_dict['interaction_other'] if 'interaction_other' in self.initial_dict else None
        dress_code_other = self.initial_dict['dress_code_other'] if 'dress_code_other' in self.initial_dict else None
        included_food_detail_other = self.initial_dict['included_food_detail_other'] if 'included_food_detail_other' in self.initial_dict else None
        included_transport_detail_other =  self.initial_dict['included_transport_detail_other'] if 'included_transport_detail_other' in self.initial_dict else None
        included_ticket_detail_other = self.initial_dict['included_ticket_detail_other'] if 'included_ticket_detail_other' in self.initial_dict else None
        if 'detail' in kwargs['form_dict']:
            prev_data = kwargs['form_dict']['detail'].cleaned_data
            activity = prev_data['activity']
            interaction = prev_data['interaction']
            dress_code = prev_data['dress_code']
            included_food = prev_data['included_food']
            included_food_detail = prev_data['included_food_detail']
            included_transport = prev_data['included_transport']
            included_transport_detail = prev_data['included_transport_detail']
            included_ticket = prev_data['included_ticket']
            included_ticket_detail = prev_data['included_ticket_detail']
            activity_other = prev_data['activity_other']
            interaction_other = prev_data['interaction_other']
            dress_code_other = prev_data['dress_code_other']
            included_food_detail_other = prev_data['included_food_detail_other']
            included_transport_detail_other = prev_data['included_transport_detail_other']
            included_ticket_detail_other = prev_data['included_ticket_detail_other']
            if not activity_other:
                activity_other = activity
            if not interaction_other:
                interaction_other = interaction
            if not dress_code_other:
                dress_code_other = dress_code
            if not included_food_detail_other:
                included_food_detail_other = included_food_detail
            if not included_transport_detail_other:
                included_transport_detail_other = included_transport_detail
            if not included_ticket_detail_other:
                included_ticket_detail_other = included_ticket_detail

        meetup_spot = self.initial_dict['meetup_spot'] if 'meetup_spot' in self.initial_dict else None
        meetup_spot_other = self.initial_dict['meetup_spot_other'] if 'meetup_spot_other' in self.initial_dict else None
        if 'location' in kwargs['form_dict']:
            prev_data = kwargs['form_dict']['location'].cleaned_data
            suburb = prev_data['suburb']
            meetup_spot = prev_data['meetup_spot']
            meetup_spot_other = prev_data['meetup_spot_other']

        if self.request.resolver_match.url_name.startswith('experience_add'):
            #if add
            experience = Experience(start_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC).replace(minute=0),
                                    end_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC).replace(minute=0) + relativedelta(years=10),
                                    repeat_cycle = 'Daily',
                                    repeat_frequency = 1,
                                    title = title, 
                                    description = summary,
                                    guest_number_min = min_guest_number,
                                    guest_number_max = max_guest_number,
                                    price = price,
                                    dynamic_price = dynamic_price,
                                    duration = duration,
                                    activity = activity,
                                    interaction = interaction,
                                    dress = dress_code,
                                    city = suburb,
                                    meetup_spot = meetup_spot,
                                    status = "Unlisted",
                                    type=type,
                                    language = language
                                    )

            experience.save()
            #add the user to the host list
            #experience.hosts.add(self.request.user)
            cursor = connections['experiencedb'].cursor()
            cursor.execute("Insert into experiences_experience_hosts ('experience_id','user_id') values (%s, %s)", [experience.id, self.request.user.id])
            
            #copy to the chinese database
            cursor = connections['cndb'].cursor()
            cursor.execute("insert into experiences_experience ('id', 'start_datetime', 'end_datetime', 'repeat_cycle', 'repeat_frequency', " 
                           + "'title', 'description', 'guest_number_min', 'guest_number_max', 'price', 'dynamic_price', 'duration', 'activity', 'interaction', "
                           + "'dress', 'city', 'meetup_spot', 'status', 'type', 'language')"
                           + " values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                           [experience.id, experience.start_datetime, experience.end_datetime, experience.repeat_cycle, experience.repeat_frequency,
                            title_other, summary_other, experience.guest_number_min, experience.guest_number_max, experience.price, experience.dynamic_price, experience.duration, activity_other, interaction_other,
                            dress_code_other, experience.city, meetup_spot_other, "Unlisted", experience.type, experience.language])

            #copy to the chinese database
            cursor = connections['cndb'].cursor()
            cursor.execute("Insert into experiences_experience_hosts ('experience_id','user_id') values (%s, %s)", [experience.id, self.request.user.id])

        else:
            #if edit
            experience = get_object_or_404(Experience, pk=self.initial_dict['id'])
            #experience.start_datetime = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(start_datetime, "%Y-%m-%d %H:%M")).astimezone(pytz.timezone('UTC')).replace(minute=0)
            #experience.end_datetime = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(end_datetime, "%Y-%m-%d %H:%M")).astimezone(pytz.timezone('UTC')).replace(minute=0)
            experience.title = title
            experience.description = summary
            experience.guest_number_min = min_guest_number
            experience.guest_number_max = max_guest_number
            experience.price = price
            experience.dynamic_price = dynamic_price
            experience.duration = duration
            experience.activity = activity
            experience.interaction = interaction
            experience.dress = dress_code
            experience.city = suburb
            experience.meetup_spot = meetup_spot
            experience.type=type
            experience.language = language

            experience.save()

            #copy to the chinese database
            cursor = connections['cndb'].cursor()
            cursor.execute("update experiences_experience set title=%s, description=%s, guest_number_min=%s, guest_number_max=%s," 
                           + "price=%s, dynamic_price=%s, duration=%s, activity=%s, interaction=%s, "
                           + "dress=%s, city=%s, meetup_spot=%s, type=%s, language=%s where id = %s", 
                           [title_other, summary_other, experience.guest_number_min, experience.guest_number_max, experience.price, experience.dynamic_price, experience.duration, activity_other, interaction_other,
                            dress_code_other, experience.city, meetup_spot_other, experience.type, experience.language, experience.id])

            #delete old whatsincluded records
            cursor = connections['cndb'].cursor()
            includes = WhatsIncluded.objects.filter(experience_id=experience.id)
            for include in includes:
                if included_food != None and include.item =='Food':
                    include.delete()
                    cursor.execute("delete from experiences_whatsincluded where experience_id = %s and item='Food'", [experience.id])
                if included_ticket != None and include.item =='Ticket':
                    include.delete()
                    cursor.execute("delete from experiences_whatsincluded where experience_id = %s and item='Ticket'", [experience.id])
                if included_transport != None and include.item =='Transport':
                    include.delete()
                    cursor.execute("delete from experiences_whatsincluded where experience_id = %s and item='Transport'", [experience.id])

            #delete old records of blockout periods, instant booking periods
            obls = BlockOutTimePeriod.objects.filter(experience = experience)
            for obl in obls:
                obl.delete()
            oibs = InstantBookingTimePeriod.objects.filter(experience = experience)
            for oib in oibs:
                oib.delete()
            #delete from chinese database
            cursor = connections['cndb'].cursor()
            cursor.execute("delete from experiences_blockouttimeperiod where experience_id = %s", [experience.id])
            cursor.execute("delete from experiences_instantbookingtimeperiod where experience_id = %s", [experience.id])

            #save blockout periods, instant booking periods
            for i in range(1,6):
                if blockout['blockout_start_datetime_'+str(i)] and blockout['blockout_end_datetime_'+str(i)]:
                    if blockout['blockout_repeat_end_date_'+str(i)]:
                        b = BlockOutTimePeriod(start_datetime = blockout['blockout_start_datetime_'+str(i)].astimezone(pytz.timezone('UTC')).replace(minute=0), 
                                                end_datetime = blockout['blockout_end_datetime_'+str(i)].astimezone(pytz.timezone('UTC')).replace(minute=0),
                                                repeat = blockout['blockout_repeat_'+str(i)], 
                                                repeat_cycle = blockout['blockout_repeat_cycle_'+str(i)], 
                                                repeat_frequency = blockout['blockout_repeat_frequency_'+str(i)],
                                                repeat_extra_information = blockout['blockout_repeat_extra_information_'+str(i)],
                                                repeat_end_date = blockout['blockout_repeat_end_date_'+str(i)],
                                                experience = experience
                                                )
                    else:
                        b = BlockOutTimePeriod(start_datetime = blockout['blockout_start_datetime_'+str(i)].astimezone(pytz.timezone('UTC')).replace(minute=0), 
                                                end_datetime = blockout['blockout_end_datetime_'+str(i)].astimezone(pytz.timezone('UTC')).replace(minute=0),
                                                repeat = blockout['blockout_repeat_'+str(i)], 
                                                repeat_cycle = blockout['blockout_repeat_cycle_'+str(i)], 
                                                repeat_frequency = blockout['blockout_repeat_frequency_'+str(i)],
                                                repeat_extra_information = blockout['blockout_repeat_extra_information_'+str(i)],
                                                repeat_end_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime("2049-12-31", "%Y-%m-%d")).astimezone(pytz.timezone('UTC')),
                                                experience = experience
                                                )
                    b.save()
                    #copy to chinese database
                    cursor = connections['cndb'].cursor()
                    cursor.execute("Insert into experiences_blockouttimeperiod ('experience_id','start_datetime','end_datetime','repeat', 'repeat_cycle', 'repeat_frequency', 'repeat_extra_information', 'repeat_end_date')"
                                   + " values (%s, %s, %s, %s, %s, %s, %s, %s)", 
                                   [experience.id, b.start_datetime, b.end_datetime, b.repeat, b.repeat_cycle, b.repeat_frequency, b.repeat_extra_information, b.repeat_end_date])
                
                if instant_booking['instant_booking_start_datetime_'+str(i)] and instant_booking['instant_booking_end_datetime_'+str(i)]:
                    if instant_booking['instant_booking_repeat_end_date_'+str(i)]:
                        ib = InstantBookingTimePeriod(start_datetime = instant_booking['instant_booking_start_datetime_'+str(i)].astimezone(pytz.timezone('UTC')).replace(minute=0), 
                                                end_datetime = instant_booking['instant_booking_end_datetime_'+str(i)].astimezone(pytz.timezone('UTC')).replace(minute=0),
                                                repeat = instant_booking['instant_booking_repeat_'+str(i)], 
                                                repeat_cycle = instant_booking['instant_booking_repeat_cycle_'+str(i)], 
                                                repeat_frequency = instant_booking['instant_booking_repeat_frequency_'+str(i)],
                                                repeat_extra_information = instant_booking['instant_booking_repeat_extra_information_'+str(i)],
                                                repeat_end_date = instant_booking['instant_booking_repeat_end_date_'+str(i)],
                                                experience = experience
                                                )
                    else:
                        ib = InstantBookingTimePeriod(start_datetime = instant_booking['instant_booking_start_datetime_'+str(i)].astimezone(pytz.timezone('UTC')).replace(minute=0), 
                                                end_datetime = instant_booking['instant_booking_end_datetime_'+str(i)].astimezone(pytz.timezone('UTC')).replace(minute=0),
                                                repeat = instant_booking['instant_booking_repeat_'+str(i)], 
                                                repeat_cycle = instant_booking['instant_booking_repeat_cycle_'+str(i)], 
                                                repeat_frequency = instant_booking['instant_booking_repeat_frequency_'+str(i)],
                                                repeat_extra_information = instant_booking['instant_booking_repeat_extra_information_'+str(i)],
                                                repeat_end_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime("2049-12-31", "%Y-%m-%d")).astimezone(pytz.timezone('UTC')),
                                                experience = experience
                                                )
                    ib.save()
                    #copy to chinese database
                    cursor = connections['cndb'].cursor()
                    cursor.execute("Insert into experiences_instantbookingtimeperiod ('experience_id','start_datetime','end_datetime','repeat', 'repeat_cycle', 'repeat_frequency', 'repeat_extra_information', 'repeat_end_date')"
                                   + " values (%s, %s, %s, %s, %s, %s, %s, %s)", 
                                   [experience.id, ib.start_datetime, ib.end_datetime, ib.repeat, ib.repeat_cycle, ib.repeat_frequency, ib.repeat_extra_information, ib.repeat_end_date])

        #common part
        #save what's included
        if included_food != None:
            food = WhatsIncluded(item='Food', included = (included_food=='Yes'), details = included_food_detail, experience = experience)
            food.save()
            #copy to chinese database
            cursor = connections['cndb'].cursor()
            cursor.execute("Insert into experiences_whatsincluded ('experience_id','item','included','details') values (%s, %s, %s, %s)", 
                            [experience.id, 'Food', (included_food=='Yes'), included_food_detail_other])
        if included_ticket != None:
            ticket = WhatsIncluded(item='Ticket', included = (included_ticket=='Yes'), details = included_ticket_detail, experience = experience)
            ticket.save()
            #copy to chinese database
            cursor = connections['cndb'].cursor()
            cursor.execute("Insert into experiences_whatsincluded ('experience_id','item','included','details') values (%s, %s, %s, %s)", 
                        [experience.id, 'Ticket', (included_ticket=='Yes'), included_ticket_detail_other])
        if included_transport != None:
            transport = WhatsIncluded(item='Transport', included = (included_transport=='Yes'), details = included_transport_detail, experience = experience)
            transport.save()
            #copy to chinese database
            cursor = connections['cndb'].cursor()
            cursor.execute("Insert into experiences_whatsincluded ('experience_id','item','included','details') values (%s, %s, %s, %s)", 
                            [experience.id, 'Transport', (included_transport=='Yes'), included_transport_detail_other])
                        
        #save images
        dirname = settings.MEDIA_ROOT + '/experiences/' + str(experience.id) + '/'
        if not os.path.isdir(dirname):
            os.mkdir(dirname)

        prev_files = self.storage.get_step_files('photo')

        thumbnail_created = False
        if prev_files:
            for index in range(1,MaxPhotoNumber+1):
                if 'photo-experience_photo_' + str(index) in prev_files:
                    content = prev_files['photo-experience_photo_'+str(index)]
                    content_type = content.content_type.split('/')[0]
                    if content_type == "image":
                        if content._size > EXPERIENCE_IMAGE_SIZE_LIMIT:
                            raise forms.ValidationError(_('Please keep filesize under %s. Current filesize %s') % (filesizeformat(EXPERIENCE_IMAGE_SIZE_LIMIT), filesizeformat(content._size)))
                    else:
                        raise forms.ValidationError(_('File type is not supported'))

                    name, extension = os.path.splitext(content.name)
                    extension = extension.lower();
                    if extension in ('.bmp', '.png', '.jpeg', '.jpg') :
                        extension = '.jpg'
                        filename = 'experience' + str(experience.id) + '_' + str(index) + extension
                        for chunk in content.chunks():
                            destination = open(dirname + filename, 'wb+')               
                            destination.write(chunk)
                            destination.close()

                        #copy to the chinese website -- folder+file
                        dirname_other = settings.MEDIA_ROOT.replace("Tripalocal_V1","Tripalocal_CN") + '/experiences/' + str(experience.id) + '/'
                        if not os.path.isdir(dirname_other):
                            os.mkdir(dirname_other)

                        subprocess.Popen(['cp',dirname + filename, dirname_other + filename])

                        #create the corresponding thumbnail (force .jpg)
                        if not thumbnail_created:
                            thumbnail_created = True
                            basewidth = 400
                            img = Image.open(dirname + filename)
                            wpercent = (basewidth/float(img.size[0]))
                            hsize = int((float(img.size[1])*float(wpercent)))
                            img1 = img.resize((basewidth,hsize), PIL.Image.ANTIALIAS)
                            img1.save(settings.MEDIA_ROOT + '/thumbnails/experiences/experience' + str(experience.id) + '_1.jpg')

                            #copy to the chinese website -- folder+file
                            dirname_other = settings.MEDIA_ROOT.replace("Tripalocal_V1","Tripalocal_CN") + '/thumbnails/experiences/'
                            if not os.path.isdir(dirname_other):
                                os.mkdir(dirname_other)

                            subprocess.Popen(['cp',settings.MEDIA_ROOT + '/thumbnails/experiences/experience' + str(experience.id) + '_1.jpg', dirname_other + 'experience' + str(experience.id) + '_1.jpg'])

                        if not len(experience.photo_set.filter(name__startswith=filename))>0:
                            photo = Photo(name = filename, directory = 'experiences/' + str(experience.id) + '/', 
                                          image = 'experiences/' + str(experience.id) + '/' + filename, experience = experience)
                            photo.save()
                            #copy to the chinese database
                            cursor = connections['cndb'].cursor()
                            cursor.execute("Insert into experiences_photo ('experience_id','name','directory','image')"
                               + " values (%s, %s, %s, %s)", 
                               [experience.id, photo.name, photo.directory, photo.image.name])

        for form in form_list:
            #if type(form) != ExperienceSummaryForm:
            f.append(form)

        kwargs['form_dict']['experience'] = ExperienceForm()
        kwargs['form_dict']['calendar'] = ExperienceCalendarForm()
        kwargs['form_dict']['price'] = ExperiencePriceForm()
        kwargs['form_dict']['overview'] = ExperienceOverviewForm()
        kwargs['form_dict']['detail'] = ExperienceDetailForm()
        kwargs['form_dict']['location'] = ExperienceLocationForm()
        kwargs['form_dict']['photo'] = ExperiencePhotoForm()

        #if self.request.resolver_match.url_name.startswith('experience_add'):
        #    return render_to_response('experience_confirmation.html', { 'experience':experience, 'add':True
        #        #'form_list': f, #'form_data': [form.cleaned_data for form in form_list],
        #    })
        #else:
        #    return render_to_response('experience_confirmation.html', { 'experience':experience, 'add':False
        #        #'form_list': f, #'form_data': [form.cleaned_data for form in form_list],
        #    })
        return HttpResponseRedirect("/mylisting")

def experience_booking_successful(request, experience, guest_number, booking_datetime):
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/accounts/login/")
    
    mp = Mixpanel(settings.MIXPANEL_TOKEN)
    mp.track(request.user.email, 'Sent request to '+ experience.hosts.all()[0].first_name)

    return render(request,'experience_booking_successful.html',{'experience': experience,
                                                                    'guest_number':guest_number,
                                                                    'booking_datetime':booking_datetime,
                                                                    'user':request.user,
                                                                    'experience_url':'http://' + settings.DOMAIN_NAME + '/experience/' + str(experience.id)})

def experience_booking_confirmation(request):
    # Get the context from the request.
    context = RequestContext(request)
    display_error = False

    if not request.user.is_authenticated():
        return HttpResponseRedirect("/accounts/login/")

    # A HTTP POST?
    if request.method == 'POST':
        form = BookingConfirmationForm(request.POST)
        experience = Experience.objects.get(id=form.data['experience_id'])

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
            else:
                #wrong dynamic settings
                subtotal_price = float(experience.price)*float(form.data['guest_number'])
        else:
            subtotal_price = float(experience.price)*float(form.data['guest_number'])

        if 'Refresh' in request.POST:
            #get coupon information
            wrong_promo_code = False
            code = form.data['promo_code']
            coupons = Coupon.objects.filter(promo_code__iexact = code,
                                            end_datetime__gt = datetime.utcnow().replace(tzinfo=pytz.UTC),
                                            start_datetime__lt = datetime.utcnow().replace(tzinfo=pytz.UTC))
            if not len(coupons):
                coupon = Coupon()
                wrong_promo_code = True
            else:
                #check if the coupon can be used on this experience
                if not coupons[0].rules or not coupons[0].rules.strip():
                    coupon = coupons[0]
                elif (not "ids" in json.loads(coupons[0].rules)) or experience.id in json.loads(coupons[0].rules)["ids"]:
                    coupon = coupons[0]
                else:
                    coupon = Coupon()
                    wrong_promo_code = True

            mp = Mixpanel(settings.MIXPANEL_TOKEN)
            mp.track(request.user.email, 'Clicked on "Refresh"')

            return render_to_response('experience_booking_confirmation.html', {'form': form, 
                                                                           'user_email':request.user.email,
                                                                           'wrong_promo_code':wrong_promo_code,
                                                                           'coupon':coupon,
                                                                           'experience': experience, 
                                                                           'guest_number':form.data['guest_number'],
                                                                           'date':form.data['date'],
                                                                           'time':form.data['time'],
                                                                           'subtotal_price':round(subtotal_price*(1.00+settings.COMMISSION_PERCENT),2),
                                                                           'service_fee':round(subtotal_price*(1.00+settings.COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                                                                           'total_price': experience_fee_calculator(subtotal_price)}, context)

        else:
            #submit the form
            display_error = True
            if form.is_valid():
                return experience_booking_successful(request, 
                                                     experience, 
                                                     int(form.data['guest_number']),
                                                     datetime.strptime(form.data['date'] + " " + form.data['time'], "%Y-%m-%d %H:%M"))
            
            else:
                return render_to_response('experience_booking_confirmation.html', {'form': form, 
                                                                                   'user_email':request.user.email,
                                                                           'display_error':display_error,
                                                                           'experience': experience, 
                                                                           'guest_number':form.data['guest_number'],
                                                                           'date':form.data['date'],
                                                                           'time':form.data['time'],
                                                                           'subtotal_price':round(subtotal_price*(1.00+settings.COMMISSION_PERCENT),2),
                                                                           'service_fee':round(subtotal_price*(1.00+settings.COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                                                                           'total_price': experience_fee_calculator(subtotal_price)}, context)
    else:
        # If the request was not a POST
        #form = BookingConfirmationForm()
        return HttpResponseRedirect("/")

    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    # return render_to_response('experience_booking_confirmation.html', {'form': form, 'display_error':display_error,}, context)

def create_experience(request, id=None):
    context = RequestContext(request)
    data={}
    files={}
    display_error = False

    if not request.user.is_authenticated() or not request.user.is_staff:
        return HttpResponseRedirect("/admin")

    if id:
        experience = get_object_or_404(Experience, pk=id)
        list = experience.whatsincluded_set.filter(item="Food")
        if len(list) > 0: 
            if list[0].included:
                included_food = "Yes" 
            else:
                included_food = "No" 
            include_food_detail = list[0].details
        else:
            included_food = "No"
            include_food_detail = None
        
        list = experience.whatsincluded_set.filter(item="Ticket")
        if len(list) >0:
            if list[0].included:
                included_ticket = "Yes"
            else:
                included_ticket = "No"
            included_ticket_detail = list[0].details
        else:
            included_ticket = "No"
            included_ticket_detail = None

        list = experience.whatsincluded_set.filter(item="Transport")
        if len(list) >0:
            if list[0].included:
                included_transport = "Yes"
            else:
                included_transport = "No"
            included_transport_detail = list[0].details
        else:
            included_transport = "No"
            included_transport_detail = None

        data = {"id":experience.id,
            "host":experience.hosts.all()[0].email,
            "language":experience.language,
            "start_datetime":experience.start_datetime,
            "end_datetime":experience.end_datetime,
            #"repeat_cycle":experience.repeat_cycle,
            #"repeat_frequency":experience.repeat_frequency,
            "title":experience.title,
            "summary":experience.description,
            "guest_number_min":experience.guest_number_min,
            "guest_number_max":experience.guest_number_max,
            "price":round(experience.price,2),
            "price_with_booking_fee":round(experience.price*Decimal.from_float(1.00+settings.COMMISSION_PERCENT)*Decimal.from_float(1.00+settings.STRIPE_PRICE_PERCENT)+Decimal.from_float(settings.STRIPE_PRICE_FIXED),2),
            "duration":experience.duration,
            "included_food":included_food,
            "included_food_detail":include_food_detail,
            "included_ticket":included_ticket,
            "included_ticket_detail":included_ticket_detail,
            "included_transport":included_transport,
            "included_transport_detail":included_transport_detail,
            "activity":experience.activity,
            "interaction":experience.interaction,
            "dress_code":experience.dress,
            "suburb":experience.city,
            "meetup_spot":experience.meetup_spot,
            "status":experience.status
        }

        for i in range(1,MaxPhotoNumber+1):
            list = experience.photo_set.filter(name__startswith='experience'+str(id)+'_'+str(i))
            if len(list)>0:
                photo = list[0]
                files['experience_photo_'+str(i)] = SimpleUploadedFile(settings.MEDIA_ROOT+'/'+photo.directory+photo.name, 
                                                                             File(open(settings.MEDIA_ROOT+'/'+photo.directory+photo.name, 'rb')).read())
                data['experience_photo_'+str(i)] = photo.image
            #else:
            #    photos['experience'+str(id)+'_'+str(i)] = None
        #if experience.hosts.all()[0] != request.user:
        #    return HttpResponseForbidden()
    else:
        experience = Experience()

    if request.method == 'POST':
        form = CreateExperienceForm(request.POST, request.FILES)
        display_error = True

        if form.is_valid():
            if not id:
                try:
                    #check if the user exist
                    user = User.objects.get(email=form.data['host'])
                except User.DoesNotExist:
                    form.add_error("host","host email does not exist")
                    return render_to_response('create_experience.html', {'form': form, 'display_error':display_error}, context)

                #create a new experience
                experience = Experience(id=form.data['id'],
                                        start_datetime = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['start_datetime'], "%Y-%m-%d %H:%M")).astimezone(pytz.timezone('UTC')),
                                        end_datetime = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['end_datetime'], "%Y-%m-%d %H:%M")).astimezone(pytz.timezone('UTC')),
                                        repeat_cycle = "Hourly",
                                        repeat_frequency = 1,
                                        title = form.data['title'], 
                                        description = form.data['summary'],
                                        guest_number_min = form.data['guest_number_min'],
                                        guest_number_max = form.data['guest_number_max'],
                                        price = form.data['price'],
                                        duration = form.data['duration'],
                                        activity = form.data['activity'],
                                        interaction = form.data['interaction'],
                                        dress = form.data['dress_code'],
                                        city = form.data['suburb'],
                                        meetup_spot = form.data['meetup_spot'],
                                        status = form.data['status'],
                                        language = form.data['language']
                                        )
            
            else:
                experience.id = form.data['id']
                experience.language = form.data['language']
                experience.start_datetime = datetime.strptime(form.data['start_datetime'], "%Y-%m-%d %H:%M")
                experience.end_datetime = datetime.strptime(form.data['end_datetime'], "%Y-%m-%d %H:%M")
                #experience.repeat_cycle = form.data['repeat_cycle']
                #experience.repeat_frequency = form.data['repeat_frequency']
                experience.title = form.data['title']
                experience.description = form.data['summary']
                experience.guest_number_min = form.data['guest_number_min']
                experience.guest_number_max = form.data['guest_number_max']
                experience.price = form.data['price']
                experience.duration = form.data['duration']
                experience.activity = form.data['activity']
                experience.interaction = form.data['interaction']
                experience.dress = form.data['dress_code']
                experience.city = form.data['suburb']
                experience.meetup_spot = form.data['meetup_spot']
                experience.status = form.data['status']
            
            experience.save()
            #add the user to the host list
            if not id and user:
                #experience.hosts.add(user)
                cursor = connections['experiencedb'].cursor()
                cursor.execute("Insert into experiences_experience_hosts ('experience_id','user_id') values (%s, %s)", [experience.id, user.id])
            
            #save images
            dirname = settings.MEDIA_ROOT + '/experiences/' + str(experience.id) + '/'
            if not os.path.isdir(dirname):
                os.mkdir(dirname)

            count = 0
            thumbnail_created = False
            for index in range (1,MaxPhotoNumber+1):
                if 'experience_photo_'+str(index) in request.FILES:
                    content = request.FILES['experience_photo_'+str(index)]
                    content_type = content.content_type.split('/')[0]
                    if content_type == "image":
                        if content._size > EXPERIENCE_IMAGE_SIZE_LIMIT:
                            raise forms.ValidationError(_('Please keep filesize under %s. Current filesize %s') % (filesizeformat(EXPERIENCE_IMAGE_SIZE_LIMIT), filesizeformat(content._size)))
                    else:
                        raise forms.ValidationError(_('File type is not supported'))

                    #count += 1 #count does not necessarily equal index
                    name, extension = os.path.splitext(request.FILES['experience_photo_'+str(index)].name)
                    extension = extension.lower();
                    if extension in ('.bmp', '.png', '.jpeg', '.jpg') :
                        filename = 'experience' + str(experience.id) + '_' + str(index) + extension
                        for chunk in request.FILES['experience_photo_'+str(index)].chunks():
                            destination = open(dirname + filename, 'wb+')               
                            destination.write(chunk)
                            destination.close()

                        #create the corresponding thumbnail (force .jpg)
                        if not thumbnail_created:
                            thumbnail_created = True
                            basewidth = 400
                            img = Image.open(dirname + filename)
                            wpercent = (basewidth/float(img.size[0]))
                            hsize = int((float(img.size[1])*float(wpercent)))
                            img1 = img.resize((basewidth,hsize), PIL.Image.ANTIALIAS)
                            img1.save(settings.MEDIA_ROOT + '/thumbnails/experiences/experience' + str(experience.id) + '_1.jpg')

                        if not len(experience.photo_set.filter(name__startswith=filename))>0:
                            photo = Photo(name = filename, directory = 'experiences/' + str(experience.id) + '/', 
                                          image = 'experiences/' + str(experience.id) + '/' + filename, experience = experience)
                            photo.save()

            #add whatsincluded
            if not id:
                food = WhatsIncluded(item='Food', included = (form.data['included_food']=='Yes'), details = form.data['included_food_detail'], experience = experience)
                ticket = WhatsIncluded(item='Ticket', included = (form.data['included_ticket']=='Yes'), details = form.data['included_ticket_detail'], experience = experience)
                transport = WhatsIncluded(item='Transport', included = (form.data['included_transport']=='Yes'), details = form.data['included_transport_detail'], experience = experience)
                food.save()
                ticket.save()
                transport.save()
            else:
                wh = WhatsIncluded.objects.get(id=experience.whatsincluded_set.filter(item="Food")[0].id)
                wh.included = (form.data['included_food']=='Yes')
                wh.details = form.data['included_food_detail']
                wh.save()
                wh = WhatsIncluded.objects.get(id=experience.whatsincluded_set.filter(item="Ticket")[0].id)
                wh.included = (form.data['included_ticket']=='Yes')
                wh.details = form.data['included_ticket_detail']
                wh.save()
                wh = WhatsIncluded.objects.get(id=experience.whatsincluded_set.filter(item="Transport")[0].id)
                wh.included = (form.data['included_transport']=='Yes')
                wh.details = form.data['included_transport_detail']
                wh.save()

            return HttpResponseRedirect('/admin/experiences/experience') 
            
    else:
        form = CreateExperienceForm(data, files)

    return render_to_response('create_experience.html', {'form': form, 'display_error':display_error}, context)

def booking_accepted(request, id=None):
    #TODO
    # respond within 48 hours?

    accepted = request.GET.get('accept')

    if not request.user.is_authenticated():
        return HttpResponseRedirect("/accounts/login/?next=/booking/" + str(id) + "?accept="+accepted)

    form = SubscriptionForm()

    if id and accepted:
        booking = get_object_or_404(Booking, pk=id)
        if booking.status.lower() == "accepted":
            # the host already accepted the booking
            messages.add_message(request, messages.INFO, 'The booking request has already been accepted.')
            return HttpResponseRedirect('/')

        if booking.status.lower() == "rejected":
            # the host/guest already rejected/cancelled the booking
            messages.add_message(request, messages.INFO, 'The booking request has already been rejected.')
            return HttpResponseRedirect('/')

        experience = Experience.objects.get(id=booking.experience_id)
        if not experience.hosts.all()[0].id == request.user.id:
            return HttpResponseRedirect("/")

        guest = User.objects.get(id = booking.user_id)
        host = request.user

        if accepted == "yes":
            booking.status = "accepted"
            booking.save()
            if booking.coupon_id != None and booking.coupon.promo_code.startswith("once"):
                #the coupon can be used once, make it unavailable
                booking.coupon.end_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC)
                booking.coupon.save()

            #send an email to the traveller
            mail.send(subject='[Tripalocal] Booking confirmed', message='', 
                      sender='Tripalocal <' + Aliases.objects.filter(destination__contains=host.email)[0].mail + '>',
                      recipients = [Aliases.objects.filter(destination__contains=guest.email)[0].mail], 
                      priority='now',  #fail_silently=False, 
                      html_message=loader.render_to_string('email_booking_confirmed_traveler.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'user':guest, #not host --> need "my" phone number
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))

            #schedule an email to the traveller one day before the experience
            mail.send(subject='[Tripalocal] Booking reminder', message='', 
                      sender='Tripalocal <' + Aliases.objects.filter(destination__contains=host.email)[0].mail + '>',
                      recipients = [Aliases.objects.filter(destination__contains=guest.email)[0].mail], 
                      priority='high',  scheduled_time = booking.datetime - timedelta(days=1), 
                      html_message=loader.render_to_string('email_reminder_traveler.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'user':guest, #not host --> need "my" phone number
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))
            
            #schedule an email to the host one day before the experience
            mail.send(subject='[Tripalocal] Booking reminder', message='', 
                      sender='Tripalocal <' + Aliases.objects.filter(destination__contains=guest.email)[0].mail + '>',
                      recipients = [Aliases.objects.filter(destination__contains=host.email)[0].mail], 
                      priority='high',  scheduled_time = booking.datetime - timedelta(days=1),  
                      html_message=loader.render_to_string('email_reminder_host.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'user':guest,
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))
                  
            #schedule an email for reviewing the experience
            mail.send(subject='[Tripalocal] How was your experience?', message='', 
                      sender='Tripalocal <enquiries@tripalocal.com>',
                      recipients = [Aliases.objects.filter(destination__contains=guest.email)[0].mail], 
                      priority='high',  scheduled_time = booking.datetime + timedelta(hours=experience.duration+1), 
                      html_message=loader.render_to_string('email_review_traveler.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                            'review_url':settings.DOMAIN_NAME + '/reviewexperience/' + str(experience.id)}))

            #send an email to the host
            mail.send(subject='[Tripalocal] Booking confirmed', message='', 
                      sender='Tripalocal <' + Aliases.objects.filter(destination__contains=guest.email)[0].mail + '>',
                      recipients = [Aliases.objects.filter(destination__contains=host.email)[0].mail], 
                      priority='now',  #fail_silently=False, 
                      html_message=loader.render_to_string('email_booking_confirmed_host.html',
                                                            {'experience': experience,
                                                            'booking':booking,
                                                            'user':guest,
                                                            'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))
            return render(request, 'email_booking_confirmed_host.html',
                          {'experience': experience,
                            'booking':booking,
                            'user':guest,
                            'experience_url':'http://' + settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                            'webpage':True})
        
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
                refund_amount = round(subtotal_price*(1+settings.COMMISSION_PERCENT),2)

                if extra_fee <= -1:
                    refund_amount = round((subtotal_price+extra_fee)*(1+settings.COMMISSION_PERCENT), 2)
                if extra_fee < 0 and extra_fee > -1:
                    refund_amount = round((subtotal_price*(1+extra_fee))*(1+settings.COMMISSION_PERCENT), 2)

                success, response = payment.refund(charge_id=payment.charge_id, amount=int(refund_amount*100))
            else:
                success = True

            if success:
                booking.status = "rejected"
                booking.save()
                #send an email to the traveller
                mail.send(subject='[Tripalocal] Your experience is cancelled', message='', 
                          sender='Tripalocal <' + Aliases.objects.filter(destination__contains=host.email)[0].mail + '>',
                          recipients = [Aliases.objects.filter(destination__contains=guest.email)[0].mail],
                          priority='now',  #fail_silently=False, 
                          html_message=loader.render_to_string('email_booking_cancelled_traveler.html',
                                                                {'experience': experience,
                                                                'booking':booking,
                                                                'user':host,
                                                                'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))
                #send an email to the host
                mail.send(subject='[Tripalocal] Cancellation confirmed', message='', 
                          sender='Tripalocal <' + Aliases.objects.filter(destination__contains=guest.email)[0].mail + '>',
                          recipients = [Aliases.objects.filter(destination__contains=host.email)[0].mail], 
                          priority='now',  #fail_silently=False, 
                          html_message=loader.render_to_string('email_booking_cancelled_host.html',
                                                                {'experience': experience,
                                                                 'booking':booking,
                                                                 'user':guest,
                                                                 'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))
                return render(request, 'email_booking_cancelled_host.html',
                               {'experience': experience,
                                'booking':booking,
                                'user':guest,
                                'experience_url': 'http://' + settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                'webpage':True})
            #else:
                #TODO
                #ask the host to try again, or contact us
                messages.add_message(request, messages.INFO, 'Please try to cancel the request later. Contact us if this happens again. Sorry for the inconvenience.')
                return HttpResponseRedirect('/')

    #wrong format
    return HttpResponseRedirect('/') 

#def charge(request):
#    if request.method == "POST":
#        form = ExperiencePaymentForm(request.POST)
 
#        if form.is_valid(): # charges the card
#            return HttpResponseRedirect("/experience_booking_successful/")
#    else:
#        form = ExperiencePaymentForm()
 
#    return render_to_response("payment.html", RequestContext( request, {'form': form} ) )

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
        BGImageURL = 'thumbnails/experiences/'+ photoList[0].name
    return BGImageURL

def ByCityExperienceListView(request, city, start_date=datetime.utcnow().replace(tzinfo=pytz.UTC), end_date=datetime.max.replace(tzinfo=pytz.UTC)):
    template = loader.get_template('search_result.html')

    # Add all experiences that belong to the specified city to a new list
    # alongside a list with all the number of reviews
    experienceList = Experience.objects.filter(city__iexact=city, status__iexact="listed")
    rateList = []
    cityExperienceList = []
    cityExperienceReviewList = []
    formattedTitleList = []
    BGImageURLList = []
    profileImageURLList = []
    cityList= ['Melbourne','Sydney']

    i = 0
    while i < len(experienceList):
        experience = experienceList[i]
        if experience.start_datetime > end_date or experience.end_datetime < start_date :
            i += 1
            continue

        if (experience.city.lower() == city.lower()):
            rate = 0.0
            counter = 0
            for review in experience.review_set.all():
                rate += review.rate
                counter += 1
            
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
                    else:
                        counter += 1
                        if counter == len(rateList):
                            rateList.append(rate)

            cityExperienceList.insert(counter, experience)
            cityExperienceReviewList.insert(counter, getNReviews(experience.id))
            # Fetch BGImageURL
            BGImageURL = getBGImageURL(experience.id)
            if (BGImageURL):
                BGImageURLList.insert(counter, BGImageURL)
            else:
                BGImageURLList.insert(counter, "default_experience_background.jpg")
            # Fetch profileImageURL
            profileImageURL = RegisteredUser.objects.get(user_id=experience.hosts.all()[0].id).image_url
            if (profileImageURL):
                profileImageURLList.insert(counter, profileImageURL)
            else:
                profileImageURLList.insert(counter, "profile_default.jpg")
            # Format title & Description
            if (experience.title != None and len(experience.title) > 50):
                formattedTitleList.insert(counter, experience.title[:47] + "...")
            else:
                formattedTitleList.insert(counter, experience.title)
        i += 1

    mp = Mixpanel(settings.MIXPANEL_TOKEN)

    if request.user.is_authenticated():
        mp.track(request.user.email,"Viewed " + city.title() + " search page");
    else:
        mp.track("","Viewed " + city.title() + " search page");

    context = RequestContext(request, {
        'city' : city.title(),
        'cityExperienceList' : zip(cityExperienceList, cityExperienceReviewList, formattedTitleList, BGImageURLList, profileImageURLList),
        'cityList':cityList
        })
    return HttpResponse(template.render(context))

def experiences(request):
    mp = Mixpanel(settings.MIXPANEL_TOKEN)
    
    if request.user.is_authenticated():
        mp.track(request.user.email,"Visited prelaunch Melbourne experiences page");
        return render(request,'experiences.html',{"user_email":request.user.email})
    else:
        mp.track("","Visited prelaunch Melbourne experiences page");
        return render(request,'experiences.html',{"user_email":""})

def experiences_ch(request):
    return render(request,'experiences_ch.html')

def experiences_pre(request):
    return render(request,'experiences_pre.html')

def experiences_ch_pre(request):
    return render(request,'experiences_ch_pre.html')

def experiences_sydney_pre(request):
    return render(request,'experiences_sydney_pre.html')

def freeSimPromo(request):

    template = loader.get_template('christmas_2014_promo.html')

    # Add all experiences that belong to the specified city to a new list
    # alongside a list with all the number of reviews
    experienceList = Experience.objects.all()

    mcityExperienceList = []
    mcityExperienceReviewList = []
    mformattedTitleList = []
    mBGImageURLList = []
    mprofileImageURLList = []

    scityExperienceList = []
    scityExperienceReviewList = []
    sformattedTitleList = []
    sBGImageURLList = []
    sprofileImageURLList = []

    i = 0
    while i < len(experienceList):
        experience = experienceList[i]
        # Melbourne
        if (experience.city.lower() == "melbourne"):
            mcityExperienceList.append(experience)
            mcityExperienceReviewList.append(getNReviews(experience.id))
            # Fetch BGImageURL
            BGImageURL = getBGImageURL(experience.id)
            if (BGImageURL):
                mBGImageURLList.append(BGImageURL)
            else:
                mBGImageURLList.append("default_experience_background.jpg")
            # Fetch profileImageURL
            profileImageURL = RegisteredUser.objects.get(user_id=experience.hosts.all()[0].id).image_url
            if (profileImageURL):
                mprofileImageURLList.append(profileImageURL)
            else:
                mprofileImageURLList.append("profile_default.jpg")
            # Format title & Description
            if (len(experience.title) > 50):
                mformattedTitleList.append(experience.title[:47] + "...")
            else:
                mformattedTitleList.append(experience.title)

        # Sydney
        if (experience.city.lower() == "sydney"):
            scityExperienceList.append(experience)
            scityExperienceReviewList.append(getNReviews(experience.id))
            # Fetch BGImageURL
            BGImageURL = getBGImageURL(experience.id)
            if (BGImageURL):
                sBGImageURLList.append(BGImageURL)
            else:
                sBGImageURLList.append("default_experience_background.jpg")
            # Fetch profileImageURL
            profileImageURL = RegisteredUser.objects.get(user_id=experience.hosts.all()[0].id).image_url
            if (profileImageURL):
                sprofileImageURLList.append(profileImageURL)
            else:
                sprofileImageURLList.append("profile_default.jpg")
            # Format title & Description
            if (len(experience.title) > 50):
                sformattedTitleList.append(experience.title[:47] + "...")
            else:
                sformattedTitleList.append(experience.title)
        i += 1


    context = RequestContext(request, {

    'mcityExperienceList' : zip(mcityExperienceList, mcityExperienceReviewList, mformattedTitleList, mBGImageURLList, mprofileImageURLList),
    'scityExperienceList' : zip(scityExperienceList, scityExperienceReviewList, sformattedTitleList, sBGImageURLList, sprofileImageURLList),

    })
    return HttpResponse(template.render(context))

def userHasLeftReview (user, experience):
    hasLeftReview = False
    reviewsByUser = Review.objects.filter(user=user, experience=experience)
    if reviewsByUser:
        hasLeftReview = True
    return hasLeftReview

def review_experience (request, id=None):
    if id:
        if not request.user.is_authenticated():
            return HttpResponseRedirect("/accounts/login/?next=/reviewexperience/"+str(id))

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

                    #copy to the chinese db
                    cursor = connections['cndb'].cursor()
                    row = cursor.execute("insert into experiences_review (user_id, experience_id, comment, rate, personal_comment, operator_comment, datetime) values(%s,%s,%s,%s,%s,%s,%s)",
                                         [user.id,experience.id,review.comment,review.rate,review.personal_comment,review.operator_comment,review.datetime])

                    return render_to_response('review_experience_success.html', {}, context)
            else:
                form = ReviewForm()
        else:
            form = ReviewForm()

        return render_to_response('review_experience.html', {'form': form}, context)
    else:
        return HttpResponseRedirect('/')