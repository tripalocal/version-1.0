from experiences.models import Booking, Experience, Payment
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.http import HttpResponseRedirect, HttpResponse, Http404
import json, pytz, xlrd, re, os, subprocess
from django.contrib.auth.models import User
from datetime import *
from app.models import RegisteredUser
from post_office import mail
from Tripalocal_V1 import settings
from tripalocal_messages.models import Aliases, Users
from experiences.forms import email_account_generator, ExperienceForm, ItineraryBookingForm
from django.db import connections
from django.template import loader, RequestContext, Context
from django.template.loader import get_template
from app.forms import BookingRequestXLSForm
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from experiences.views import get_itinerary, update_booking
from app.views import getreservation
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from allauth.account.utils import user_username, user_email, user_field
from allauth.account.signals import user_signed_up, user_logged_in
from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialLogin, SocialToken, SocialApp
from allauth.socialaccount.providers.facebook.views import fb_complete_login
from allauth.socialaccount.helpers import complete_social_login

def isLegalInput(inputs):
    for input in inputs:
        if not re.match("^[\(\)\w\d\.\s:@_-]*$", input):
            return False

    return True

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

        cursor = connections['default'].cursor()
        cursor.execute("Insert into account_emailaddress ('user_id','email','verified','primary') values (%s, %s, %s, %s)", 
                       [user.id, email, 1, 1])

        #copy to the chinese website database
        cursor = connections['cndb'].cursor()
        cursor.execute("Insert into auth_user ('id','first_name','last_name','email') values (%s, %s, %s, %s)", 
                        [user.id,user.first_name, user.last_name, user.email])
        cursor.execute("Insert into app_registereduser ('user_id') values (%s)", [user.id])

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
        mail.send(subject='[Tripalocal] Successfully registered', message='', sender='Tripalocal <enquiries@tripalocal.com>',
                      recipients = [email], priority='now', html_message=loader.render_to_string('app/email_auto_registration.html',
                                                                                                 {'email':user.email, 'password':password, 'url':'https://www.tripalocal.com/accounts/login?next=/accounts/password/change'}))

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
        cursor.execute("Insert into experiences_experience_guests ('experience_id','user_id') values (%s, %s)", [experience_id, user.id])

    ## send an email to the host
    #mail.send(subject='[Tripalocal] ' + user.first_name + ' has requested your experience', message='',
    #            sender='Tripalocal <' + Aliases.objects.filter(destination__contains=user.email)[0].mail + '>',
    #            recipients = [Aliases.objects.filter(destination__contains=experience.hosts.all()[0].email)[0].mail], #fail_silently=False,
    #            priority='now',
    #            html_message=loader.render_to_string('email_booking_requested_host.html', 
    #                                                    {'experience': experience,
    #                                                    'booking':booking,
    #                                                    'user_first_name':user.first_name,
    #                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
    #                                                    'accept_url': settings.DOMAIN_NAME + '/booking/' + str(booking.id) + '?accept=yes',
    #                                                    'reject_url': settings.DOMAIN_NAME + '/booking/' + str(booking.id) + '?accept=no'}))
    ## send an email to the traveler
    #mail.send(subject='[Tripalocal] You booking request is sent to the host',  message='', 
    #            sender='Tripalocal <' + Aliases.objects.filter(destination__contains=experience.hosts.all()[0].email)[0].mail + '>',
    #            recipients = [Aliases.objects.filter(destination__contains=user.email)[0].mail], #fail_silently=False,
    #            priority='now', 
    #            html_message=loader.render_to_string('email_booking_requested_traveler.html',
    #                                                    {'experience': experience, 
    #                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
    #                                                    'booking':booking}))

    host = experience.hosts.all()[0]
    #send an email to the traveller
    mail.send(subject='[Tripalocal] Booking confirmed', message='', 
                sender='Tripalocal <' + Aliases.objects.filter(destination__contains=host.email)[0].mail + '>',
                recipients = [Aliases.objects.filter(destination__contains=user.email)[0].mail], 
                priority='now',  #fail_silently=False, 
                html_message=loader.render_to_string('email_booking_confirmed_traveler.html',
                                                    {'experience': experience,
                                                    'booking':booking,
                                                    'user':user, #not host --> need "my" phone number
                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))
            
    #schedule an email for reviewing the experience
    mail.send(subject='[Tripalocal] How was your experience?', message='', 
                sender='Tripalocal <enquiries@tripalocal.com>',
                recipients = [Aliases.objects.filter(destination__contains=user.email)[0].mail], 
                priority='high',  scheduled_time = booking.datetime + timedelta(days=1), 
                html_message=loader.render_to_string('email_review_traveler.html',
                                                    {'experience': experience,
                                                    'booking':booking,
                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                    'review_url':settings.DOMAIN_NAME + '/reviewexperience/' + str(experience.id)}))

    #send an email to the host
    mail.send(subject='[Tripalocal] Booking confirmed', message='', 
                sender='Tripalocal <' + Aliases.objects.filter(destination__contains=user.email)[0].mail + '>',
                recipients = [Aliases.objects.filter(destination__contains=host.email)[0].mail], 
                priority='now',  #fail_silently=False, 
                html_message=loader.render_to_string('email_booking_confirmed_host.html',
                                                    {'experience': experience,
                                                    'booking':booking,
                                                    'user':user, # guest here
                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))

    #schedule an email to the traveller one day before the experience
    mail.send(subject='[Tripalocal] Booking reminder', message='', 
                sender='Tripalocal <' + Aliases.objects.filter(destination__contains=host.email)[0].mail + '>',
                recipients = [Aliases.objects.filter(destination__contains=user.email)[0].mail], 
                priority='high',  scheduled_time = booking.datetime - timedelta(days=1), 
                html_message=loader.render_to_string('email_reminder_traveler.html',
                                                    {'experience': experience,
                                                    'booking':booking,
                                                    'user':user, #not host --> need "my" phone number
                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))
            
    #schedule an email to the host one day before the experience
    mail.send(subject='[Tripalocal] Booking reminder', message='', 
                sender='Tripalocal <' + Aliases.objects.filter(destination__contains=user.email)[0].mail + '>',
                recipients = [Aliases.objects.filter(destination__contains=host.email)[0].mail], 
                priority='high',  scheduled_time = booking.datetime - timedelta(days=1),  
                html_message=loader.render_to_string('email_reminder_host.html',
                                                    {'experience': experience,
                                                    'booking':booking,
                                                    'user':user,
                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))

def saveBookingRequestsFromXLS(request):
    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect("/accounts/login/?next=/booking_request_xls")

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
    template = "add_experience_experience.html"

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

@api_view(['POST'])
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
            result = {"error":"User not existing"}
            return Response(result, status=status.HTTP_404_NOT_FOUND)

    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
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

        u = User.objects.filter(username = username)
        counter = len(u) if u is not None else 0
        counter += 1
        username = username + str(counter) if counter > 1 else username 

        user = User(first_name = first_name, last_name = last_name, email = email,username = username,
                    date_joined = datetime.utcnow().replace(tzinfo=pytz.UTC),
                    last_login = datetime.utcnow().replace(tzinfo=pytz.UTC))
        user.save()

        user.set_password(password)
        user.save()

        user_signed_up.send(sender=user.__class__, request=request, user=user)
        user = authenticate(username=username, password=password)
        login(request, user)
        new_token = Token.objects.get_or_create(user=user)
        result = {'user_id':user.id, 'token':new_token[0].key}

        return Response(result, status=status.HTTP_200_OK)

    except Exception as err:
        #TODO
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
def service_facebook_login(request):
    data = request.data #self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))

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
@authentication_classes((TokenAuthentication,))#, SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def service_search(request, format=None):
    try:
        criteria = request.data #request.query_params['data']
        start_datetime = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(criteria['start_datetime'], "%Y-%m-%d"))
        end_datetime = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(criteria['end_datetime'], "%Y-%m-%d"))
        city = criteria['city']
        guest_number = criteria['guest_number']
        keywords = criteria['keywords']
        language = "Chinese,English"

        itinerary = get_itinerary(start_datetime, end_datetime, guest_number, city, language, keywords)

        return Response(itinerary, status=status.HTTP_200_OK)
    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))#, SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def service_mytrip(request, format=None):
    try:
        user = request.user
        b = Booking.objects.filter(user=user)
        cursor = connections['cndb'].cursor()
        rows = cursor.execute('select datetime, status, guest_number, experience_id from experiences_booking where user_id = %s order by datetime',
                                [request.user.id]).fetchall()

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
                row = cursor.execute('select meetup_spot, title from experiences_experience where id = %s',
                                [rows[index][3]]).fetchone()
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
                  'experience_title':booking.experience.title, 'meetup_spot':booking.experience.meetup_spot,
                  'host_name':host.first_name + ' ' + host.last_name, 'host_phone_number':phone_number}

            bks.append(bk)

        return Response(bks, status=status.HTTP_200_OK)
    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))#, SessionAuthentication, BasicAuthentication))
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
@authentication_classes((TokenAuthentication,))#, SessionAuthentication, BasicAuthentication))
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

#{"itinerary_string":[{"id":"1","date":"2015/04/17","time":"4:00 - 6:00","guest_number":"2"},{"id":"20","date":"2015/04/17","time":"17:00 - 20:00","guest_number":"2"}],"card_number":"4242424242424242","expiration_month":10,"expiration_year":2015,"cvv":123}
@api_view(['POST'])
@authentication_classes((TokenAuthentication,))#, SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def service_booking(request, format=None):
    try:
        data = request.data
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

        ItineraryBookingForm.booking(ItineraryBookingForm(),booking_data['experience_id'],booking_data['date'],booking_data['time'],booking_data['user'],booking_data['guest_number'],
                                     booking_data['card_number'],booking_data['exp_month'],booking_data['exp_year'],booking_data['cvv'])
        return Response("Success", status=status.HTTP_200_OK)

    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)
