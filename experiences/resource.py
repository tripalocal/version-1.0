from experiences.models import *
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse
import json, pytz, xlrd, re, os, subprocess, math, logging, ast
from django.contrib.auth.models import User
from datetime import *
from app.models import *
from post_office import mail
from Tripalocal_V1 import settings
from tripalocal_messages.models import Aliases, Users
from experiences.forms import *
from django.db import connections
from django.template import loader, RequestContext, Context
from django.template.loader import get_template
from app.forms import UploadXLSForm, ExperienceTagsXLSForm
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from experiences.views import get_itinerary, update_booking, getAvailableOptions, update_pageview_statistics, get_related_experiences, get_experience_popularity
from app.views import getreservation
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from allauth.account.utils import user_username, user_email, user_field
from allauth.account.signals import user_signed_up, user_logged_in
from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialLogin, SocialToken, SocialApp
from allauth.socialaccount.helpers import complete_social_login
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from experiences.constant import  *
from experiences.telstra_sms_api import send_sms
from experiences.utils import *

if settings.LANGUAGE_CODE.lower() != "zh-cn":
    from allauth.socialaccount.providers.facebook.views import fb_complete_login

GEO_POSTFIX = settings.GEO_POSTFIX

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
            while curr_row < 2:
                #the first two rows are tags
                while curr_cell < num_cells:
                    curr_cell += 1
                    # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
                    cell_type = worksheet.cell_type(curr_row, curr_cell)
                    cell_value = worksheet.cell_value(curr_row, curr_cell)
                    if cell_type == 1 or cell_type == 0:
                        all_tags.append(cell_value)
                    else:
                        raise Exception("Type error: column name, " + str(curr_cell))
                curr_row += 1
                curr_cell = -1

            cursor = connections['default'].cursor()
            #delete all existing records
            cursor.execute("delete from experiences_experience_tags")
            cursor.execute("delete from experiences_newproduct_tags")
            cursor.execute("delete from experiences_experiencetag")
            #add new tags
            all_tags = [x for x in all_tags if x]
            for i in range(len(all_tags)):
                tag = ExperienceTag(tag = all_tags[i], language = "en" if isEnglish(all_tags[i]) else "zh")
                tag.save()
                all_tags.remove(all_tags[i])
                all_tags.insert(i, tag)

            curr_row = 1
            #start from the third row
            while curr_row < num_rows:
                curr_row += 1
                row = worksheet.row(curr_row)

                curr_cell = 0
                id = row[curr_cell].value
                id = int(id)
                try:
                    exp = AbstractExperience.objects.get(id=id)
                except AbstractExperience.DoesNotExist:
                    continue

                while curr_cell < num_cells:
                    curr_cell += 1
                    # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
                    cell_type = worksheet.cell_type(curr_row, curr_cell)

                    if cell_type == 1 or cell_type == 0:
                        if worksheet.cell_value(curr_row, curr_cell).lower() == "y":
                            exp.tags.add(all_tags[curr_cell-1])
                            exp.tags.add(all_tags[curr_cell-1+num_cells])
                    else:
                        raise Exception("Type error: row " + str(curr_row) + ", col " + str(curr_cell))
    else:
        form = ExperienceTagsXLSForm()

    return render_to_response('app/experience_tags_xls.html', {'form': form}, context)

