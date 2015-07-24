from experiences.models import Booking, Experience, Payment, WhatsIncluded, Coupon
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseForbidden
import json, pytz, xlrd, re, os, subprocess, math, logging, ast
from django.contrib.auth.models import User
from datetime import *
from app.models import RegisteredUser, Message
from post_office import mail
from Tripalocal_V1 import settings
from tripalocal_messages.models import Aliases, Users
from experiences.forms import email_account_generator, ExperienceForm, ItineraryBookingForm, check_coupon, Currency, DollarSign
from django.db import connections
from django.template import loader, RequestContext, Context
from django.template.loader import get_template
from app.forms import BookingRequestXLSForm, ExperienceTagsXLSForm
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from experiences.views import get_itinerary, update_booking, getAvailableOptions, experience_fee_calculator
from app.views import getreservation
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from allauth.account.utils import user_username, user_email, user_field
from allauth.account.signals import user_signed_up, user_logged_in
from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialLogin, SocialToken, SocialApp
from allauth.socialaccount.providers.facebook.views import fb_complete_login
from allauth.socialaccount.helpers import complete_social_login
from django.utils.translation import ugettext_lazy as _, string_concat
from django.views.decorators.csrf import csrf_exempt

GEO_POSTFIX = "/"
ENDB = 'default'
CNDB = 'cndb'

def isLegalInput(inputs):
    for input in inputs:
        if not re.match("^[\(\)\w\d\.\s:@_-]*$", input):
            return False

    return True

def updateExperienceTagsFromXLS(request):
    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/?next=" + GEO_POSTFIX + "experience_tags_xls")

    context = RequestContext(request)
    if request.method == 'POST':
        form = ExperienceTagsXLSForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['file']
                name, extension = os.path.splitext(file.name)
                extension = extension.lower();
                if extension in ('.xls', '.xlsx'):
                    destination = open(os.path.join(os.path.join(settings.PROJECT_ROOT,'xls'), file.name), 'wb+')
                    for chunk in file.chunks():             
                        destination.write(chunk)
                    destination.close()

                workbook = xlrd.open_workbook(os.path.join(os.path.join(settings.PROJECT_ROOT,'xls'), file.name))
            except OSError:
                #TODO
                raise

            worksheet = workbook.sheet_by_name('Sheet1')
            num_rows = worksheet.nrows - 1
            num_cells = worksheet.ncols - 1
            curr_row = 0
            all_tags = []

            curr_cell = -1
            while curr_cell < num_cells:
                curr_cell += 1
                # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
                cell_type = worksheet.cell_type(curr_row, curr_cell)
                cell_value = worksheet.cell_value(curr_row, curr_cell)
                if cell_type == 1 or cell_type == 0:
                    all_tags.append(cell_value)
                else:
                    raise Exception("Type error: column name, " + str(curr_cell))
            
            curr_row = 0
            while curr_row < num_rows:
                curr_row += 1
                row = worksheet.row(curr_row)

                curr_cell = 0
                exp_tags=""
                id = row[curr_cell].value.split("--")[0]
                id = int(id)
                try:
                    exp = Experience.objects.get(id=id)
                except Experience.DoesNotExist:
                    continue

                while curr_cell < num_cells:
                    curr_cell += 1
                    # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
                    cell_type = worksheet.cell_type(curr_row, curr_cell)

                    if cell_type == 1 or cell_type == 0:
                        if worksheet.cell_value(curr_row, curr_cell).lower() == "y":
                            exp_tags += all_tags[curr_cell] + ","
                    else:
                        raise Exception("Type error: row " + str(curr_row) + ", col " + str(curr_cell))

                exp.tags = exp_tags
                exp.save()
    else:
        form = ExperienceTagsXLSForm()

    return render_to_response('app/experience_tags_xls.html', {'form': form}, context)

