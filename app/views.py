"""
Definition of views.
"""

from django.shortcuts import render, render_to_response
from django.http import HttpRequest, HttpResponseRedirect, HttpResponse
from django.template import RequestContext, loader
from datetime import *
from django import forms
from django.contrib.auth import authenticate, login
from allauth.account.signals import password_reset, user_signed_up, user_logged_in
from allauth.account.views import PasswordResetFromKeyDoneView 
from django.dispatch import receiver
from app.forms import SubscriptionForm, HomepageSearchForm, UserProfileForm, UserCalendarForm
from app.models import *
from django.core.mail import send_mail
from django.contrib import messages
import string, random, pytz, base64, subprocess, os, geoip2.database, PIL, requests
from mixpanel import Mixpanel
from Tripalocal_V1 import settings
from experiences.views import SearchView, saveProfileImage, getBGImageURL, getProfileImage
from allauth.account.signals import email_confirmed, password_changed
from experiences.models import Booking, Experience, Payment, get_experience_title, get_experience_meetup_spot
from experiences.forms import Currency, DollarSign, email_account_generator
from django.core.files.uploadedfile import SimpleUploadedFile, File
from django.db import connections
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from post_office import mail
from django.contrib.auth.models import User
from os import path
from PIL import Image
from tripalocal_messages.models import Aliases, Users

PROFILE_IMAGE_SIZE_LIMIT = 1048576

PRIVATE_IPS_PREFIX = ('10.', '172.', '192.', '127.')

GEO_POSTFIX = settings.GEO_POSTFIX

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