def get_user(first_name, last_name, email, phone):
    '''
    if the user does not exist, create a new one, otherwise return the user
    '''
    if email is None and phone is None:
        return None

    if email is None:
        profile = RegisteredUser.objects.filter(phone_number = phone)
        if profile and len(profile):
            profile = profile[0]
            return profile.user
        else:
            return None
    else:
        try:
            user = User.objects.get(email=email)
            return user
        except User.DoesNotExist:
            if first_name is None or last_name is None or phone is None:
                return None

            count = len(User.objects.filter(first_name__iexact=first_name)) + len(User.objects.filter(username__iexact=first_name))
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
            cursor.execute("Insert into account_emailaddress (user_id,email,verified,`primary`) values (%s, %s, %s, %s)", 
                           [user.id, email, 1, 1])

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

            #send a welcome email
            mail.send(subject=_('[Tripalocal] Successfully registered'), message='', sender=settings.DEFAULT_FROM_EMAIL,
                          recipients = [email], priority='now', html_message=loader.render_to_string('app/email_auto_registration.html',
                                                                                                     {'email':user.email, 'password':password, 'url':'https://www.tripalocal.com' + GEO_POSTFIX + 'accounts/login?next=' + GEO_POSTFIX + 'accounts/password/change/'}))

            return user

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

    experience = AbstractExperience.objects.get(id=experience_id)
    exp_information = experience.get_information(settings.LANGUAGES[0][0])
    experience.title = exp_information.title
    experience.meetup_spot = exp_information.meetup_spot

    #create a new account if the user does not exist
    user = get_user(first_name, last_name, email, phone)

    #record the booking request
    local_timezone = pytz.timezone(experience.get_timezone())
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
        experience.guests.add(user)

    host = experience.get_host()
    #send an email to the traveller
    mail.send(subject=_('[Tripalocal] Booking confirmed'), message='', 
                sender=_('Tripalocal <') + Aliases.objects.filter(destination__contains=host.email)[0].mail + '>',
                recipients = [Aliases.objects.filter(destination__contains=user.email)[0].mail], 
                priority='now',  #fail_silently=False, 
                html_message=loader.render_to_string('experiences/email_booking_confirmed_traveler.html',
                                                    {'experience': experience,
                                                    'booking':booking,
                                                    'user':user, #not host --> need "my" phone number
                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                    'LANGUAGE':settings.LANGUAGE_CODE}))
            
    #schedule an email for reviewing the experience
    mail.send(subject=_('[Tripalocal] How was your experience?'), message='', 
                sender=settings.DEFAULT_FROM_EMAIL,
                recipients = [Aliases.objects.filter(destination__contains=user.email)[0].mail], 
                priority='high',  scheduled_time = booking.datetime + timedelta(days=1), 
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
                                                    'user':user, # guest here
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

def saveBookingRequestsFromXLS(request):
    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/?next=" + GEO_POSTFIX + "booking_request_xls")

    context = RequestContext(request)
    if request.method == 'POST':
        form = UploadXLSForm(request.POST, request.FILES)
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

            if settings.LANGUAGES[0][0] == "en":
                worksheet = workbook.sheet_by_name('English')
            elif settings.LANGUAGES[0][0] == "zh":
                worksheet = workbook.sheet_by_name('Chinese')
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
        form = UploadXLSForm()

    return render_to_response('app/booking_request_xls.html', {'form': form}, context)

def updateNewProduct(experience):
    id = experience['Tripalocal listing ID']
    title = experience['Title']
    background = experience['Background info']
    description = experience['Description']
    service = experience['Service']
    highlights = experience['Highlights']
    schedule = experience['Schedule']
    whatsincluded = experience['What\'s included']
    language = experience['Language']
    disclaimer = experience['Disclaimer']
    guest_number_min = int(float(experience['Guest number min']))
    guest_number_max = int(float(experience['Guest number max']))
    price = float(experience['Price'])
    refund_policy = experience['Refund policy']
    ticket_use_instruction = experience['Ticket use instruction']
    notice = experience['Notice']
    pick_up = experience['Pick up detail']
    insurance = experience['Insurance']

    if id and len(id):
        #update an existing experience
        id = int(id)
        exp = AbstractExperience.objects.get(id = id)
    else:
        #create a new product
        exp = NewProduct()

    exp.start_datetime = pytz.timezone("UTC").localize(datetime.utcnow())
    exp.end_datetime = pytz.timezone("UTC").localize(datetime.utcnow()) + timedelta(weeks=520)
    exp.suppliers.add(Provider.objects.get(id=1))
    exp.language = language.lower() + ";"
    exp.guest_number_min = guest_number_min
    exp.guest_number_max = guest_number_max
    exp.price = price
    exp.save()

    exp_i18n = NewProductI18n()

    if hasattr(exp, 'newproducti18n_set') and len(exp.newproducti18n_set.all()) > 0:
        exp_i18n_prev = exp.newproducti18n_set.filter(language = settings.LANGUAGES[0][0])
        if len(exp_i18n_prev)>0:
            exp_i18n = exp_i18n_prev[0]
    
    exp_i18n.title = title
    exp_i18n.background_info = background
    exp_i18n.description = description
    exp_i18n.service = service
    exp_i18n.highlights = highlights
    exp_i18n.schedule = schedule
    exp_i18n.whatsincluded = whatsincluded
    exp_i18n.disclaimer = disclaimer
    exp_i18n.title = title
    exp_i18n.refund_policy = refund_policy
    exp_i18n.ticket_use_instruction = ticket_use_instruction
    exp_i18n.notice = notice
    exp_i18n.pickup_detail = pick_up
    exp_i18n.insurance = insurance
    exp_i18n.language = settings.LANGUAGES[0][0]

    exp_i18n.product_id = exp.id
    exp_i18n.save()

def updateNewProductFromXLS(request):
    if not (request.user.is_authenticated() and request.user.is_superuser):
        return HttpResponseRedirect(GEO_POSTFIX + "accounts/login/?next=" + GEO_POSTFIX + "update_newproduct_xls")

    context = RequestContext(request)
    if request.method == 'POST':
        form = UploadXLSForm(request.POST, request.FILES)
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

            worksheet = workbook.sheet_by_name('Sheet 1')

            num_rows = worksheet.nrows - 1
            num_cells = worksheet.ncols - 1
            curr_row = 0
            col_names= []
            legal_names= ['Tripalocal listing ID', 'Title', 'Background info', 'Description',
                          'Service', 'Highlights', 'Schedule', 'What\'s included', 'Language',
                          'Disclaimer', 'Guest number min', 'Guest number max', 'Price', 'Refund policy', 'Ticket use instruction',
                          'Notice', 'Pick up detail', 'Insurance']

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
                experience={}
                while curr_cell < num_cells:
                    curr_cell += 1
                    # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
                    cell_type = worksheet.cell_type(curr_row, curr_cell)

                    if cell_type <= 2:
                        experience[col_names[curr_cell]] = str(worksheet.cell_value(curr_row, curr_cell))
                    else:
                        raise Exception("Type error: row " + str(curr_row) + ", col " + str(curr_cell))

                if experience:
                    updateNewProduct(experience)
    else:
        form = UploadXLSForm()

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
@authentication_classes((TokenAuthentication,))# SessionAuthentication, BasicAuthentication))
def service_wishlist(request):
    if request.method == 'POST': #request.is_ajax() and 
        try:
            if request.is_ajax():
                data = request.POST
            else:
                data=request.data

            user_id = int(data['user_id'])
            experience_id = int(data['experience_id'])
            added = data['added']

            user = User.objects.get(id=user_id)
            experience = AbstractExperience.objects.get(id=experience_id)
            if added == "False":
                try:
                    #user.registereduser.wishlist.add(experience)
                    cursor = connections['default'].cursor()
                    cursor.execute("select id from app_registereduser_wishlist where experience_id=%s and registereduser_id=%s", [experience.id, user.registereduser.id])
                    wl = cursor._rows
                    if wl is not None and len(wl)>0:
                        response={'success':False, 'error':'already added'}
                        return HttpResponse(json.dumps(response),content_type="application/json")

                    cursor.execute("Insert into app_registereduser_wishlist (experience_id,registereduser_id) values (%s, %s)", [experience.id, user.registereduser.id])

                    response={'success':True, 'added':True}
                except BaseException:
                    response={'success':False, 'error':'fail to add'}
                    return HttpResponse(json.dumps(response),content_type="application/json")
            else:
                try:
                    #user.registereduser.wishlist.remove(experience)
                    cursor = connections['default'].cursor()
                    cursor.execute("delete from app_registereduser_wishlist where experience_id=%s and registereduser_id=%s", [experience.id, user.registereduser.id])

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
            cursor = connections['default'].cursor()
            wl = cursor.execute("select experience_id from app_registereduser_wishlist where registereduser_id=%s", [user.registereduser.id])
            wl = cursor._rows
            experiences = []
            for id in wl:
                experience = AbstractExperience.objects.get(id=id[0])
                #price
                if experience.guest_number_min <= 4 and experience.guest_number_max>=4:
                    guest_number = 4
                elif experience.guest_number_min > 4:
                    guest_number = experience.guest_number_min
                elif experience.guest_number_max < 4:
                    guest_number = experience.guest_number_max
                exp_price = float(experience.price)
                if experience.dynamic_price != None and len(experience.dynamic_price.split(',')) == experience.guest_number_max - experience.guest_number_min + 2 :
                    exp_price = float(experience.dynamic_price.split(",")[int(guest_number)-experience.guest_number_min])

                photo_url = ''
                photos = experience.photo_set.all()
                if photos is not None and len(photos) > 0:
                    photo_url = photos[0].directory+photos[0].name
                exp_information = experience.get_information(settings.LANGUAGES[0][0])
                experiences.append({'id':experience.id,
                                    'title':exp_information.title,
                                    'description':exp_information.description,
                                    'price':experience_fee_calculator(exp_price, experience.commission),
                                    'language':experience.language,
                                    'duration':experience.duration,
                                    'photo_url':photo_url,
                                    'host_image':experience.get_host().registereduser.image_url})

            return Response(experiences,status=status.HTTP_200_OK)

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
        keywords = criteria.get('keywords', None)
        language = "Mandarin,English"
        type = criteria.get('type', 'experience')

        if keywords is not None and len(keywords) == 0:
            keywords = None

        if int(guest_number) == 0:
            itinerary = get_itinerary(type, start_datetime, end_datetime, None, city, language, keywords, mobile=True)
        else:
            itinerary = get_itinerary(type, start_datetime, end_datetime, guest_number, city, language, keywords, mobile=True)

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
        booking_status = ["paid","accepted","rejected","paid_archived","accepted_archived","rejected_archived"]
        b = Booking.objects.filter(user=user, status__in=booking_status)

        bookings = []
        for booking in b:
            bookings.append(booking)

        bookings = sorted(bookings, key=lambda booking: booking.datetime, reverse=True)

        bks = []
        for booking in bookings:
            payment = booking.payment if booking.payment_id != None else Payment()
            host = get_host(booking.experience)
            phone_number = host.registereduser.phone_number

            photo_url = ''
            photos = booking.experience.photo_set.all()
            if photos is not None and len(photos) > 0:
                photo_url = photos[0].directory+photos[0].name

            exp_information = booking.experience.get_information(settings.LANGUAGES[0][0])
            # Convert timezone
            local_timezone = pytz.timezone(experience.get_timezone())
            bk = {'datetime':booking.datetime.astimezone(local_timezone).isoformat(), 'status':booking.status,
                  'guest_number':booking.guest_number, 'experience_id':booking.experience.id,
                  'experience_title':exp_information.title,
                  'experience_photo':photo_url, 'experience_type':booking.experience.type,
                  'meetup_spot':exp_information.meetup_spot,
                  'host_id':host.id, 'host_name':host.first_name + ' ' + host.last_name[:1] + '.',
                  'host_phone_number':phone_number,'host_image':host.registereduser.image_url}

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
@authentication_classes((TokenAuthentication,)) #SessionAuthentication, BasicAuthentication))
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
@authentication_classes((TokenAuthentication,))# SessionAuthentication, BasicAuthentication))
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
            ItineraryBookingForm.booking(ItineraryBookingForm(),booking_data['experience_id'],booking_data['date'],booking_data['time'],booking_data['user'],adult_number=booking_data['guest_number'],
                                         card_number=booking_data['card_number'],exp_month=booking_data['exp_month'],exp_year=booking_data['exp_year'],cvv=booking_data['cvv'],coupon=coupons[0])
        else:
            ItineraryBookingForm.booking(ItineraryBookingForm(),booking_data['experience_id'],booking_data['date'],booking_data['time'],booking_data['user'],adult_number=booking_data['guest_number'],
                                         card_number=booking_data['card_number'],exp_month=booking_data['exp_month'],exp_year=booking_data['exp_year'],cvv=booking_data['cvv'])

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

#{"partner":"test","bookings":[
#{"first_name":"first","last_name":"last","email":"test@test.com","phone":"123456789","experience_id":"2","datetime":"2015/12/17 12:00","guest_number_adult":2,"guest_number_children":2,"coupon":"abcdefgh"},
#{"email":"test@test.com","experience_id":"1","datetime":"2015/12/28 17:00","guest_number_adult":3,"guest_number_children":0,"coupon":""},
#{"phone":"123456789","experience_id":"20","datetime":"2015/12/28 17:00","guest_number_adult":3,"guest_number_children":0,"coupon":""},
#]}
@api_view(['POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def service_booking_request(request, format=None):
    try:
        data = request.data

        if type(data) is str:
            data = ast.literal_eval(data)

        bookings = data['bookings']
        partner = data['partner']

        for item in bookings:
            first_name = item['first_name'] if 'first_name' in item else None
            last_name = item['last_name'] if 'last_name' in item else None
            email = item['email'] if 'email' in item else None
            phone = item['phone'] if 'phone' in item else None
            user = get_user(first_name, last_name, email, phone)
            if user is None:
                raise Exception("Incomplete/Incorrect user information")
            experience = AbstractExperience.objects.get(id=str(item['experience_id']))
            local_timezone = pytz.timezone(experience.get_timezone())
            host = experience.get_host()
            bk_datetime = local_timezone.localize(datetime.strptime(item['datetime'].strip(), "%Y/%m/%d %H:%M")).astimezone(pytz.timezone("UTC"))
            guest_number_adult = int(item['guest_number_adult'])
            guest_number_children = int(item['guest_number_children'])
            coupon = None
            if 'coupon' in item and len(item['coupon']) > 0:
                coupon = Coupon.objects.filter(promo_code__iexact = item['coupon'],
                                               end_datetime__gt = bk_datetime,
                                               start_datetime__lt = bk_datetime)
                if len(coupon)>0:
                    coupon = coupon[0]
                    valid = check_coupon(coupon, experience.id, guest_number_adult + guest_number_children)
                    if not valid['valid']:
                        coupon = None
                else:
                    coupon = None

            booking = Booking(user = user, experience = experience, guest_number = guest_number_adult + guest_number_children,
                              adult_number = guest_number_adult, children_number = guest_number_children,
							  datetime = bk_datetime, submitted_datetime = datetime.utcnow().replace(tzinfo=pytz.UTC),
							  status=partner, coupon=coupon)
            
            booking.save()
            send_booking_email_verification(booking, experience, user, False)

        result = {"success":"true"}
        return Response(result, status=status.HTTP_200_OK)
    except Exception as err:
        #TODO
        logger = logging.getLogger("Tripalocal_V1")
        reason = ""
        if hasattr(err, 'detail'):
            reason = err.detail
        else:
            reason = err
        logger.error(reason)
        result = {"success":"false","error":reason}
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

#{"coupon":"aasfsaf","id":"20","date":"2015/06/17","time":"4:00 - 6:00","guest_number":2}
@api_view(['POST'])
@authentication_classes((TokenAuthentication,))# SessionAuthentication, BasicAuthentication)) #
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
                    result={"valid":"yes","new_price":valid['new_price']}
    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

    return Response(result, status=status.HTTP_200_OK)

def get_experience_detail(experience, get_available_date=True, partner = False):
    available_options = []
    available_date = ()

    if get_available_date:
        available_date = getAvailableOptions(experience, available_options, available_date)

    if type(experience) == Experience:
        WhatsIncludedList = WhatsIncluded.objects.filter(experience=experience)
        included_food = WhatsIncludedList.filter(item='Food', language=settings.LANGUAGES[0][0])[0]
        included_ticket = WhatsIncludedList.filter(item='Ticket', language=settings.LANGUAGES[0][0])[0]
        included_transport = WhatsIncludedList.filter(item='Transport', language=settings.LANGUAGES[0][0])[0]

        host = experience.get_host()
        host_image = host.registereduser.image_url
        host_bio = get_user_bio(host.registereduser, settings.LANGUAGES[0][0])

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
        dynamic_price = [experience_fee_calculator(float(x), experience.commission) for x in dynamic_price if x]

    experience_images = []
    photos = experience.photo_set.all()
    for photo in photos:
        experience_images.append(photo.directory+photo.name)

    result = {'experience_id':experience.id,
                'experience_language':experience.language,
                'experience_duration':experience.duration,
                'experience_price':experience_fee_calculator(float(experience.price), 
                                                             experience.commission if not partner else experience.commission/(2-experience.commission)),
                'experience_currency': str(dict(Currency).get(experience.currency.upper(),experience.currency.upper())),
                'experience_dollarsign': DollarSign.get(experience.currency.upper(),'$'),
                'experience_dynamic_price':dynamic_price if not partner else "",
                'experience_guest_number_min':experience.guest_number_min,
                'experience_guest_number_max':experience.guest_number_max,
                'experience_images':experience_images,
                'experience_city':experience.city,
                'experience_type':experience.type,

                'experience_rate':math.ceil(rate),
                'experience_reviews':experience_reviews,

                'experience_popularity':get_experience_popularity(experience),
            }

    if get_available_date:
        avail_date = {'available_options':available_options,
            'available_date':available_date,}
        result.update(avail_date)

    if type(experience) == Experience:
        exp_information = experience.get_information(settings.LANGUAGES[0][0])
        result_experience = {'experience_title':exp_information.title,
                'experience_description':exp_information.description,
                'experience_activity':exp_information.activity,
                'experience_interaction':exp_information.interaction,
                'experience_dress':exp_information.dress,
                'experience_meetup_spot':exp_information.meetup_spot,
                    
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
                'host_id':str(host.id),}
        result.update(result_experience)
    else:
        result_newproduct = {'title':'',
                                'description':'',
                                'highlights':'',
                                'notice':'',
                                'tips':'',
                                'whatsincluded':'',
                                'pickup_detail':'',
                                'service':'',
                                'schedule':'',
                                'disclaimer':'',
                                'refund_policy':'',
                                'insurance':'',
                                }
        if experience.newproducti18n_set is not None and len(experience.newproducti18n_set.all()) > 0:
            t = experience.newproducti18n_set.filter(language=settings.LANGUAGES[0][0])
            if len(t)>0:
                t=t[0]
            else:
                t = experience.newproducti18n_set.all()[0]

            result_newproduct['title'] = t.title
            result_newproduct['description'] = t.description
            result_newproduct['highlights'] = t.highlights
            result_newproduct['notice'] = t.notice
            result_newproduct['tips'] = t.tips
            result_newproduct['whatsincluded'] = t.whatsincluded
            result_newproduct['service'] = t.service
            result_newproduct['schedule'] = experience.instant_booking
            result_newproduct['disclaimer'] = t.disclaimer
            result_newproduct['refund_policy'] = t.refund_policy
            result_newproduct['insurance'] = t.insurance
            result_newproduct['pickup_detail'] = t.pickup_detail

        result.update(result_newproduct)

    #get related experiences
    result_related = {"related_experiences":[]}
    related_experiences = get_related_experiences(experience, None)
    for exp in related_experiences:
        image=""
        ph = exp.photo_set.all()
        if ph and len(ph) > 0:
            image = ph[0].directory+ph[0].name
        result_related['related_experiences'].append({'image':image,
                                                      'id':exp.id,
                                                      'title':exp.get_information(settings.LANGUAGE_CODE[0][0]).title,
                                                      'price':float(exp.price)*exp.commission, #commission is updated in get_related_experiences 
                                                      'currency': str(dict(Currency).get(exp.currency.upper(),exp.currency.upper())),
                                                      'dollarsign': DollarSign.get(exp.currency.upper(),'$'),
                                                      'duration':exp.duration,
                                                      'language':exp.language})
    result.update(result_related)
    return result

#TODO: change to GET
@api_view(['POST'])
@csrf_exempt
def service_experience(request, format=None):
    try:
        data = request.data
        experience = AbstractExperience.objects.get(id=data['experience_id'])
        result = get_experience_detail(experience)

        return Response(result, status=status.HTTP_200_OK)

    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@csrf_exempt
def service_experiencedetail(request, format=None):
    try:
        data = request.query_params
        if type(data) is str:
            data = ast.literal_eval(data)

        experience = AbstractExperience.objects.get(id=data['experience_id'])
        result = get_experience_detail(experience, False)

        return Response(result, status=status.HTTP_200_OK)

    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))# SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated, IsAdminUser))
def service_all_products(request, format=None):
    try:
        result=[]
        cursor = connections['default'].cursor()
        raw_query = "select experiences_newproducti18n.*,"+\
	                       "experiences_newproduct.duration,"+\
                           "experiences_newproduct.guest_number_min,"+\
                           "experiences_newproduct.guest_number_max,"+\
                           "round(experiences_newproduct.price*(2 - experiences_newproduct.commission/(2 - 2*experiences_newproduct.commission)),0) as price,"+\
                           "experiences_newproduct.city,"+\
                           "experiences_newproduct.language,"+\
                           "experiences_newproduct.currency"+\
                    " from experiences_newproduct, experiences_newproducti18n"+\
                    " where experiences_newproduct.abstractexperience_ptr_id = experiences_newproducti18n.product_id"+\
                          " and experiences_newproducti18n.language='zh'"

        cursor.execute(raw_query)
        nps = cursor._rows
        if nps is not None and len(nps)>0:
            for product in nps:
                result.append({"title":product[2],"location":product[3],"background_info":product[4],"description":product[5],"service":product[6],
                               "highlights":product[7],"schedule":product[8],"ticket_use_instruction":product[9],"refund_policy":product[10],"notice":product[11],
                               "tips":product[12],"whatsincluded":product[12],"pickup_detail":product[14],"combination_options":product[15],"insurance":product[16],
                               "disclaimer":product[17],"id":product[17],"duration":product[19],"guest_number_min":product[20],"guest_number_max":product[21],
                               "price":product[22],"city":product[23],"language":product[24],"currency":product[25],})

        raw_query = "select experiences_experiencetitle.title,"+\
                           "experiences_experiencedescription.description,"+\
                           "experiences_experienceactivity.activity,"+\
                           "experiences_experienceinteraction.interaction,"+\
                           "experiences_experiencedress.dress,"+\
                           "experiences_experiencemeetupspot.meetup_spot,"+\
	                       "experiences_experience.duration,"+\
                           "experiences_experience.guest_number_min,"+\
                           "experiences_experience.guest_number_max,"+\
                           "round(experiences_experience.price*(2 - experiences_experience.commission/(2 - 2*experiences_experience.commission)),0) as price,"+\
                           "experiences_experience.city,"+\
                           "experiences_experience.language,"+\
                           "experiences_experience.currency,"+\
                           "experiences_experience.abstractexperience_ptr_id as id"+\
                    " from  experiences_experience,experiences_experiencetitle,experiences_experiencedescription,"+\
                          "experiences_experienceactivity,experiences_experienceinteraction,experiences_experiencedress,"+\
                          "experiences_experiencemeetupspot"+\
                    " where experiences_experience.status=\"Listed\" and experiences_experiencetitle.language=\"zh\""+\
                          " and experiences_experiencedescription.language=\"zh\" and experiences_experienceactivity.language=\"zh\""+\
                          " and experiences_experienceinteraction.language=\"zh\" and experiences_experiencedress.language=\"zh\""+\
                          " and experiences_experiencemeetupspot.language=\"zh\""+\
                          " and experiences_experience.abstractexperience_ptr_id = experiences_experiencetitle.experience_id"+\
                          " and experiences_experience.abstractexperience_ptr_id = experiences_experiencedescription.experience_id"+\
                          " and experiences_experience.abstractexperience_ptr_id = experiences_experienceactivity.experience_id"+\
                          " and experiences_experience.abstractexperience_ptr_id = experiences_experienceinteraction.experience_id"+\
                          " and experiences_experience.abstractexperience_ptr_id = experiences_experiencedress.experience_id"+\
                          " and experiences_experience.abstractexperience_ptr_id = experiences_experiencemeetupspot.experience_id"+\
                    " order by id;"

        cursor.execute(raw_query)
        exps = cursor._rows
        if exps is not None and len(exps)>0:
            for experience in exps:
                result.append({"title":experience[0],"description":experience[1],"activity":experience[2],
                               "interaction":experience[3],"dress":experience[4],"meetup_spot":experience[5],
                               "duration":experience[6],"guest_number_min":experience[7],"guest_number_max":experience[8],
                               "price":experience[9],"city":experience[10],"language":experience[11],
                               "currency":experience[12],"id":experience[13]})

        return Response(result, status=status.HTTP_200_OK)

    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@authentication_classes((TokenAuthentication,))# SessionAuthentication, BasicAuthentication))
@permission_classes((IsAuthenticated,))
def service_myprofile(request, format=None):
    try:
        user = request.user
        profile = user.registereduser
        if request.method == "GET":
            result={'id':user.id, 'first_name':user.first_name, 'last_name':user.last_name, 'email':user.email,
                     'image':user.registereduser.image_url,'phone_number':profile.phone_number if profile.phone_number is not None else "",
                     'bio':get_user_bio(profile, settings.LANGUAGES[0][0]),'rate':profile.rate}
            return Response(result, status=status.HTTP_200_OK)
        elif request.method == "POST":
            data = request.data
            phone_number = data["phone_number"]
            profile.phone_number = phone_number
            profile.save()
            result={'id':user.id, 'first_name':user.first_name, 'last_name':user.last_name, 'email':user.email,
                     'image':user.registereduser.image_url,'phone_number':profile.phone_number,
                     'bio':get_user_bio(profile, settings.LANGUAGES[0][0]),'rate':profile.rate}
            return Response(result, status=status.HTTP_200_OK)
    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))# SessionAuthentication, BasicAuthentication))
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