def saveBookingRequest(booking_request):
    first_name = booking_request['first_name']
    last_name = booking_request['last_name']
    email = booking_request['email']
    city = booking_request['city']
    country = booking_request['country']
    phone = booking_request['phone']
    experience_id = booking_request['experience_id']
    guest_number = booking_request['guest_number']
    booking_datetime = booking_request['booking_datetime']
    booking_extra_information = booking_request['booking_extra_information']

    if not isLegalInput([first_name,last_name,email,city,country,phone,experience_id,guest_number,booking_datetime,booking_extra_information]):
        raise Exception("Illegal input")

    experience = Experience.objects.get(id=experience_id)

    #create a new account if the user does not exist
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        count = len(User.objects.filter(first_name__iexact=first_name))
        if count > 0 :
            user = User(first_name = first_name, last_name = last_name, email = email,
                        username = first_name+str(count+1),
                        date_joined = datetime.utcnow().replace(tzinfo=pytz.UTC),
                        last_login = datetime.utcnow().replace(tzinfo=pytz.UTC))
        else:
            user = User(first_name = first_name, last_name = last_name, email = email,
                        username = first_name,
                        date_joined = datetime.utcnow().replace(tzinfo=pytz.UTC),
                        last_login = datetime.utcnow().replace(tzinfo=pytz.UTC))
        user.save()
        password = User.objects.make_random_password()
        user.set_password(password)
        user.save()
        profile = RegisteredUser(user = user, phone_number = phone)
        profile.save()

        cursor = connections[ENDB].cursor()
        cursor.execute("Insert into account_emailaddress (user_id,email,verified,primary) values (%s, %s, %s, %s)", 
                       [user.id, email, 1, 1])

        #copy to the chinese website database
        cursor = connections[CNDB].cursor()
        cursor.execute("Insert into auth_user (id,first_name,last_name,email) values (%s, %s, %s, %s)", 
                        [user.id,user.first_name, user.last_name, user.email])
        cursor.execute("Insert into app_registereduser (user_id) values (%s)", [user.id])

        username = user.username

        new_email = Users(id = email_account_generator() + ".user@tripalocal.com",
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
                    
        #send a welcome email
        mail.send(subject=_('[Tripalocal] Successfully registered'), message='', sender=settings.DEFAULT_FROM_EMAIL,
                      recipients = [email], priority='now', html_message=loader.render_to_string('app/email_auto_registration.html',
                                                                                                 {'email':user.email, 'password':password, 'url':'https://www.tripalocal.com' + GEO_POSTFIX + 'accounts/login?next=' + GEO_POSTFIX + 'accounts/password/change/'}))

    #record the booking request
    local_timezone = pytz.timezone(settings.TIME_ZONE)
    booking = Booking(user = user, experience = experience, guest_number = guest_number, 
                        datetime = local_timezone.localize(datetime.strptime(booking_datetime, '%Y-%m-%d %H:%M')).astimezone(pytz.timezone("UTC")),
                        submitted_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC), status="accepted", booking_extra_information=booking_extra_information)
    booking.save()

    payment = Payment(booking = booking, city = city, country = country, phone_number = phone)
    payment.save()

    booking.payment_id = payment.id
    booking.save()

    #add the user to the guest list
    if user not in experience.guests.all():
        #experience.guests.add(user)
        cursor = connections['experiencedb'].cursor()
        cursor.execute("Insert into experiences_experience_guests (experience_id,user_id) values (%s, %s)", [experience_id, user.id])

    host = experience.hosts.all()[0]
    #send an email to the traveller
    mail.send(subject=_('[Tripalocal] Booking confirmed'), message='', 
                sender=string_concat(_('Tripalocal <'), Aliases.objects.filter(destination__contains=host.email)[0].mail, '>'),
                recipients = [Aliases.objects.filter(destination__contains=user.email)[0].mail], 
                priority='now',  #fail_silently=False, 
                html_message=loader.render_to_string('experiences/email_booking_confirmed_traveler.html',
                                                    {'experience': experience,
                                                    'booking':booking,
                                                    'user':user, #not host --> need "my" phone number
                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))
            
    #schedule an email for reviewing the experience
    mail.send(subject=_('[Tripalocal] How was your experience?'), message='', 
                sender=settings.DEFAULT_FROM_EMAIL,
                recipients = [Aliases.objects.filter(destination__contains=user.email)[0].mail], 
                priority='high',  scheduled_time = booking.datetime + timedelta(days=1), 
                html_message=loader.render_to_string('experiences/email_review_traveler.html',
                                                    {'experience': experience,
                                                    'booking':booking,
                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                    'review_url':settings.DOMAIN_NAME + '/reviewexperience/' + str(experience.id)}))

    #send an email to the host
    mail.send(subject=_('[Tripalocal] Booking confirmed'), message='', 
                sender=string_concat(_('Tripalocal <'), Aliases.objects.filter(destination__contains=user.email)[0].mail, '>'),
                recipients = [Aliases.objects.filter(destination__contains=host.email)[0].mail], 
                priority='now',  #fail_silently=False, 
                html_message=loader.render_to_string('experiences/email_booking_confirmed_host.html',
                                                    {'experience': experience,
                                                    'booking':booking,
                                                    'user':user, # guest here
                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))

    #schedule an email to the traveller one day before the experience
    mail.send(subject=_('[Tripalocal] Booking reminder'), message='', 
                sender=string_concat(_('Tripalocal <'), Aliases.objects.filter(destination__contains=host.email)[0].mail, '>'),
                recipients = [Aliases.objects.filter(destination__contains=user.email)[0].mail], 
                priority='high',  scheduled_time = booking.datetime - timedelta(days=1), 
                html_message=loader.render_to_string('experiences/email_reminder_traveler.html',
                                                    {'experience': experience,
                                                    'booking':booking,
                                                    'user':user, #not host --> need "my" phone number
                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))

    #schedule an email to the host one day before the experience
    mail.send(subject=_('[Tripalocal] Booking reminder'), message='', 
                sender=string_concat(_('Tripalocal <'), Aliases.objects.filter(destination__contains=user.email)[0].mail, '>'),
                recipients = [Aliases.objects.filter(destination__contains=host.email)[0].mail], 
                priority='high',  scheduled_time = booking.datetime - timedelta(days=1),  
                html_message=loader.render_to_string('experiences/email_reminder_host.html',
                                                    {'experience': experience,
                                                    'booking':booking,
                                                    'user':user,
                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))

def saveBookingRequestsFromXLS(request):
    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/?next=" + GEO_POSTFIX + "booking_request_xls")

    context = RequestContext(request)
    if request.method == 'POST':
        form = BookingRequestXLSForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['file']
                name, extension = os.path.splitext(file.name)
                extension = extension.lower();
                if extension in ('.xls', '.xlsx'):
                    destination = open(os.path.join(os.path.join(settings.PROJECT_ROOT,'xls'), file.name), 'wb+')
                    for chunk in file.chunks():             
                        destination.write(chunk)
                    destination.close()

                workbook = xlrd.open_workbook(os.path.join(os.path.join(settings.PROJECT_ROOT,'xls'), file.name))
            except OSError:
                #TODO
                raise

            worksheet = workbook.sheet_by_name('English')
            num_rows = worksheet.nrows - 1
            num_cells = worksheet.ncols - 1
            curr_row = 0
            col_names= []
            legal_names= ['first_name','last_name','email','city','country','phone','experience_id','guest_number','booking_datetime','booking_extra_information']

            curr_cell = -1
            while curr_cell < num_cells:
                curr_cell += 1
                # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
                cell_type = worksheet.cell_type(curr_row, curr_cell)
                cell_value = worksheet.cell_value(curr_row, curr_cell)
                if cell_type == 1 and cell_value in legal_names:
                    col_names.append(cell_value)
                else:
                    raise Exception("Type error: column name, " + str(curr_cell))

            while curr_row < num_rows:
                curr_row += 1
                row = worksheet.row(curr_row)

                curr_cell = -1
                booking_request={}
                while curr_cell < num_cells:
                    curr_cell += 1
                    # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
                    cell_type = worksheet.cell_type(curr_row, curr_cell)

                    if cell_type == 1 or cell_type == 0:
                        booking_request[col_names[curr_cell]] = worksheet.cell_value(curr_row, curr_cell)
                    else:
                        raise Exception("Type error: row " + str(curr_row) + ", col " + str(curr_cell))

                if booking_request:
                    saveBookingRequest(booking_request)
    else:
        form = BookingRequestXLSForm()

    return render_to_response('app/booking_request_xls.html', {'form': form}, context)

#request.data should contain a list of (first_name, last_name, email, country, destination phone number, experience_id, guest_number, booking_datetime, booking_extra_information)
#e.g.,  "[{\"first_name\": \"test\", \"last_name\": \"test\", \"email\":\"123@123.com\", \"city\":\"Beijing\", \"country\":\"China\", \"phone\":\"121221\", \"experience_id\": \"23\", \"guest_number\": \"2\", \"booking_datetime\":\"2015-01-05 00:00\", \"booking_extra_information\":\"Need Chinese translation\"}]"
@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,IsAdminUser))
def booking_request(request, format=None):
    try:
        # a list of requests
        #booking_requests = json.loads(request.data)
        #for booking_request in booking_requests:
        #    saveBookingRequest(booking_request)

        return Response("Booking request recorded", status=status.HTTP_201_CREATED)
    except TypeError as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

#https://djangosnippets.org/snippets/2172/
def ajax_view(request):
    template = "experiences/add_experience_experience.html"

    if request.is_ajax() and request.user.is_authenticated():
        if request.method == 'POST':
            request.POST['duration'] = request.POST['experience-duration']
            request.POST['location'] = request.POST['experience-location']
            request.POST['title'] = request.POST['experience-title']
            experience_form = ExperienceForm(request.POST)
            if experience_form.is_valid():
                #experience_form.save(commit=True)
                response={'status':True}
            else:
                response={'status':False}
            return HttpResponse(json.dumps(response, ensure_ascii=False))
        else:
            return render_to_response(template, {'form':ExperienceForm()}, context_instance=RequestContext(request))
    else:
        raise Http404

@api_view(['POST','GET'])
@authentication_classes((TokenAuthentication,))#, SessionAuthentication, BasicAuthentication))
def service_wishlist(request):
    if request.method == 'POST': #request.is_ajax() and 
        try:
            user_id = int(request.POST['user_id'])
            experience_id = int(request.POST['experience_id'])
            added = request.POST['added']

            user = User.objects.get(id=user_id)
            experience = Experience.objects.get(id=experience_id)
            if added == "False":
                try:
                    #user.registereduser.wishlist.add(experience)
                    cursor = connections[ENDB].cursor()
                    cursor.execute("select id from app_registereduser_wishlist where experience_id=%s and registereduser_id=%s", [experience.id, user.registereduser.id])
                    wl = cursor.fetchone()
                    if wl is not None and len(wl)>0:
                        response={'success':False, 'error':'already added'}
                        return HttpResponse(json.dumps(response),content_type="application/json")

                    cursor.execute("Insert into app_registereduser_wishlist (experience_id,registereduser_id) values (%s, %s)", [experience.id, user.registereduser.id])
                    
                    cursor = connections[CNDB].cursor()
                    cursor.execute("Select id from app_registereduser where user_id=%s",[user_id])
                    profile_id = cursor.fetchone()
                    cursor.execute("Insert into app_registereduser_wishlist (experience_id,registereduser_id) values (%s, %s)", [experience.id, profile_id[0]])
                    response={'success':True, 'added':True}
                except BaseException:
                    response={'success':False, 'error':'fail to add'}
                    return HttpResponse(json.dumps(response),content_type="application/json")
            else:
                try:
                    #user.registereduser.wishlist.remove(experience)
                    cursor = connections[ENDB].cursor()
                    cursor.execute("delete from app_registereduser_wishlist where experience_id=%s and registereduser_id=%s", [experience.id, user.registereduser.id])
                    
                    cursor = connections[CNDB].cursor()
                    cursor.execute("Select id from app_registereduser where user_id=%s",[user_id])
                    profile_id = cursor.fetchone()
                    cursor.execute("delete from app_registereduser_wishlist where experience_id=%s and registereduser_id=%s", [experience.id, profile_id[0]])
                    response={'success':True, 'removed':True}
                except BaseException:
                    response={'success':False, 'error':'fail to remove'}
                    return HttpResponse(json.dumps(response),content_type="application/json")

            return HttpResponse(json.dumps(response),content_type="application/json")
        except User.DoesNotExist:
            response={'success':False, 'error':'user does not exist'}
            return HttpResponse(json.dumps(response),content_type="application/json")
        except Experience.DoesNotExist:
            response={'success':False, 'error':'experience does not exist'}
            return HttpResponse(json.dumps(response),content_type="application/json")

    elif request.method == 'GET' and request.user.is_authenticated():
        try:
            user = request.user
            cursor = connections[ENDB].cursor()
            wl = cursor.execute("select experience_id from app_registereduser_wishlist where registereduser_id=%s", [user.registereduser.id])
            wl = cursor.fetchall()
            ids = []
            for id in wl:
                ids.append(id)

            response={'experience_ids':ids}
            return HttpResponse(json.dumps(response),content_type="application/json")

        except Exception as err:
            #TODO
            return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(status=status.HTTP_403_FORBIDDEN)

@api_view(['POST'])
@csrf_exempt
def service_login(request):
    try:
        data = request.data #request.query_params['data']

        if "email" not in data or "password" not in data:
            result = {"error":"Wrong username/password"} 
            return Response(result, status=status.HTTP_401_UNAUTHORIZED)

        email = data['email']
        password = data['password']
        username = User.objects.get(email=email).username

        user = authenticate(username=username, password=password)
        if user is not None: # and user.is_active:
            login(request, user)
            new_token = Token.objects.get_or_create(user=user)
            result = {'user_id':user.id, 'token':new_token[0].key}
            return Response(result, status=status.HTTP_200_OK)
        else:
            result = {"error":"Wrong username/password"}
            return Response(result, status=status.HTTP_404_NOT_FOUND)

    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@csrf_exempt
def service_signup(request):
    try:
        data = request.data #request.query_params['data']

        if "email" not in data or "password" not in data or "first_name" not in data or "last_name" not in data:
            result = {"error":"Incomplete information"} 
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        email = data['email']
        password = data['password']
        first_name = data['first_name']
        last_name = data['last_name']
        username = first_name.lower()

        u = User.objects.filter(first_name__iexact = username)
        counter = len(u) if u is not None else 0
        counter += 1
        username = username + str(counter) if counter > 1 else username 

        try:
            user = User.objects.get(email = email)
            return Response({"error":"email already registered"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            user = User(first_name = first_name, last_name = last_name, email = email,username = username,
                        date_joined = datetime.utcnow().replace(tzinfo=pytz.UTC),
                        last_login = datetime.utcnow().replace(tzinfo=pytz.UTC))
            user.save()

            user.set_password(password)
            user.save()

            if 'phone_number' in data:
                user_signed_up.send(sender=user.__class__, request=request, user=user, phone_number=data['phone_number'])
            else:
                user_signed_up.send(sender=user.__class__, request=request, user=user)
            user = authenticate(username=username, password=password)
            login(request, user)
            new_token = Token.objects.get_or_create(user=user)
            result = {'user_id':user.id, 'token':new_token[0].key}

            return Response(result, status=status.HTTP_200_OK)

    except Exception as err:
        #TODO
        logger = logging.getLogger("Tripalocal_V1")
        if hasattr(err, 'detail'):
            logger.error(err.detail)
        else:
            logger.error(err)
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))#, SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def service_logout(request):
    logout(request)
    return Response({"result":"Logged out"}, status=status.HTTP_200_OK)

# http://bytefilia.com/titanium-mobile-facebook-application-django-allauth-sign-sign/
# http://stackoverflow.com/questions/16381732/how-to-create-new-user-and-new-django-allauth-social-account-when-given-access-t
@api_view(['POST'])
@csrf_exempt
def service_facebook_login(request):
    data = request.data

    access_token = data.get('access_token', '')

    try:
        app = SocialApp.objects.get(provider="facebook")
        token = SocialToken(app=app, token=access_token)

        # check token against facebook 
        login = fb_complete_login(request, app, token) #updated
        login.token = token
        login.state = SocialLogin.state_from_request(request)

        # add or update the user into users table
        ret = complete_social_login(request._request, login)

        new_token = Token.objects.get_or_create(user=login.account.user)
        #if we get here we've succeeded
        return Response({'user_id': login.account.user.id, "token":new_token[0].key}, status = status.HTTP_200_OK) 
    except Exception as err:
        # FIXME: Catch only what is needed
        return Response({'reason': "Bad Access Token"}, status = status.HTTP_401_UNAUTHORIZED)

#{"start_datetime":"2015-05-05", "end_datetime":"2015-05-08", "city":"melbourne", "guest_number":"2", "keywords":"Sports,Arts,Food"}
@api_view(['POST'])
@csrf_exempt
def service_search(request, format=None):
    try:
        criteria = request.data #request.query_params['data']
        start_datetime = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(criteria['start_datetime'].strip(), "%Y-%m-%d"))
        end_datetime = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(criteria['end_datetime'].strip(), "%Y-%m-%d"))
        city = criteria['city']
        guest_number = criteria['guest_number']
        keywords = criteria['keywords']
        language = "Mandarin,English"

        guest_number = 5 #temp fix
        if int(guest_number) == 0:
            itinerary = get_itinerary(start_datetime, end_datetime, None, city, language, keywords)
        else:
            itinerary = get_itinerary(start_datetime, end_datetime, guest_number, city, language, keywords)

        return Response(itinerary, status=status.HTTP_200_OK)
    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))# SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def service_mytrip(request, format=None):
    try:
        user = request.user
        booking_status = "paid,accepted,rejected"
        b = Booking.objects.filter(user=user, status__in=booking_status.split(","))
        cursor = connections[CNDB].cursor()
        cursor.execute('select datetime, status, guest_number, experience_id from experiences_booking where user_id = %s and status in (%s) order by datetime',
                                [request.user.id, booking_status])
        rows = cursor.fetchall()

        bookings = []
        for booking in b:
            bookings.append(booking)

        if rows:
            for index in range(len(rows)):
                bk = Booking()
                bk.datetime = rows[index][0]
                bk.status = rows[index][1]
                bk.guest_number = rows[index][2]
                exp = Experience()
                cursor.execute('select meetup_spot, title from experiences_experience where id = %s',
                                [rows[index][3]])
                row = cursor.fetchone()
                exp.id = rows[index][3]
                exp.meetup_spot = row[0]
                exp.title = row[1]
                #row = cursor.execute('select first_name, last_name from auth_user where id in (select user_id from experiences_experience_hosts where experience_id = %s)',
                #             [rows[index][3]]).fetchone()
                #host = User()
                #host.first_name = row[0]
                #host.last_name = row[1]
                #exp.hosts.
                bk.experience = exp
                bookings.append(bk)

        bookings = sorted(bookings, key=lambda booking: booking.datetime, reverse=True)

        # Convert timezone
        local_timezone = pytz.timezone(settings.TIME_ZONE)

        bks = []
        for booking in bookings:
            payment = booking.payment if booking.payment_id != None else Payment()
            host = booking.experience.hosts.all()[0]
            phone_number = host.registereduser.phone_number
            
            bk = {'datetime':booking.datetime.astimezone(local_timezone).isoformat(), 'status':booking.status, 'guest_number':booking.guest_number, 
                  'experience_title':booking.experience.title, 'meetup_spot':booking.experience.meetup_spot, 'experience_id':booking.experience.id,
                  'host_id':host.id, 'host_name':host.first_name + ' ' + host.last_name[:1] + '.', 'host_phone_number':phone_number,'host_image':host.registereduser.image_url}

            bks.append(bk)

        return Response(bks, status=status.HTTP_200_OK)
    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))# SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def service_myreservation(request, format=None):
    try:
        user = request.user
        reservations = getreservation(user)
        for reservation in reservations['current_reservations']:
            reservation['booking_datetime'] = reservation['booking_datetime'].isoformat()

        for reservation in reservations['past_reservations']:
            reservation['booking_datetime'] = reservation['booking_datetime'].isoformat()

        return Response(reservations, status=status.HTTP_200_OK)
    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