def home(request):
    """Renders the home page."""

    context = RequestContext(request)
    if request.method == 'POST':
        form = HomepageSearchForm(request.POST)
        if form.is_valid():
            if len(form.data['start_date']):
                if len(form.data['end_date']):
                    return SearchView(request, form.data['city'], 
                                             start_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['start_date'], "%Y-%m-%d")), 
                                             end_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['end_date'], "%Y-%m-%d")))
                else:
                    return SearchView(request, form.data['city'], 
                                             start_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['start_date'], "%Y-%m-%d")))    

            if len(form.data['end_date']):       
                return SearchView(request, form.data['city'], 
                                             end_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['end_date'], "%Y-%m-%d")))
            else:
                return SearchView(request, form.data['city'])

            #mp = Mixpanel(settings.MIXPANEL_TOKEN)
            #try: 
            #    Subscription.objects.get(email = form.data['email'])
            #    messages.add_message(request, messages.INFO, 'It seems you already subscribed. Thank you.')
            #except Subscription.DoesNotExist:
            #    ref = request.GET.get('ref')
            #    ref_link=id_generator(size=8)

            #    try:
            #        ref_by = Subscription.objects.get(ref_link = ref)
            #        new_sub = Subscription(email = form.data['email'], subscribed_datetime = datetime.utcnow().replace(tzinfo=pytz.utc), ref_by = ref_by.email, ref_link=ref_link)
            #        #send an email to the referal
            #        counter = len(Subscription.objects.filter(ref_by = ref_by.email))
                    
            #        if count <= 5:
            #            if counter%5 < 4: # i.e., (count+1)%5==0
            #                mp.track(ref_by.email, 'Referred a friend')
            #                mail.send('[Tripalocal] Someone has signed up because of you!', '', 'Tripalocal <enquiries@tripalocal.com>',
            #                            [ref_by.email], fail_silently=False, 
            #                            html_message=loader.render_to_string('app/email_new_referral.html', {'ref_url':'http://www.tripalocal.com?ref='+ref_by.ref_link, 'counter':counter%5+1, 'left':5-1-counter%5}))
            #            else:
            #                mp.track(ref_by.email, 'Qualified for a free experience')
            #                mail.send('[Tripalocal] Free experience!', '', 'Tripalocal <enquiries@tripalocal.com>',
            #                            [ref_by.email], fail_silently=False, 
            #                            html_message=loader.render_to_string('app/email_free_experience.html', {'ref_url':'http://www.tripalocal.com?ref='+ref_by.ref_link}))
            #    except Subscription.DoesNotExist:
            #        new_sub = Subscription(email = form.data['email'], subscribed_datetime = datetime.utcnow().replace(tzinfo=pytz.utc), ref_link=ref_link)
            #    finally:    
            #        new_sub.save()
            #        #send an email to the new subscriber
            #        #mp.people_set(form.data['email'], {"$email": form.data['email']})
            #        #mp.track(form.data['email'], 'Entered email address at prelaunch')
            #        data = "{'event': 'Opened welcome email','properties': {'token': '" + settings.MIXPANEL_TOKEN + "', 'distinct_id': '" + form.data['email'] + "'}}"
            #        mail.send('[Tripalocal] Welcome', '', 'Tripalocal <enquiries@tripalocal.com>',
            #                    [form.data['email']], fail_silently=False, 
            #                    html_message=loader.render_to_string('app/email_welcome.html', 
            #                                                         {'ref_url':'http://www.tripalocal.com?ref='+ref_link, 'data':base64.b64encode(data.encode('utf-8')).decode('utf-8')}))
            #        #messages.add_message(request, messages.INFO, 'Thank you for subscribing.')
            #        return render_to_response('app/welcome.html', {'ref_url':'http://www.tripalocal.com?ref='+ref_link}, context)
    else:
        form = HomepageSearchForm()

        #redirect according to ip
        remote_address = request.META.get('HTTP_X_FORWARDED_FOR')or request.META.get('REMOTE_ADDR')
        ip = remote_address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            proxies = x_forwarded_for.split(',')
            # remove the private ips from the beginning
            while (len(proxies) > 0 and proxies[0].startswith(PRIVATE_IPS_PREFIX)):
                proxies.pop(0)
                # take the first ip which is not a private one (of a proxy)
                if len(proxies) > 0:
                    ip = proxies[0]
        if not settings.DEVELOPMENT:
            if settings.LANGUAGES[0][0] != "zh":
                try:
                    reader = geoip2.database.Reader(path.join(settings.PROJECT_ROOT, 'GeoLite2-City.mmdb'))
                    response = reader.city(ip)
                    country = response.country.name
                    reader.close()
                    if country.lower() in ['china']:
                        return HttpResponseRedirect('/cn')
                except Exception:
                    reader.close()
    
                if request.LANGUAGE_CODE.startswith("zh"):
                    return HttpResponseRedirect('/cn')

    experienceList = Experience.objects.filter(id__in=[1,2,20])
    idxList = random.sample(range(len(experienceList)), 3)
    featuredExperienceList = [experienceList[i] for i in idxList]

    BGImages = [getBGImageURL(exp.id) for exp in featuredExperienceList]
    profileImages = [getProfileImage(exp) for exp in featuredExperienceList]

    featuredExperience = []
    for i in range(len(featuredExperienceList)):
        featuredExperienceList[i].dollarsign = DollarSign[featuredExperienceList[i].currency.upper()]
        featuredExperienceList[i].currency = str(dict(Currency)[featuredExperienceList[i].currency.upper()])
        featuredExperience.append({"experience":featuredExperienceList[i],"background":BGImages[i],"hostImage":profileImages[i]})

    featuredCityList = [('Melbourne', _('Melbourne')),('Sydney', _('Sydney')),('Goldcoast',_('Gold Coast')),('Cairns',_('Cairns')),('Adelaide',_('Adelaide'))]

    context = RequestContext(request, {
        'featuredExperience': featuredExperience,
        'cityList': featuredCityList
    })

    if request.user.is_authenticated():
        return render_to_response('app/index.html', {'form': form, 'user_email':request.user.email}, context)

    return render_to_response('app/index.html', {'form': form}, context)

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contactus.html',
        context_instance = RequestContext(request)
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/aboutus.html',
        context_instance = RequestContext(request)
    )

def termsofservice(request):
    return render(
        request,
        'app/termsofservice.html',
        context_instance = RequestContext(request)
    )

def privacypolicy(request):
    return render(
        request,
        'app/privacypolicy.html',
        context_instance = RequestContext(request)
    )

def refundpolicy(request):
    return render(
        request,
        'app/refundpolicy.html',
        context_instance = RequestContext(request)
    )