#{"messages":[{"receiver_id":677,"msg_content":"afdaf","msg_date":"2015/04/06/00/00/00/123","local_id":100},{"receiver_id":677,"msg_content":"sdfg","msg_date":"2015/05/06/00/00/00/567","local_id":200}]}
@api_view(['GET','POST'])
@authentication_classes((TokenAuthentication, SessionAuthentication, BasicAuthentication))#))#,
@permission_classes((IsAuthenticated,))
def service_message(request, format=None):
    try:
        if request.method == "GET":
            data = request.query_params
            if type(data) is str:
                data = ast.literal_eval(data)

            sender_id = int(data["sender_id"]) if "sender_id" in data else None
            receiver_id = request.user.id
            last_update_id = int(data["last_update_id"]) if "last_update_id" in data else None

            messages = None
            if sender_id is not None and last_update_id is not None:
                #messages since last_update_id from a particualr user
                messages = Message.objects.raw('select * from app_message where ((sender_id=%s and receiver_id=%s) or (sender_id=%s and receiver_id=%s)) and id > %s',
                                               [sender_id, receiver_id, receiver_id, sender_id, last_update_id])
            else:
                message_list = {"error":"missing parameters"}
                return Response({"result":message_list}, status=status.HTTP_400_BAD_REQUEST)

            message_list = []
            for msg in messages:
                m = {"id":msg.id,"sender_id":msg.sender_id,"receiver_id":msg.receiver_id,
                        "msg_date":msg.datetime_sent.strftime("%Y/%m/%d/%H/%M/%S/%f"),"msg_content":msg.content}
                message_list.append(m)

            return Response(message_list, status=status.HTTP_200_OK)
        elif request.method == "POST":
            data = request.data
            if type(data) is str:
                data = ast.literal_eval(data)

            #save messages
            messages = data["messages"]
            msg_ids = []

            for msg in messages:
                message = Message(sender_id=request.user.id, receiver_id=msg['receiver_id'], content=msg['msg_content'], status="received",
                                  datetime_sent=pytz.timezone("UTC").localize(datetime.strptime(msg['msg_date'], '%Y/%m/%d/%H/%M/%S/%f')))
                message.save()
                msg_ids.append({"local_id":msg['local_id'],"global_id":message.id})

            #send an email notification
            #receiver = User.objects.get(id=messages[0]['receiver_id'])
            #mail.send(subject=_('[Tripalocal] ') + request.user.first_name + _(' has sent you messages'), message='',
            #            sender=_('Tripalocal <') + Aliases.objects.filter(destination__contains=request.user.email)[0].mail + '>',
            #            recipients = [Aliases.objects.filter(destination__contains=receiver.email)[0].mail], #fail_silently=False,
            #            priority='now',
            #            html_message=loader.render_to_string('app/email_new_messages.html', 
            #                                                    {}))

            receiver = RegisteredUser.objects.get(user_id=messages[0]['receiver_id'])
            receiver_phone_num = receiver.phone_number
            sender_name = request.user.first_name

            if receiver_phone_num:
                sms_content = ""
                for msg in messages:
                    sms_content += msg['msg_content']
                    sms_content += ".\n"

                if len(sms_content) > 140:
                    sms_content = sms_content[:140]
                sms_header = _('%s' % MESSAGE_NOTIFY).format(sender_name=sender_name)

                send_sms(receiver_phone_num, sms_header + '\n' + sms_content)

            return Response(msg_ids, status=status.HTTP_200_OK)

    except Exception as err:
        #TODO
        return Response({"error":err}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication, BasicAuthentication))#))#,