#"{"id":58,"accept":"yes"}"
@api_view(['POST'])
@authentication_classes((TokenAuthentication,))# SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def service_acceptreservation(request, format=None):
    try:
        user = request.user
        data = request.data
        id = data['id']
        accepted = data['accept']

        result = update_booking(id, accepted, user)

        r={'success':result['booking_success']}

        return Response(r, status=status.HTTP_200_OK)
    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

#{"itinerary_string":[{"id":"20","date":"2015/06/17","time":"4:00 - 6:00","guest_number":2},{"id":"20","date":"2015/06/17","time":"17:00 - 20:00","guest_number":2}],"card_number":"4242424242424242","expiration_month":10,"expiration_year":2015,"cvv":123, "coupon":"abcdefgh"}
@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def service_booking(request, format=None):
    try:
        data = request.data
        if type(data) is str:
            data = ast.literal_eval(data)

        itinerary = data['itinerary_string']

        booking_data = {}
        booking_data['user'] = request.user

        booking_data['experience_id'] = []
        booking_data['date'] = []
        booking_data['time'] = []

        for item in itinerary:
            booking_data['experience_id'].append(str(item['id']))
            booking_data['date'].append(str(item['date']))
            booking_data['time'].append(str(item['time']))
            booking_data['guest_number'] = item['guest_number']

        booking_data["card_number"] = data["card_number"]
        booking_data["exp_month"] = data["expiration_month"]
        booking_data["exp_year"] = data["expiration_year"]
        booking_data["cvv"] = data["cvv"]

        coupon = data["coupon"]
        coupons = None
        if coupon is not None and len(coupon) > 0:
            bk_dt = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(booking_data['date'][0].strip() + " " + booking_data['time'][0].split(":")[0].strip(),"%Y/%m/%d %H"))
            coupons = Coupon.objects.filter(promo_code__iexact = coupon,
                                            end_datetime__gt = bk_dt,
                                            start_datetime__lt = bk_dt)
        
        if coupons is not None and len(coupons) > 0:
            ItineraryBookingForm.booking(ItineraryBookingForm(),booking_data['experience_id'],booking_data['date'],booking_data['time'],booking_data['user'],booking_data['guest_number'],
                                         booking_data['card_number'],booking_data['exp_month'],booking_data['exp_year'],booking_data['cvv'],coupon=coupons[0])
        else:
            ItineraryBookingForm.booking(ItineraryBookingForm(),booking_data['experience_id'],booking_data['date'],booking_data['time'],booking_data['user'],booking_data['guest_number'],
                                         booking_data['card_number'],booking_data['exp_month'],booking_data['exp_year'],booking_data['cvv'])

        result = {"success":"true"}
        return Response(result, status=status.HTTP_200_OK)

    except Exception as err:
        #TODO
        logger = logging.getLogger("Tripalocal_V1")
        if hasattr(err, 'detail'):
            logger.error(err.detail)
        else:
            logger.error(err)
        result = {"success":"false"}
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

