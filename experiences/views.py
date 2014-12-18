from django.shortcuts import render, get_object_or_404, render_to_response
from django.db.models import Q
from experiences.models import Experience, WhatsIncluded, Photo
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.contrib.formtools.wizard.views import SessionWizardView
from experiences.forms import ExperienceForm, ExperienceCalendarForm, BookingForm, BookingConfirmationForm, CreateExperienceForm
from datetime import *
import pytz, string, os, json, math
from django.core.mail import send_mail
from django.template import RequestContext, loader
from experiences.models import Experience, Booking, Payment
from django.contrib.auth.models import User
from Tripalocal_V1 import settings
from decimal import Decimal
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile, File
from django.contrib import messages
from tripalocal_messages.models import Aliases
from experiences.models import Review, Photo, RegisteredUser, Coupon
from app.forms import SubscriptionForm
from mixpanel import Mixpanel

def experience_fee_calculator(price):
    if type(price)==int or type(price) == float:
        return round(price*(1.00+settings.COMMISSION_PERCENT)*(1.00+settings.STRIPE_PRICE_PERCENT) + settings.STRIPE_PRICE_FIXED,2)

    return price

class ExperienceListView(ListView):
    template_name = 'experience_list.html'
    #paginate_by = 9
    #context_object_name = 'experience_list'

    def get_queryset(self):
#        if self.request.user.is_superuser:
            return Experience.objects.all#()