@permission_classes((IsAuthenticated,))
def service_message_list(request, format=None):
    try:
        cursor = connections['default'].cursor()
        count = cursor.execute('select distinct sender_id from app_message where receiver_id=%s',[request.user.id])
        if count > 1:
            # set @num := 0;
            messages = Message.objects.raw('select id, datetime_sent, x.sender as sender_id, receiver_id, content from (select id, datetime_sent, receiver_id, content, @num := if(@sender_id = sender_id, @num + 1, 1) as row_number, @sender_id := sender_id as sender from app_message where receiver_id=%s order by sender_id, datetime_sent desc) as x where x.row_number =1 order by sender_id',
                                            [request.user.id])
        else:
            messages = Message.objects.raw('select * from app_message where receiver_id=%s order by datetime_sent desc limit 1',
                                           [request.user.id])
        len(list(messages))
        message_list = []
        for msg in messages:
            sender = User.objects.get(id=msg.sender_id)
            m = {"id":msg.id,"sender_id":msg.sender_id,
                    "msg_date":msg.datetime_sent.strftime("%Y/%m/%d/%H/%M/%S/%f"),"msg_content":msg.content,
                    "sender_name":sender.first_name, "sender_image":sender.registereduser.image_url}
            message_list.append(m)

        return Response(message_list, status=status.HTTP_200_OK)
    except Exception as err:
        #TODO
        return Response({"error":err}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes((BasicAuthentication,))#, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def update_files(request, format=None):
    try:
        if not request.user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)

        data = request.data
        user_email = data['user_email']
        tripalocal_email = data['tripalocal_email']

        with open('/etc/postfix/canonical', 'a') as f:
            f.write(user_email + " " + tripalocal_email + "\n")
            f.close()

        subprocess.Popen(['sudo','postmap','/etc/postfix/canonical'])
    
        with open('/etc/postgrey/whitelist_recipients.local', 'a') as f:
            f.write(tripalocal_email + "\n")
            f.close()
    except Exception as err:
        #TODO
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"error":err})
    return Response(status=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes((SessionAuthentication, BasicAuthentication,))#, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def service_email(request, format=None):
    try:
        data = request.data
        start_date = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(data['start_date'].strip(), "%Y/%m/%d"))
        exps = AbstractExperience.objects.filter(start_datetime__gte = start_date).filter(status__iexact="Listed")
        hosts = []
        exp_urls = []

        for exp in exps:
            host = get_host(exp)
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

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))# SessionAuthentication, BasicAuthentication))
def service_pageview(request):
    if not request.is_ajax():
        return HttpResponseNotAllowed(['POST'])

    try:
        data = request.POST
        update_pageview_statistics(data['user_id'], data['experience_id'], data['length'])
        response={'success':True}
    except Exception as err:
        response={'success':False}
    return HttpResponse(json.dumps(response),content_type="application/json")

@api_view(['POST'])
@csrf_exempt
def service_update_session(request):
    if not request.is_ajax():
        return HttpResponseNotAllowed(['POST'])

    try:
        data = request.POST
        for key, value in data.items():
            request.session[key] = value
        response={'success':True}
    except Exception as err:
        response={'success':False}
    return HttpResponse(json.dumps(response),content_type="application/json")

@api_view(['GET'])
@csrf_exempt
def service_weather(request):
    try:
        data = request.GET
        #debug print(data)
        response = get_weather(data['lat'], data['lon'], data['time'])
        #debug print(response)
    except Exception as err:
        response = { 'success': False }
    return JsonResponse(response)
        