#{"coupon":"aasfsaf","id":"20","date":"2015/06/17","time":"4:00 - 6:00","guest_number":2}
@api_view(['POST'])
@authentication_classes((TokenAuthentication,))#, SessionAuthentication, BasicAuthentication)) #
@permission_classes((IsAuthenticated,))
def service_couponverification(request, format=None):
    try:
        data = request.data
        if type(data) is str:
            data = ast.literal_eval(data)

        result={"valid":"no","new_price":-1}
        coupon = data["coupon"]
        if coupon is not None and len(coupon) > 0:
            bk_dt = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(data['date'].strip() + " " + data['time'].split(":")[0].strip(),"%Y/%m/%d %H"))
            coupons = Coupon.objects.filter(promo_code__iexact = coupon,
                                            end_datetime__gt = bk_dt,
                                            start_datetime__lt = bk_dt)

            if coupons is not None and len(coupons) > 0:
                valid = check_coupon(coupons[0],data["id"], data["guest_number"])
                if valid['valid']:
                    free = False
                    extra_fee = 0.0
                    rules = json.loads(coupons[0].rules)
                    if type(rules["extra_fee"]) == int or type(rules["extra_fee"]) == float:
                        extra_fee = rules["extra_fee"]
                    elif type(rules["extra_fee"]) == str and rules["extra_fee"]== "FREE":
                        free = True
                        result={"valid":"yes","new_price":0.0}

                    if not free:
                        subtotal_price = 0.0
                        experience = Experience.objects.get(id = data["id"])
                        if experience.dynamic_price and type(experience.dynamic_price) == str:
                            price = experience.dynamic_price.split(',')
                            if len(price)+experience.guest_number_min-2 == experience.guest_number_max:
                            #these is comma in the end, so the length is max-min+2
                                if data["guest_number"] <= experience.guest_number_min:
                                    subtotal_price = float(experience.price) * float(experience.guest_number_min)
                                else:
                                    subtotal_price = float(price[data["guest_number"]-experience.guest_number_min]) * float(data["guest_number"])
                            else:
                                #wrong dynamic settings
                                subtotal_price = float(experience.price)*float(data["guest_number"])
                        else:
                            subtotal_price = float(experience.price)*float(data["guest_number"])

                        if extra_fee >= 1.00 or extra_fee <= -1.00:
                            #absolute value
                            price = round((subtotal_price*(1.00+settings.COMMISSION_PERCENT)+extra_fee)*(1.00+settings.STRIPE_PRICE_PERCENT) + settings.STRIPE_PRICE_FIXED,2) 
                        else:
                            #percentage, e.g., 30% discount --> percentage == -0.3
                            price = round(subtotal_price*(1.00+settings.COMMISSION_PERCENT)*(1+extra_fee)*(1.00+settings.STRIPE_PRICE_PERCENT) + settings.STRIPE_PRICE_FIXED,2)

                        result={"valid":"yes","new_price":price}
    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@csrf_exempt