#        else:
#            return self.request.user.experience_hosts.all()

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
            
            return render(request, 'experience_booking_confirmation.html', 
                          {'form': form, #'eid':self.object.id, 
                           'experience': experience, 
                           'guest_number':form.data['guest_number'],
                           'date':form.data['date'],
                           'time':form.data['time'],
                           'subtotal_price':round(float(experience.price)*float(form.data['guest_number'])*(1.00+settings.COMMISSION_PERCENT),2),
                           'service_fee':round(float(experience.price)*float(form.data['guest_number'])*(1.00+settings.COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                           'total_price': experience_fee_calculator(float(experience.price)*float(form.data['guest_number']))
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
            # experience already expired
            context['expired'] = True
            return context

        while (sdt < datetime.utcnow().replace(tzinfo=pytz.UTC)):     

            if experience.repeat_cycle == "Hourly" :
                sdt += timedelta(hours=experience.repeat_frequency)
            elif experience.repeat_cycle == "Daily" :
                sdt += timedelta(days=experience.repeat_frequency)
            elif experience.repeat_cycle == "Weekly" :
                sdt += timedelta(weeks=experience.repeat_frequency)
            #else :
                #TODO

        while (sdt <= experience.end_datetime):
            #check if the date is blocked
            blocked = False
            for blk in experience.blockouttimeperiod_set.filter(experience_id=experience.id) :
                if blk.start_date <= sdt.date() and sdt.date() <= blk.end_date:
                    blocked = True

            if not blocked:
                i = 0
                for bking in experience.booking_set.filter(experience_id=experience.id) :
                    if bking.datetime == sdt and bking.status.lower() != "rejected":
                        i += bking.guest_number

                if i < experience.guest_number_max :
                    sdt_local = sdt.astimezone(local_timezone)
                    if experience.repeat_cycle != "Hourly" or (sdt_local.time().hour > 7 and sdt_local.time().hour <22):
                        dict = {'available_seat': experience.guest_number_max - i, 
                                'date_string': sdt_local.strftime("%d/%m/%Y"), 
                                'time_string': sdt_local.strftime("%H:%M"), 
                                'datetime': sdt_local}
                        available_options.append(dict)

                        if sdt.astimezone(local_timezone).date() != last_sdt.astimezone(local_timezone).date():
                            new_date = ((sdt_local.strftime("%d/%m/%Y"),
                                             sdt_local.strftime("%d/%m/%Y")),)
                            available_date += new_date
                            last_sdt = sdt
            
            if experience.repeat_cycle == "Hourly" :
                sdt += timedelta(hours=experience.repeat_frequency)
            elif experience.repeat_cycle == "Daily" :
                sdt += timedelta(days=experience.repeat_frequency)
            elif experience.repeat_cycle == "Weekly" :
                sdt += timedelta(weeks=experience.repeat_frequency)
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

        return context

class ExperienceWizard(SessionWizardView):
    #template_name = 'add_experience.html'
    #form_list = [ExperienceForm, ExperienceCalendarForm]

    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        return render_to_response('experience_confirmation.html', {
            'form_list': form_list,
        })

FORMS = [("experience", ExperienceForm),
         ("calendar", ExperienceCalendarForm)]

TEMPLATES = {"experience": "add_experience.html",
             "calendar": "add_experience_calendar.html"}

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

        if 'Refresh' in request.POST:
            #get coupon information
            wrong_promo_code = False
            code = form.data['promo_code']
            coupons = Coupon.objects.filter(promo_code = code,
                                            end_datetime__gt = datetime.utcnow().replace(tzinfo=pytz.UTC),
                                            start_datetime__lt = datetime.utcnow().replace(tzinfo=pytz.UTC))
            if not len(coupons):
                coupon = Coupon()
                wrong_promo_code = True
            else:
                coupon = coupons[0]

            #prevent the form from being submitted
            form.add_error("coupon_extra_information","coupon_extra_information")

            experience = Experience.objects.get(id=form.data['experience_id'])

            mp = Mixpanel(settings.MIXPANEL_TOKEN)
            mp.track(request.user.email, 'Clicked on "Refresh"')
            return render_to_response('experience_booking_confirmation.html', {'form': form, 
                                                                           'wrong_promo_code':wrong_promo_code,
                                                                           'coupon':coupon,
                                                                           'experience': experience, 
                                                                           'guest_number':form.data['guest_number'],
                                                                           'date':form.data['date'],
                                                                           'time':form.data['time'],
                                                                           'subtotal_price':round(float(experience.price)*float(form.data['guest_number'])*(1.00+settings.COMMISSION_PERCENT),2),
                                                                           'service_fee':round(float(experience.price)*float(form.data['guest_number'])*(1.00+settings.COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                                                                           'total_price': experience_fee_calculator(float(experience.price)*float(form.data['guest_number']))}, context)

        else:
            #submit the form
            display_error = True
            if form.is_valid():
                return experience_booking_successful(request, 
                                                     Experience.objects.get(id=form.data['experience_id']), 
                                                     int(form.data['guest_number']),
                                                     datetime.strptime(form.data['date'] + " " + form.data['time'], "%Y-%m-%d %H:%M"))
            
            else:
                experience = Experience.objects.get(id=form.data['experience_id'])
                return render_to_response('experience_booking_confirmation.html', {'form': form, 
                                                                           'display_error':display_error,
                                                                           'experience': experience, 
                                                                           'guest_number':form.data['guest_number'],
                                                                           'date':form.data['date'],
                                                                           'time':form.data['time'],
                                                                           'subtotal_price':round(float(experience.price)*float(form.data['guest_number'])*(1.00+settings.COMMISSION_PERCENT),2),
                                                                           'service_fee':round(float(experience.price)*float(form.data['guest_number'])*(1.00+settings.COMMISSION_PERCENT)*settings.STRIPE_PRICE_PERCENT+settings.STRIPE_PRICE_FIXED,2),
                                                                           'total_price': experience_fee_calculator(float(experience.price)*float(form.data['guest_number']))}, context)
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
    photos={}
    display_error = False

    if not request.user.is_authenticated():
        return HttpResponseRedirect("/accounts/login/")

    if id:
        experience = get_object_or_404(Experience, pk=id)
        if len(experience.whatsincluded_set.filter(item="Food")) > 0: 
            if experience.whatsincluded_set.filter(item="Food")[0].included:
                included_food = "Yes" 
            else:
                included_food = "No" 
            include_food_detail = experience.whatsincluded_set.filter(item="Food")[0].details
        else:
            included_food = "No"
            include_food_detail = None
        
        if len(experience.whatsincluded_set.filter(item="Ticket")) >0:
            if experience.whatsincluded_set.filter(item="Ticket")[0].included:
                included_ticket = "Yes"
            else:
                included_ticket = "No"
            included_ticket_detail = experience.whatsincluded_set.filter(item="Ticket")[0].details
        else:
            included_ticket = "No"
            included_ticket_detail = None

        if len(experience.whatsincluded_set.filter(item="Transport")) >0:
            if experience.whatsincluded_set.filter(item="Transport")[0].included:
                included_transport = "Yes"
            else:
                included_transport = "No"
            included_transport_detail = experience.whatsincluded_set.filter(item="Transport")[0].details
        else:
            included_transport = "No"
            included_transport_detail = None

        for i in range(1,6):
            if len(experience.photo_set.filter(name__startswith='experience'+str(id)+'_'+str(i)))>0:
                photo = experience.photo_set.filter(name__startswith='experience'+str(id)+'_'+str(i))[0]
                photos['experience_photo_'+str(i)] = SimpleUploadedFile(settings.MEDIA_ROOT+'/'+photo.directory+photo.name, 
                                                                             File(open(settings.MEDIA_ROOT+'/'+photo.directory+photo.name, 'rb')).read())
            #else:
            #    photos['experience'+str(id)+'_'+str(i)] = None

        data = {"start_datetime":experience.start_datetime,
            "end_datetime":experience.end_datetime,
            "repeat_cycle":experience.repeat_cycle,
            "repeat_frequency":experience.repeat_frequency,
            "title":experience.title,
            "summary":experience.description,
            "guest_number_min":experience.guest_number_min,
            "guest_number_max":experience.guest_number_max,
            "price":experience.price,
            "price_with_booking_fee":experience.price*Decimal.from_float(1.00+settings.COMMISSION_PERCENT),
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
            "meetup_spot":experience.meetup_spot
        }
        #if experience.hosts.all()[0] != request.user:
        #    return HttpResponseForbidden()
    else:
        experience = Experience()

    if request.method == 'POST':
        form = CreateExperienceForm(request.POST, request.FILES)
        display_error = True

        if form.is_valid():
            if not id:
                experience = Experience(start_datetime = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['start_datetime'], "%Y-%m-%d %H:%M")),
                                        end_datetime = pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(form.data['end_datetime'], "%Y-%m-%d %H:%M")),
                                        repeat_cycle = form.data['repeat_cycle'],
                                        repeat_frequency = form.data['repeat_frequency'],
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
                                        status = 'Listed'
                                        )
            
            else:
                experience.start_datetime = datetime.strptime(form.data['start_datetime'], "%Y-%m-%d %H:%M")
                experience.end_datetime = datetime.strptime(form.data['end_datetime'], "%Y-%m-%d %H:%M")
                experience.repeat_cycle = form.data['repeat_cycle']
                experience.repeat_frequency = form.data['repeat_frequency']
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
            
            experience.save()
            
            #save images
            dirname = settings.MEDIA_ROOT + '/experiences/' + str(experience.id) + '/'
            if not os.path.isdir(dirname):
                os.mkdir(dirname)

            count = 0
            for index in range (1,6):
                if 'experience_photo_'+str(index) in request.FILES:
                    count += 1 #count does not necessarily equal index
                    name, extension = os.path.splitext(request.FILES['experience_photo_'+str(index)].name)
                    extension = extension.lower();
                    if extension in ('.bmp', '.png', '.jpeg', '.jpg') :
                        filename = 'experience' + str(experience.id) + '_' + str(count) + extension
                        for chunk in request.FILES['experience_photo_'+str(index)].chunks():
                            destination = open(dirname + filename, 'wb+')               
                            destination.write(chunk)
                            destination.close()
                        if not len(experience.photo_set.filter(name__startswith=filename))>0:
                            photo = Photo(name = filename, directory = 'experiences/' + str(experience.id) + '/', 
                                          image = 'experiences/' + str(experience.id) + '/' + filename, experience = experience)
                            photo.save()


            #add the user to the host list
            if not id:
                user = User.objects.get(id=request.user.id)
                experience.hosts.add(user)

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

            return HttpResponseRedirect('/experiencelist/') 
            
    else:
        form = CreateExperienceForm(data=data, files=photos)

    return render_to_response('create_experience.html', {'form': form, 'display_error':display_error}, context)

def booking_accepted(request, id=None):
    #TODO
    # respond within 48 hours?


    accepted = request.GET.get('accept')
    form = SubscriptionForm()

    if id and accepted:
        booking = get_object_or_404(Booking, pk=id)
        if booking.status.lower() == "accepted":
            # the host already accepted the booking
            messages.add_message(request, messages.INFO, 'The booking request has already been accepted.')
            return render(request, 'app/index.html', {'form': form})

        if booking.status.lower() == "rejected":
            # the host/guest already rejected/cancelled the booking
            messages.add_message(request, messages.INFO, 'The booking request has already been rejected.')
            return render(request, 'app/index.html', {'form': form})

        experience = Experience.objects.get(id=booking.experience_id)
        user = User.objects.get(id = booking.user_id)

        if accepted == "yes":
            booking.status = "accepted"
            booking.save()
            #send an email to the traveller
            send_mail('[Tripalocal] Booking confirmed', '', 
                      'Tripalocal <' + Aliases.objects.filter(destination__contains=experience.hosts.all()[0].email)[0].mail + '>',
                        [Aliases.objects.filter(destination__contains=User.objects.get(id=booking.user_id).email)[0].mail], 
                        fail_silently=False, 
                        html_message=loader.render_to_string('email_booking_confirmed_traveler.html',
                                                                {'experience': experience,
                                                                    'booking':booking,
                                                                    'user':user,
                                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))
            
            #send an email to the host
            send_mail('[Tripalocal] Booking confirmed', '', 
                      'Tripalocal <' + Aliases.objects.filter(destination__contains=User.objects.get(id=booking.user_id).email)[0].mail + '>',
                        [Aliases.objects.filter(destination__contains=experience.hosts.all()[0].email)[0].mail], 
                        fail_silently=False, 
                        html_message=loader.render_to_string('email_booking_confirmed_host.html',
                                                                {'experience': experience,
                                                                    'booking':booking,
                                                                    'user':user,
                                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))
            return render(request, 'email_booking_confirmed_host.html',
                          {'experience': experience,
                            'booking':booking,
                            'user':user,
                            'experience_url':'http://' + settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                            'webpage':True})
        
        elif accepted == "no":         
            payment = Payment.objects.get(booking_id=booking.id)

            extra_fee = 0.00
            if len(booking.coupon_extra_information) > 0:
                extra = json.loads(booking.coupon_extra_information)
                if type(extra["extra_fee"]) == int or type(extra["extra_fee"]) == float:
                    extra_fee = extra["extra_fee"]
            
            refund_amount = float(experience.price)*float(booking.guest_number)*(1+settings.COMMISSION_PERCENT)

            if extra_fee < 0:
                refund_amount = refund_amount + extra_fee

            success, response = payment.refund(charge_id=payment.charge_id, amount=int(refund_amount*100))
            if success:
                booking.status = "rejected"
                #send an email to the traveller
                send_mail('[Tripalocal] Your experience is cancelled', '', 
                          'Tripalocal <' + Aliases.objects.filter(destination__contains=experience.hosts.all()[0].email)[0].mail + '>',
                            [Aliases.objects.filter(destination__contains=User.objects.get(id=booking.user_id).email)[0].mail],
                            fail_silently=False, 
                            html_message=loader.render_to_string('email_booking_cancelled_traveler.html',
                                                                 {'experience': experience,
                                                                  'booking':booking,
                                                                  'user':user,
                                                                  'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))
                #send an email to the host
                send_mail('[Tripalocal] Cancellation confirmed', '', 
                          'Tripalocal <' + Aliases.objects.filter(destination__contains=User.objects.get(id=booking.user_id).email)[0].mail + '>',
                            [Aliases.objects.filter(destination__contains=experience.hosts.all()[0].email)[0].mail], 
                            fail_silently=False, 
                            html_message=loader.render_to_string('email_booking_cancelled_host.html',
                                                                {'experience': experience,
                                                                 'booking':booking,
                                                                 'user':user,
                                                                 'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id)}))
                return render(request, 'email_booking_cancelled_host.html',
                               {'experience': experience,
                                'booking':booking,
                                'user':user,
                                'experience_url': 'http://' + settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                'webpage':True})
            #else:
                #TODO
                #ask the host to try again, or contact us
                messages.add_message(request, messages.INFO, 'Please try to cancel the request later. Contact us if this happens again. Sorry for the inconvenience.')
                return render(request, 'app/index.html', {'form': form})

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
        BGImageURL = photoList[0].image
    return BGImageURL

def ByCityExperienceListView(request, city):
    template = loader.get_template('search_result.html')

    # Add all experiences that belong to the specified city to a new list
    # alongside a list with all the number of reviews
    experienceList = Experience.objects.filter(city__iexact=city)
    rateList = []
    cityExperienceList = []
    cityExperienceReviewList = []
    formattedTitleList = []
    BGImageURLList = []
    profileImageURLList = []

    i = 0
    while i < len(experienceList):
        experience = experienceList[i]
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
            if (len(experience.title) > 50):
                formattedTitleList.insert(counter, experience.title[:47] + "...")
            else:
                formattedTitleList.insert(counter, experience.title)
        i += 1

    mp = Mixpanel(settings.MIXPANEL_TOKEN)
    sydneySelected = False
    if (city == "sydney"):
        sydneySelected = True

    if request.user.is_authenticated():
        mp.track(request.user.email,"Viewed " + city.title() + " search page");
    else:
        mp.track("","Viewed " + city.title() + " search page");

    context = RequestContext(request, {
        'city' : city.title(),
        'cityExperienceList' : zip(cityExperienceList, cityExperienceReviewList, formattedTitleList, BGImageURLList, profileImageURLList),
        'sydneySelected' : sydneySelected,
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