def signup(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            new_user = authenticate(username=request.POST['username'],
                                    password=request.POST['password1'])
            login(request, new_user)
            return HttpResponseRedirect(GEO_POSTFIX)
    else:
        form = UserCreateForm()
    return render(request, "app/signup.html", {
        'form': form,
    })

def registration_successful(request):

    if request.user.is_authenticated():
        return render(
            request,
            'app/registration_successful.html',
            context_instance = RequestContext(request, {})
        )
    else:
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/")

@receiver(email_confirmed)
def email_confirmed(request, **kwargs):
    useremail = None

    if hasattr(request.user, 'email'):
        useremail = request.user.email
    elif 'email_address' in kwargs and hasattr(kwargs['email_address'], 'email'):
        useremail = kwargs['email_address'].email

    if useremail:
        #send an email
        mail.send(subject=_('[Tripalocal] Successfully registered'), message='', sender=settings.DEFAULT_FROM_EMAIL,
                  recipients = [useremail], priority='now', html_message=loader.render_to_string('app/email_registration_successful.html'))

@receiver(password_reset)
def password_reset(request, user, **kwargs):
    PasswordResetFromKeyDoneView.user_reset = user
    PasswordResetFromKeyDoneView.reset_datetime = datetime.utcnow()

def current_datetime(request):
    import datetime
    return {'current_datetime':datetime.datetime.utcnow()}

def disclaimer(request):
    
    return render(
        request,
        'app/disclaimer.html',
        context_instance = RequestContext(request)
    )

def mylisting(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/?next=" + GEO_POSTFIX + "mylisting")

    experiences = []
    context = RequestContext(request)
    exps = Experience.objects.raw('select id from experiences_experience where id in (select experience_id from experiences_experience_hosts where user_id= %s) order by start_datetime', [request.user.id])

    for experience in exps:
        experience.title = get_experience_title(experience, settings.LANGUAGES[0][0])
        experiences.append(experience)

    context['experiences'] = experiences

    return render_to_response('app/mylisting.html', {}, context)

def getreservation(user):
    bookings = Booking.objects.raw('select id from experiences_booking where experience_id in (select experience_id from experiences_experience_hosts where user_id= %s) order by datetime', [user.id])

    current_reservations = []
    past_reservations = []
    local_timezone = pytz.timezone(settings.TIME_ZONE)

    for booking in bookings:
        experience = Experience.objects.get(id=booking.experience_id)
        payment = Payment.objects.get(id=booking.payment_id) if booking.payment_id != None else Payment()
        guest = User.objects.get(id=booking.user_id)
        phone_number = payment.phone_number if payment.phone_number != None and len(payment.phone_number) else guest.registereduser.phone_number
        reservation = {"booking_datetime":booking.datetime.astimezone(local_timezone), "booking_status":booking.status,
                       "booking_guest_number":booking.guest_number,"booking_id":booking.id,
                       "experience_id":experience.id,"experience_title":get_experience_title(experience, settings.LANGUAGES[0][0]), 
                       "payment_city":payment.city, "payment_country":payment.country,
                       "guest_first_name":guest.first_name, "guest_last_name":guest.last_name, "guest_phone_number":phone_number}

        if datetime.utcnow().replace(tzinfo=pytz.utc) > booking.datetime + timedelta(hours=48):
            past_reservations.append(reservation)
        else:
            current_reservations.append(reservation)

    return {'past_reservations':past_reservations, 'current_reservations':current_reservations}

def myreservation(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/?next=" + GEO_POSTFIX + "myreservation")

    context = RequestContext(request)

    reservations = getreservation(request.user)

    context['current_reservations'] = reservations['current_reservations']
    context['past_reservations'] = reservations['past_reservations']

    return render_to_response('app/myreservation.html', {}, context)

def mytrip(request):
    if request.user.is_authenticated():
        template = loader.get_template('app/mytrip.html')

        user_id = request.user.id

        # Retrieve all bookings the user has made
        user_bookings = []
        bookings = Booking.objects.filter(user=user_id)

        for booking in bookings:
            booking.experience.title = get_experience_title(booking.experience, settings.LANGUAGES[0][0])
            booking.experience.meetup_spot = get_experience_meetup_spot(booking.experience, settings.LANGUAGES[0][0])
            user_bookings.append(booking)

        # Sort user_bookings with their dates
        user_bookings = sorted(user_bookings, key=lambda booking: booking.datetime, reverse=True)

        # Convert timezones
        local_timezone = pytz.timezone(settings.TIME_ZONE)

        # Place bookings into a list of lists where each index is a date
        bookings_all = []
        end_dates = []

        currentDate = 0
        for booking in user_bookings:
            placedIn = False

            # convert timezone
            booking_time_local = booking.datetime.astimezone(local_timezone)
            booking.datetime = booking_time_local

            #Fetch end_date
            end_date = booking.datetime + timedelta(hours=booking.experience.duration)

            for existing_booking in bookings_all:
                # Find a better method of comparing two dates for the same day
                if (existing_booking[0].datetime.year == booking.datetime.year and existing_booking[0].datetime.month == booking.datetime.month and existing_booking[0].datetime.day == booking.datetime.day):
                    existing_booking.append(booking)

                    if len(end_dates) <= currentDate:
                        end_dates.append([])

                    end_dates[currentDate].append(end_date)
                    placedIn = True

            if (placedIn == False):
                bookings_all.append([booking])
                end_dates.append([end_date])
            currentDate += 1

        context = RequestContext(request, {
            'bookings_all' : bookings_all,
            'end_dates' : end_dates,
            })
        return HttpResponse(template.render(context))

    else:
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/?next=" + GEO_POSTFIX + "mytrip")

def myprofile(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/?next=" + GEO_POSTFIX + "myprofile")

    context = RequestContext(request)
    profile = RegisteredUser.objects.get(user_id = request.user.id)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile.phone_number = form.cleaned_data['phone_number']
            profile.save()
            save_user_bio(profile, form.cleaned_data['bio'], settings.LANGUAGES[0][0])

            #save the profile image
            if 'image' in request.FILES:
                saveProfileImage(request.user, profile, request.FILES['image'])

    #display the original/updated data
    data={"first_name":request.user.first_name, "last_name":request.user.last_name, "email":request.user.email}
    photo={}
    if profile.image_url:
        context["image_url"] = profile.image_url
        #photo["image"] = SimpleUploadedFile(settings.MEDIA_ROOT+'/'+profile.image_url, 
        #                                    File(open(settings.MEDIA_ROOT+'/'+profile.image_url, 'rb')).read())
    else:
        context["image_url"] = "hosts/no_img.jpg"

    if profile.phone_number:
        data["phone_number"]=profile.phone_number

    data["bio"]=get_user_bio(profile, settings.LANGUAGES[0][0])
        
    form = UserProfileForm(data=data)

    return render_to_response('app/myprofile.html', {'form': form}, context)

def mycalendar(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/?next=" + GEO_POSTFIX + "mycalendar")

    context = RequestContext(request)

    if request.method == 'POST':
        form = UserCalendarForm(request.POST)

        if form.is_valid():
            blockout = {}
            instant_booking = {}
            for i in range(1,6):
                blockout['blockout_start_datetime_'+str(i)] = form.cleaned_data['blockout_start_datetime_'+str(i)] if 'blockout_start_datetime_'+str(i) in form.cleaned_data else None
                blockout['blockout_end_datetime_'+str(i)] = form.cleaned_data['blockout_end_datetime_'+str(i)] if 'blockout_end_datetime_'+str(i) in form.cleaned_data else None
                blockout['blockout_repeat_'+str(i)] = form.cleaned_data['blockout_repeat_'+str(i)] if 'blockout_repeat_'+str(i) in form.cleaned_data else None
                blockout['blockout_repeat_cycle_'+str(i)] = form.cleaned_data['blockout_repeat_cycle_'+str(i)] if 'blockout_repeat_cycle_'+str(i) in form.cleaned_data else None
                blockout['blockout_repeat_frequency_'+str(i)] = form.cleaned_data['blockout_repeat_frequency_'+str(i)] if 'blockout_repeat_frequency_'+str(i) in form.cleaned_data else None
                blockout['blockout_repeat_extra_information_'+str(i)] = form.cleaned_data['blockout_repeat_extra_information_'+str(i)] if 'blockout_repeat_extra_information_'+str(i) in form.cleaned_data else None
                blockout['blockout_repeat_end_date_'+str(i)] = form.cleaned_data['blockout_repeat_end_date_'+str(i)] if 'blockout_repeat_end_date_'+str(i) in form.cleaned_data else None
                instant_booking['instant_booking_start_datetime_'+str(i)] = form.cleaned_data['instant_booking_start_datetime_'+str(i)] if 'instant_booking_start_datetime_'+str(i) in form.cleaned_data else None
                instant_booking['instant_booking_end_datetime_'+str(i)] = form.cleaned_data['instant_booking_end_datetime_'+str(i)] if 'instant_booking_end_datetime_'+str(i) in form.cleaned_data else None
                instant_booking['instant_booking_repeat_'+str(i)] = form.cleaned_data['instant_booking_repeat_'+str(i)] if 'instant_booking_repeat_'+str(i) in form.cleaned_data else None
                instant_booking['instant_booking_repeat_cycle_'+str(i)] = form.cleaned_data['instant_booking_repeat_cycle_'+str(i)] if 'instant_booking_repeat_cycle_'+str(i) in form.cleaned_data else None
                instant_booking['instant_booking_repeat_frequency_'+str(i)] = form.cleaned_data['instant_booking_repeat_frequency_'+str(i)] if 'instant_booking_repeat_frequency_'+str(i) in form.cleaned_data else None
                instant_booking['instant_booking_repeat_extra_information_'+str(i)] = form.cleaned_data['instant_booking_repeat_extra_information_'+str(i)] if 'instant_booking_repeat_extra_information_'+str(i) in form.cleaned_data else None
                instant_booking['instant_booking_repeat_end_date_'+str(i)] = form.cleaned_data['instant_booking_repeat_end_date_'+str(i)] if 'instant_booking_repeat_end_date_'+str(i) in form.cleaned_data else None

            #delete old records of blockout periods, instant booking periods
            obls = BlockOutTimePeriod.objects.filter(user_id = request.user.id)
            for obl in obls:
                obl.delete()
            oibs = InstantBookingTimePeriod.objects.filter(user_id = request.user.id)
            for oib in oibs:
                oib.delete()

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
                                                user = request.user
                                                )
                    else:
                        b = BlockOutTimePeriod(start_datetime = blockout['blockout_start_datetime_'+str(i)].astimezone(pytz.timezone('UTC')).replace(minute=0), 
                                                end_datetime = blockout['blockout_end_datetime_'+str(i)].astimezone(pytz.timezone('UTC')).replace(minute=0),
                                                repeat = blockout['blockout_repeat_'+str(i)], 
                                                repeat_cycle = blockout['blockout_repeat_cycle_'+str(i)], 
                                                repeat_frequency = blockout['blockout_repeat_frequency_'+str(i)],
                                                repeat_extra_information = blockout['blockout_repeat_extra_information_'+str(i)],
                                                repeat_end_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime("2049-12-31", "%Y-%m-%d")).astimezone(pytz.timezone('UTC')),
                                                user = request.user
                                                )
                    b.save()
                
                if instant_booking['instant_booking_start_datetime_'+str(i)] and instant_booking['instant_booking_end_datetime_'+str(i)]:
                    if instant_booking['instant_booking_repeat_end_date_'+str(i)]:
                        ib = InstantBookingTimePeriod(start_datetime = instant_booking['instant_booking_start_datetime_'+str(i)].astimezone(pytz.timezone('UTC')).replace(minute=0), 
                                                end_datetime = instant_booking['instant_booking_end_datetime_'+str(i)].astimezone(pytz.timezone('UTC')).replace(minute=0),
                                                repeat = instant_booking['instant_booking_repeat_'+str(i)], 
                                                repeat_cycle = instant_booking['instant_booking_repeat_cycle_'+str(i)], 
                                                repeat_frequency = instant_booking['instant_booking_repeat_frequency_'+str(i)],
                                                repeat_extra_information = instant_booking['instant_booking_repeat_extra_information_'+str(i)],
                                                repeat_end_date = instant_booking['instant_booking_repeat_end_date_'+str(i)],
                                                user = request.user
                                                )
                    else:
                        ib = InstantBookingTimePeriod(start_datetime = instant_booking['instant_booking_start_datetime_'+str(i)].astimezone(pytz.timezone('UTC')).replace(minute=0), 
                                                end_datetime = instant_booking['instant_booking_end_datetime_'+str(i)].astimezone(pytz.timezone('UTC')).replace(minute=0),
                                                repeat = instant_booking['instant_booking_repeat_'+str(i)], 
                                                repeat_cycle = instant_booking['instant_booking_repeat_cycle_'+str(i)], 
                                                repeat_frequency = instant_booking['instant_booking_repeat_frequency_'+str(i)],
                                                repeat_extra_information = instant_booking['instant_booking_repeat_extra_information_'+str(i)],
                                                repeat_end_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime("2049-12-31", "%Y-%m-%d")).astimezone(pytz.timezone('UTC')),
                                                user = request.user
                                                )
                    ib.save()
            return render_to_response('app/mycalendar.html', {'form': form, 'updated':True}, context)
        else:
            return render_to_response('app/mycalendar.html', {'form': form, 'error':True}, context)
    else:
        data={}
        blockouts = BlockOutTimePeriod.objects.filter(user_id = request.user.id)
        for index in range(len(blockouts)):
            data['blockout_start_datetime_'+str(index+1)] = blockouts[index].start_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
            data['blockout_end_datetime_'+str(index+1)] = blockouts[index].end_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
            data['blockout_repeat_'+str(index+1)] = blockouts[index].repeat
            data['blockout_repeat_cycle_'+str(index+1)] = blockouts[index].repeat_cycle
            data['blockout_repeat_frequency_'+str(index+1)] = blockouts[index].repeat_frequency
            data['blockout_repeat_end_date_'+str(index+1)] = blockouts[index].repeat_end_date
            data['blockout_repeat_extra_information_'+str(index+1)] = blockouts[index].repeat_extra_information

        instant_bookings = InstantBookingTimePeriod.objects.filter(user_id = request.user.id)
        for index in range(len(instant_bookings)):
            data['instant_booking_start_datetime_'+str(index+1)] = instant_bookings[index].start_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
            data['instant_booking_end_datetime_'+str(index+1)] = instant_bookings[index].end_datetime.astimezone(pytz.timezone(settings.TIME_ZONE))
            data['instant_booking_repeat_'+str(index+1)] = instant_bookings[index].repeat
            data['instant_booking_repeat_cycle_'+str(index+1)] = instant_bookings[index].repeat_cycle
            data['instant_booking_repeat_frequency_'+str(index+1)] = instant_bookings[index].repeat_frequency
            data['instant_booking_repeat_end_date_'+str(index+1)] = instant_bookings[index].repeat_end_date
            data['instant_booking_repeat_extra_information_'+str(index+1)] = instant_bookings[index].repeat_extra_information

        form = UserCalendarForm(data=data)

        return render_to_response('app/mycalendar.html', {'form': form}, context)

@receiver(password_changed)
def password_change_callback(sender, request, user, **kwargs):
    messages.success(request, str(user.id) + '_PasswordChanged')

@receiver(user_signed_up)
def handle_user_signed_up(request, user, sociallogin=None, **kwargs):
    try:
        new_registereduser = RegisteredUser.objects.get(user_id = user.id)
    except RegisteredUser.DoesNotExist:
        new_registereduser = RegisteredUser(user_id = user.id)
        if 'phone_number' in kwargs:
            new_registereduser.phone_number = kwargs['phone_number']
        new_registereduser.save()

    username = user.username

    new_email = Users(id = email_account_generator() + ".user@tripalocal.com",
                        name = username,
                        maildir = username + "/")
    new_email.save()

    new_alias = Aliases(mail = new_email.id, destination = user.email + ", " + new_email.id)
    new_alias.save()

    if not settings.DEVELOPMENT:
        if len(settings.ADMINS) == 0:
            with open('/etc/postfix/canonical', 'a') as f:
                f.write(user.email + " " + new_email.id + "\n")
                f.close()

            subprocess.Popen(['sudo','postmap','/etc/postfix/canonical'])
    
            with open('/etc/postgrey/whitelist_recipients.local', 'a') as f:
                f.write(new_email.id + "\n")
                f.close()
        else:
            try:
                response = requests.post('https://www.tripalocal.com/update_files/',
                                         data={'user_email': user.email,'tripalocal_email':new_email.id},
                                         auth=(settings.ADMINS[0][1], settings.ADMIN_PASSWORD[0]),
                                         timeout=3)
            except requests.exceptions.RequestException as err:
                #TODO
                pass

    """get the client ip from the request
    """
    #remote_address = request.META.get('REMOTE_ADDR')
    remote_address = request.META.get('HTTP_X_FORWARDED_FOR')or request.META.get('REMOTE_ADDR')
    # set the default value of the ip to be the REMOTE_ADDR if available
    # else None
    ip = remote_address
    # try to get the first non-proxy ip (not a private ip) from the
    # HTTP_X_FORWARDED_FOR
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        proxies = x_forwarded_for.split(',')
        # remove the private ips from the beginning
        while (len(proxies) > 0 and proxies[0].startswith(PRIVATE_IPS_PREFIX)):
            proxies.pop(0)
            # take the first ip which is not a private one (of a proxy)
            if len(proxies) > 0:
                ip = proxies[0]

    if not settings.DEVELOPMENT:
        track_user_signup(ip, sociallogin, user)

def track_user_signup(ip, sociallogin, user):
    mp = Mixpanel(settings.MIXPANEL_TOKEN)
    mp.people_set(user.email, {"IP":ip, 
                               "$created":pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone(settings.TIME_ZONE)).strftime("%Y-%m-%dT%H:%M:%S")
                               })

    reader = None
    try:
        reader = geoip2.database.Reader(path.join(settings.PROJECT_ROOT, 'GeoLite2-City.mmdb'))
        response = reader.city(ip)
        country = response.country.name
        region = response.subdivisions.most_specific.name
        postcode = response.postal.code
        city = response.city.name
        longitude = response.location.longitude
        latitude = response.location.latitude

        mp.track(user.email, "has signed up via email_"+settings.LANGUAGES[0][0])
        mp.people_set(user.email, {'$email':user.email, "$country":country, "$city":city, "$region":region, "$first_name":user.first_name, "$last_name":user.last_name, "Postcode":postcode, "Latitude":latitude, "Longitude":longitude})
        reader.close()
    except Exception:
        mp.track(user.email, "has signed up via email_"+settings.LANGUAGES[0][0])
    finally:
        if reader is not None:
            reader.close()

    if sociallogin:
        data = sociallogin.account.extra_data
        first_name=""
        last_name=""
        age=0
        gender=""
        email = user.email

        if 'first_name' in data:
            first_name = data['first_name']
        if 'last_name' in data:
            last_name = data['last_name']
        if 'age' in data:
            age = data['age']
        if 'gender' in data:
            gender = data['gender']

        mp = Mixpanel(settings.MIXPANEL_TOKEN)
        mp.track(email, 'has signed up via Facebook',{'$email':email,'$name':first_name + " " + last_name, 'age':age, 'gender':gender})
        mp.people_set(email, {'$email':email,'$name':first_name + " " + last_name, 'age':age, 'gender':gender})

@receiver(user_logged_in)
def handle_user_logged_in(request, user, sociallogin=None, **kwargs):
    remote_address = request.META.get('HTTP_X_FORWARDED_FOR')or request.META.get('REMOTE_ADDR')
    # set the default value of the ip to be the REMOTE_ADDR if available
    # else None
    ip = remote_address
    # try to get the first non-proxy ip (not a private ip) from the
    # HTTP_X_FORWARDED_FOR
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        proxies = x_forwarded_for.split(',')
        # remove the private ips from the beginning
        while (len(proxies) > 0 and proxies[0].startswith(PRIVATE_IPS_PREFIX)):
            proxies.pop(0)
            # take the first ip which is not a private one (of a proxy)
            if len(proxies) > 0:
                ip = proxies[0]

    if not settings.DEVELOPMENT:
        track_user_login(ip, sociallogin, user)

def track_user_login(ip, sociallogin, user):
    mp = Mixpanel(settings.MIXPANEL_TOKEN)
    mp.people_set(user.email, {"IP":ip})

    try:
        reader = geoip2.database.Reader(path.join(settings.PROJECT_ROOT, 'GeoLite2-City.mmdb'))
        response = reader.city(ip)
        country = response.country.name
        region = response.subdivisions.most_specific.name
        postcode = response.postal.code
        city = response.city.name
        longitude = response.location.longitude
        latitude = response.location.latitude

        mp.track(user.email, "has signed in via email_"+settings.LANGUAGES[0][0])
        mp.people_set(user.email, {'$email':user.email, "$country":country, "$city":city, "$region":region, "Postcode":postcode, 
                                   "Latitude":latitude, "Longitude":longitude, "Language":settings.LANGUAGES[0][1]}) #"$last_seen": datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(settings.TIME_ZONE))
        reader.close()
    except Exception:
        mp.track(user.email, "has signed in via email_"+settings.LANGUAGES[0][0])
    finally:
        if reader is not None:
            reader.close()

    if sociallogin:
        data = sociallogin.account.extra_data
        first_name=""
        last_name=""
        age=0
        gender=""
        email = user.email

        if 'first_name' in data:
            first_name = data['first_name']
        if 'last_name' in data:
            last_name = data['last_name']
        if 'age' in data:
            age = data['age']
        if 'gender' in data:
            gender = data['gender']

        mp = Mixpanel(settings.MIXPANEL_TOKEN)
        mp.track(email, 'has signed in via Facebook',{'$email':email,'$name':first_name + " " + last_name, 'age':age, 'gender':gender})
        mp.people_set(email, {'$email':email,'$name':first_name + " " + last_name, 'age':age, 'gender':gender})