def service_experience(request, format=None):
    try:
        data = request.data
        exp_id = data['experience_id']
        experience = Experience.objects.get(id=exp_id)
        available_options = []
        available_date = ()

        available_date = getAvailableOptions(experience, available_options, available_date)

        WhatsIncludedList = WhatsIncluded.objects.filter(experience=experience)
        included_food = WhatsIncludedList.filter(item='Food')[0]
        included_ticket = WhatsIncludedList.filter(item='Ticket')[0]
        included_transport = WhatsIncludedList.filter(item='Transport')[0]

        host = experience.hosts.all()[0]
        host_image = host.registereduser.image_url
        host_bio = host.registereduser.bio

        rate = 0.0
        counter = 0
        experience_reviews = []
        for review in experience.review_set.all():
            reviewer = User.objects.get(id=review.user_id)
            d={'reviewer_firstname':reviewer.first_name,
                  'reviewer_lastname':reviewer.last_name,
                  'reviewer_image':reviewer.registereduser.image_url,
                  'review_comment':review.comment,}
            experience_reviews.append(d)
            rate += review.rate
            counter += 1
        
        if counter > 0:        
            rate /= counter
        
        dynamic_price = []
        if experience.dynamic_price != None and len(experience.dynamic_price.split(',')) == experience.guest_number_max - experience.guest_number_min + 2 :
            dynamic_price = experience.dynamic_price.split(",")
            dynamic_price = [experience_fee_calculator(float(x)) for x in dynamic_price if x]

        return Response({'experience_title':experience.title,
                         'experience_language':experience.language,
                         'experience_duration':experience.duration,
                         'experience_description':experience.description,
                         'experience_activity':experience.activity,
                         'experience_interaction':experience.interaction,
                         'experience_dress':experience.dress,
                         'experience_meetup_spot':experience.meetup_spot,
                         'experience_price':experience_fee_calculator(float(experience.price)),
                         'experience_currency': str(dict(Currency)[experience.currency.upper()]),
                         'experience_dollarsign': DollarSign[experience.currency.upper()],
                         'experience_dynamic_price':dynamic_price,
                         'experience_guest_number_min':experience.guest_number_min,
                         'experience_guest_number_max':experience.guest_number_max,

                         'available_options':available_options,
                         'available_date':available_date,

                         'included_food':included_food.included,
                         'included_food_detail':included_food.details,
                         'included_ticket':included_ticket.included,
                         'included_ticket_detail':included_ticket.details,
                         'included_transport':included_transport.included,
                         'included_transport_detail':included_transport.details,

                         'host_firstname': host.first_name,
                         'host_lastname': host.last_name,
                         'host_image':host_image,
                         'host_bio':host_bio,
                         'host_id':str(host.id),

                         'experience_rate':math.ceil(rate),
                         'experience_reviews':experience_reviews,

                         }, status=status.HTTP_200_OK)

    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@authentication_classes((TokenAuthentication,))#, SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def service_myprofile(request, format=None):
    try:
        user = request.user
        profile = user.registereduser
        if request.method == "GET":
            result={'id':user.id, 'first_name':user.first_name, 'last_name':user.last_name, 'email':user.email,
                     'image':user.registereduser.image_url,'phone_number':profile.phone_number,'bio':profile.bio,'rate':profile.rate}
            return Response(result, status=status.HTTP_200_OK)
        elif request.method == "POST":
            data = request.data
            phone_number = data["phone_number"]
            profile.phone_number = phone_number
            profile.save()
            result={'id':user.id, 'first_name':user.first_name, 'last_name':user.last_name, 'email':user.email,
                     'image':user.registereduser.image_url,'phone_number':profile.phone_number,'bio':profile.bio,'rate':profile.rate}
            return Response(result, status=status.HTTP_200_OK)
    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))#, SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def service_publicprofile(request,format=None):
    try:
        data = request.query_params
        if type(data) is str:
            data = ast.literal_eval(data)

        user = User.objects.get(id=data["user_id"])
        profile = user.registereduser
        result={'first_name':user.first_name, 'last_name':user.last_name, 'image':user.registereduser.image_url}
        return Response(result, status=status.HTTP_200_OK)
    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes((SessionAuthentication, BasicAuthentication,))#, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def service_email(request, format=None):
    try:
        data = request.data
        start_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(data['start_date'].strip(), "%Y/%m/%d"))
        exps = Experience.objects.filter(start_datetime__gte = start_date).filter(status__iexact="Listed")
        hosts = []
        exp_urls = []

        for exp in exps:
            host = exp.hosts.all()[0]
            if host not in hosts:
                hosts.append(host)
                exp_urls.append([])
                exp_urls[hosts.index(host)].append('https://www.'+settings.DOMAIN_NAME + '/experience/' + str(exp.id))
            else:
                exp_urls[hosts.index(host)].append('https://www.'+settings.DOMAIN_NAME + '/experience/' + str(exp.id))
        for i in range(len(hosts)):
            host = hosts[i]
            host.first_name = host.first_name.title()
            #mail.send(subject='Tripalocal - June coupon code', message='', 
            #          sender='Tripalocal <' + 'yiyi@tripalocal.com' + '>',
            #          recipients = [Aliases.objects.filter(destination__contains=host.email)[0].mail], 
            #          priority='now',
            #          html_message=loader.render_to_string('email_june_campaign_host.html',
            #                                                {'experiences': exp_urls[i], 'host':host,
            #                                                }))
    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"error":err})
    return Response(status=status.HTTP_200_OK)

