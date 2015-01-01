"""
Definition of views.
"""

from django.shortcuts import render, render_to_response
from django.http import HttpRequest, HttpResponseRedirect, HttpResponse
from django.template import RequestContext, loader
from datetime import *
from django import forms
from django.contrib.auth import authenticate, login
from app.forms import UserCreateForm
from allauth.account.signals import password_reset
from allauth.account.views import PasswordResetFromKeyDoneView 
from django.dispatch import receiver
from app.forms import SubscriptionForm, HomepageSearchForm, UserProfileForm
from app.models import Subscription, RegisteredUser
from django.core.mail import send_mail
from django.contrib import messages
import string, random, pytz, base64
from mixpanel import Mixpanel
from Tripalocal_V1 import settings
from experiences.views import ByCityExperienceListView
from allauth.account.signals import email_confirmed, password_changed
from experiences.models import Booking 
from django.core.files.uploadedfile import SimpleUploadedFile, File
import os
from django.dispatch import receiver

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
                    return ByCityExperienceListView(request, form.data['city'], 
                                             start_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['start_date'], "%Y-%m-%d")), 
                                             end_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['end_date'], "%Y-%m-%d")))
                else:
                    return ByCityExperienceListView(request, form.data['city'], 
                                             start_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['start_date'], "%Y-%m-%d")))    

            if len(form.data['end_date']):       
                return ByCityExperienceListView(request, form.data['city'], 
                                             end_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['end_date'], "%Y-%m-%d")))
            else:
                return ByCityExperienceListView(request, form.data['city'])

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
            #                send_mail('[Tripalocal] Someone has signed up because of you!', '', 'Tripalocal <enquiries@tripalocal.com>',
            #                            [ref_by.email], fail_silently=False, 
            #                            html_message=loader.render_to_string('app/email_new_referral.html', {'ref_url':'http://www.tripalocal.com?ref='+ref_by.ref_link, 'counter':counter%5+1, 'left':5-1-counter%5}))
            #            else:
            #                mp.track(ref_by.email, 'Qualified for a free experience')
            #                send_mail('[Tripalocal] Free experience!', '', 'Tripalocal <enquiries@tripalocal.com>',
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
            #        send_mail('[Tripalocal] Welcome', '', 'Tripalocal <enquiries@tripalocal.com>',
            #                    [form.data['email']], fail_silently=False, 
            #                    html_message=loader.render_to_string('app/email_welcome.html', 
            #                                                         {'ref_url':'http://www.tripalocal.com?ref='+ref_link, 'data':base64.b64encode(data.encode('utf-8')).decode('utf-8')}))
            #        #messages.add_message(request, messages.INFO, 'Thank you for subscribing.')
            #        return render_to_response('app/welcome.html', {'ref_url':'http://www.tripalocal.com?ref='+ref_link}, context)
    else:
        form = HomepageSearchForm()

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
            return HttpResponseRedirect("/")
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
        return HttpResponseRedirect("/accounts/login/")

@receiver(email_confirmed)
def email_confirmed(request, **kwargs):
    #send an email
    send_mail('[Tripalocal] Successfully registered', '', 'Tripalocal <enquiries@tripalocal.com>',
                [request.user.email], fail_silently=False, html_message=loader.render_to_string('app/email_registration_successful.html'))

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

def mytrips(request):
    if request.user.is_authenticated():
        template = loader.get_template('app/mytrips.html')

        user_id = request.user.id

        # Retrieve all bookings the user has made
        user_bookings = Booking.objects.filter(user=user_id)
    
        #filter out bookings with reviews given
        #index = 0
        #while index < len(user_bookings):
        #    experienceKey = user_bookings[index].experience
        #    if (hasReviewedExperience(user_id, experienceKey)):
        #        user_bookings.pop(index)
        #        i -= 1

        #    index += 1

        # Sort user_bookings with their dates
        user_bookings = sorted(user_bookings, key=lambda booking: booking.datetime, reverse=False)

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
            

        #print(bookings_all)
        #print(end_dates)
        context = RequestContext(request, {
            'bookings_all' : bookings_all,
            'end_dates' : end_dates,
            })
        return HttpResponse(template.render(context))

    else:
        return HttpResponseRedirect("/accounts/login/")

def myprofile(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/accounts/login/")

    context = RequestContext(request)
    profile = RegisteredUser.objects.get(user_id = request.user.id)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        profile.phone_number = form.data['phone_number']
        profile.bio = form.data['bio']

        #save the profile image
        if 'image' in request.FILES:
            dirname = settings.MEDIA_ROOT + '/hosts/' + str(request.user.id) + '/'
            if not os.path.isdir(dirname):
                os.mkdir(dirname)

            name, extension = os.path.splitext(request.FILES['image'].name)
            extension = extension.lower();
            if extension in ('.bmp', '.png', '.jpeg', '.jpg') :
                filename = 'host' + str(request.user.id) + '_1_' + request.user.first_name.title() + request.user.last_name[:1].title() + extension
                for chunk in request.FILES['image'].chunks():
                    destination = open(dirname + filename, 'wb+')               
                    destination.write(chunk)
                    destination.close()
                profile.image_url = "hosts/" + str(request.user.id) + '/host' + str(request.user.id) + '_1_' + request.user.first_name.title() + request.user.last_name[:1].title() + extension

        profile.save()

    #display the original/updated data
    data={"first_name":request.user.first_name, "last_name":request.user.last_name, "email":request.user.email}
    photo={}
    if profile.image_url:
        context["image_url"] = profile.image_url
        photo["image"] = SimpleUploadedFile(settings.MEDIA_ROOT+'/'+profile.image_url, 
                                            File(open(settings.MEDIA_ROOT+'/'+profile.image_url, 'rb')).read())
    else:
        context["image_url"] = "hosts/no_img.jpg"

    if profile.phone_number:
        data["phone_number"]=profile.phone_number
    if profile.bio:
        data["bio"]=profile.bio
        
    form = UserProfileForm(data=data, files=photo)

    return render_to_response('app/myprofile.html', {'form': form}, context)

@receiver(password_changed)
def password_change_callback(sender, request, user, **kwargs):
    messages.success(request, str(user.id) + '_PasswordChanged')