@api_view(['GET','POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication, BasicAuthentication))#))#,
@permission_classes((IsAuthenticated,))
def service_message(request, format=None):
    try:
        data = request.query_params
        if type(data) is str:
            data = ast.literal_eval(data)

        if request.method == "GET":
            sender = data["sender_id"] if "sender_id" in data else None
            id_earlier = data["id_earlier"] if "id_earlier" in data else None

            messages = None
            if sender is not None:
                #history messages from a particualr user
                if id_earlier is not None:
                    messages = Message.objects.filter(sender_id=sender, receiver_id=request.user.id, id__lt=id_earlier)
                #undelivered messages from a particualr user 
                else:
                    messages = Message.objects.filter(sender_id=sender, receiver_id=request.user.id, status__iexact="received")
            else:
                #all undelivered messages
                messages = Message.objects.filter(receiver_id=request.user.id, status__iexact="received")

            result = []
            for msg in messages:
                if msg.status == "received":
                    msg.status="delivered"
                    msg.datetime_delivered = datetime.utcnow().replace(tzinfo=pytz.UTC)
                    msg.save()
                m={"id":msg.id,"sender_id":msg.sender_id,"receiver_id":msg.receiver_id,"datetime_sent":msg.datetime_sent,
                   "datetime_read":msg.datetime_read,"status":msg.status,"content":msg.content}
                result.append(m)

            return Response({"result":result}, status=status.HTTP_200_OK)
        elif request.method == "POST":
            data = request.data
            if "message_id" not in data:
                #save message
                receiver_id = data["receiver_id"]
                content = data["content"]
              
                message = Message(sender_id=request.user.id, receiver_id=receiver_id, content=content,
                                  status="received", datetime_sent=datetime.utcnow().replace(tzinfo=pytz.UTC))
                message.save()
                return Response({"result":"message received"}, status=status.HTTP_200_OK)
            else:
                #update status: delivered-->read
                sender_id = data["sender_id"]
                message_id = data["message_id"]
                messages = Message.objects.filter(sender_id=sender_id, receiver_id=request.user.id, 
                                                  id__lte=message_id, status__iexact="delivered")
                for msg in messages:
                    msg.status="read"
                    msg.datetime_read = datetime.utcnow().replace(tzinfo=pytz.UTC)
                    msg.save()
                return Response({"result":"message status updated"}, status=status.HTTP_200_OK)
    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)