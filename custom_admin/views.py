from django.views.generic import ListView
from django.views.generic.edit import FormMixin
from custom_admin.forms import ChangeTimeForm, UploadReviewForm

from experiences.models import Booking,Experience
from experiences.models import Review
from django.contrib.auth.models import User
from django.template import RequestContext, loader
from datetime import datetime,timezone,timedelta
from django.views.generic.edit import FormView
from Tripalocal_V1 import settings
from django.shortcuts import render
from django.http import HttpResponseRedirect

from post_office import mail
from tripalocal_messages.models import Aliases
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test

class PaymentView(ListView):
    model = Booking
    template_name = 'custom_admin/payment.html'
    context_object_name = 'booking_list'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(PaymentView, self).get_context_data(**kwargs)
        g = StatusGenerator(context['booking_list'])
        g.generate_status_description()
        change_status_notification_key = 'status'
        _calculte_price(context['booking_list'])
        context['user_name'] = self.request.user.username        
        if change_status_notification_key in  self.request.GET:
            context[change_status_notification_key] = self.request.GET[change_status_notification_key]
        else:
            context[change_status_notification_key] = 'none'
        return context



class ArchiveView(ListView):
    model = Booking
    template_name = 'custom_admin/archives.html'
    context_object_name = 'booking_list'
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(ArchiveView, self).get_context_data(**kwargs)
        g = StatusGenerator(context['booking_list'])
        g.generate_status_description()
        context['user_name'] = self.request.user.username        
        return context

class BookingView(ListView, FormMixin):
    model = Booking
    template_name = 'custom_admin/bookings.html'
    context_object_name = 'booking_list'
    form_class = ChangeTimeForm
    second_form_class = UploadReviewForm

    def post(self, request, **kwargs):
        if 'new_date_day' in request.POST:
            form = ChangeTimeForm(request.POST)
            # check whether it's valid:
            status = ''
            if form.is_valid():
                cleaned_time = form.cleaned_data['new_time'].split(":")
                cleaned_date = form.cleaned_data['new_date']
            
                if cleaned_time.__len__() != 2 or cleaned_time[0].isdigit() == False or cleaned_time[1].isdigit() == False:
                    status = 'failed'
                else:
                    new_time = _format_time(cleaned_date, cleaned_time)
                    conflict = _check_availiability(kwargs['booking_id'], new_time)
                    if conflict:
                        status = 'failed'
                    else:
                        new_booking = Booking.objects.get(id = kwargs['booking_id'])
                        new_booking.datetime = new_time
                        new_booking.save()
                        status = 'success'
            else:
                status = 'failed'
            return HttpResponseRedirect('/custom_admin/?status=%s' % (status))
        
        elif 'review' in request.POST:
            form = UploadReviewForm(request.POST)
            # check whether it's valid:
            status = ''
            if form.is_valid():
                cleaned_review = form.cleaned_data['review']
                cleaned_rate = form.cleaned_data['rate']
                booking = Booking.objects.get(id = kwargs['booking_id'])
                experience_id = booking.experience_id
                user_id = booking.user_id
                new_review = Review(experience_id = int(experience_id), user_id = int(user_id), comment = cleaned_review, rate = int(cleaned_rate), datetime = datetime.now())
                new_review.save()
                status = 'success'  
            else:
                status = 'failed'
            return HttpResponseRedirect('/custom_admin/?status=%s' % (status))
        

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(BookingView, self).get_context_data(**kwargs)
    #    context['form'] = self.get_form(self.form_class)
        if 'form' not in context:
            context['form'] = self.form_class()
        if 'form2' not in context:
            context['form2'] = self.second_form_class()

        context['user_name'] = self.request.user.username
        g = StatusGenerator(context['booking_list'])
        g.generate_status_description()
        change_status_notification_key = 'status'
        if change_status_notification_key in  self.request.GET:
            context[change_status_notification_key] = self.request.GET[change_status_notification_key]
        else:
            context[change_status_notification_key] = 'none'
        

        return context

    
"""
It contains a page representation logic. In other word, it indicates how the status 
information of each booking in the web page will be displayed. 
Attributes:
        booking_list : (List)Booking  - It is a list of the Booking model retrieved 
                                        from the database.
        now_time : datetime - It shows the current time.    
"""
class StatusGenerator:

    """
    It's the constructor of this class.
    Parameters:
        booking_list : (List)Booking  - It is a list of the Booking model retrieved 
                                        from the database.
    """    
    def __init__(self, booking_list):
        self.booking_list = booking_list
        self.now_time = datetime.now(timezone.utc)

    def generate_status_description(self):
        for booking in self.booking_list:
            self.now_time = datetime.now(timezone.utc)
            if booking.status == 'rejected' or booking.status == 'accepted' or booking.status == 'requested' or booking.status == 'no_show':
                manipulate_function_name = '_manipulate_' + booking.status + '_booking'
                manipulate_function = getattr(self, manipulate_function_name)
                manipulate_function(booking)
                booking.datetime = booking.datetime.strftime("%d %b %Y %H:%I")
            else:
                previous_status = booking.status.split('_')[0]
                manipulate_function_name = '_manipulate_' + previous_status + '_booking'  
                manipulate_function = getattr(self, manipulate_function_name)
                manipulate_function(booking)
                booking.datetime = booking.datetime.strftime("%d %b %Y %H:%I")

    def _manipulate_requested_booking(self, booking):
        time_after_booking_submission = self.now_time - booking.submitted_datetime
        # The submission time has been beyond the current time, which means there's an
        # internal error.
        if (time_after_booking_submission.days < 0):
            booking.status_description = 'Server external error.'
            booking.colour = 'red'

        # The booking hasn't been manipulated by anyone yet, and the time after the 
        # submission is greater than 12 hours.
        elif (time_after_booking_submission.days == 0 and time_after_booking_submission.seconds > 43200): 
            booking.status_description = 'Travellers sent the request.' + str(round(float(time_after_booking_submission.seconds/3600),1)) + ' hours ago.'
            booking.colour = 'red'
            booking.actions = ['Cancel booking', 'Change time'] 
        # The booking hasn't been manipulated by anyone yet, and the time after the 
        # submission is less than 12 hours.
        elif (time_after_booking_submission.days == 0 and time_after_booking_submission.seconds < 43200): 
            booking.status_description = 'Travellers sent the request.' + str(round(float(time_after_booking_submission.seconds/3600),1)) + ' hours ago.'
            booking.colour = 'black'
            booking.actions = ['Cancel booking', 'Change time']
        # The booking hasn't been manipulated by anyone yet, and the time after the 
        # submission is greater than 24 hours.
        elif (time_after_booking_submission.days > 0):  
            booking.status_description = 'The request has been expired.'
            booking.colour = 'grey'
            booking.actions = ['Cancel booking', 'Change time']

    def _manipulate_accepted_booking(self, booking):
        time_after_experience = self.now_time - booking.datetime
        # Check whether a review has been received.
        review = Review.objects.filter(user_id = booking.user.id).filter(experience_id = booking.experience.id)
        if (review.__len__() == 1):
            time_after_review = self.now_time - review[0].datetime
            booking.status_description = 'The review has been received ' + str(time_after_review.days) + ' days and ' + str(round(float(time_after_review.seconds/3600),1)) + ' hours ago.' 
            booking.colour = 'black'
        # If the booking is accepted and there has been 24 hours after the experience
        # when the email has been sent.
        elif (time_after_experience.days > 0):
            booking.status_description = 'The review email has been sent ' + str(time_after_experience.days) + ' days and ' + str(round(float(time_after_experience.seconds/3600),1)) + ' hours ago.'
            booking.colour = 'black'
            booking.actions = ['Mark as no show', 'Upload review']    

        else:
            booking.status_description = 'The host has accepted the booking.' 
            booking.colour = 'black'    
            booking.actions = ['Mark as no show', 'Change time']    

    def _manipulate_rejected_booking(self, booking):
        booking.status_description = 'Cancelled'
        booking.colour = 'grey'
        booking.actions = ['Reopen booking', 'Change time']

    def _manipulate_no_show_booking(self, booking):
        booking.status_description = 'No show'
        booking.colour = 'grey'
        booking.actions = []       

    def _manipulate_deleted_booking(self, booking):
        pass

    def _manipulate_paid_booking(self, booking):
        self._manipulate_requested_booking(booking)
    def _manipulate_booking_booking(self, booking):
        pass   




def mark_as_no_show(request, **kwargs):
    booking = Booking.objects.get(id = kwargs['booking_id'])
    booking.status = 'no_show'
    booking.save()
    status = 'success'
    return HttpResponseRedirect('/custom_admin/?status=%s' % (status))

def reopen_booking(request, **kwargs):
    booking = Booking.objects.get(id = kwargs['booking_id'])
    booking.status = 'requested'
    booking.save()
    status = 'success'
    return HttpResponseRedirect('/custom_admin/?status=%s' % (status))

def cancel_booking(request, **kwargs):
    booking = Booking.objects.get(id = kwargs['booking_id'])
    booking.status = 'rejected'
    booking.save()
    status = 'success'
    return HttpResponseRedirect('/custom_admin/?status=%s' % (status))

def delete_bookings(request, **kwargs):
    ids_key = 'admin_panel_booking_id_checkbox'
    if ids_key in request.POST:
        chosen_ids = dict(request.POST)['admin_panel_booking_id_checkbox']
        for booking_id in chosen_ids:
            booking_id = int(booking_id)
            booking = Booking.objects.get(id = booking_id)
            booking.status = 'deleted'
            booking.save()
    status = 'success'
    return HttpResponseRedirect('/custom_admin/?status=%s' % (status))

def archive_bookings(request, **kwargs):
    ids_key = 'admin_panel_booking_id_checkbox'
    if ids_key in request.POST:
        chosen_ids = dict(request.POST)['admin_panel_booking_id_checkbox']
        for booking_id in chosen_ids:
            booking_id = int(booking_id)
            booking = Booking.objects.get(id = booking_id)
            booking.status = booking.status + '_archived'
            booking.save()
    status = 'success'
    return HttpResponseRedirect('/custom_admin/?status=%s' % (status))

def unarchive_bookings(request, **kwargs):
    ids_key = 'admin_panel_booking_id_checkbox'
    if ids_key in request.POST:
        chosen_ids = dict(request.POST)['admin_panel_booking_id_checkbox']
        for booking_id in chosen_ids:
            booking_id = int(booking_id)
            booking = Booking.objects.get(id = booking_id)
            previous_status = booking.status.split('_')[0] 
            booking.status = previous_status
            booking.save()
    status = 'success'
    return HttpResponseRedirect('/custom_admin/?status=%s' % (status))
 


def send_confirmation_email_host(request, **kwargs):
    ids_key = 'admin_panel_booking_id_checkbox'
    all_chosen_key = 'all'
    if ids_key in request.POST:
        chosen_ids = dict(request.POST)['admin_panel_booking_id_checkbox']
        if all_chosen_key in chosen_ids:
            pass
        else: 
            for booking_id in chosen_ids:
                booking_id = int(booking_id)
                booking = Booking.objects.get(id = booking_id)
                experience = Experience.objects.get(id = booking.experience_id)
                guest = User.objects.get(id = booking.user_id)
                host = experience.hosts.all()[0]
                
                if booking.status == 'requested' or booking.status == 'paid':
                    #send an email to the host
                    mail.send(subject = '[Tripalocal] ' + guest.first_name + ' has requested your experience', message='',
                              sender = 'Tripalocal <' + Aliases.objects.filter(destination__contains = guest.email)[0].mail + '>',
                              recipients = [Aliases.objects.filter(destination__contains=host.email)[0].mail], #fail_silently=False,
                              priority = 'now',
                              html_message = loader.render_to_string('experiences/email_booking_requested_host.html', 
                                                                     {'experience': experience,
                                                                      'booking':booking,
                                                                      'user_first_name':guest.first_name,
                                                                      'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                                      'accept_url': settings.DOMAIN_NAME + '/booking/' + str(booking.id) + '?accept=yes',
                                                                      'reject_url': settings.DOMAIN_NAME + '/booking/' + str(booking.id) + '?accept=no',
                                                                      'LANGUAGE':settings.LANGUAGE_CODE}))

                if booking.status == 'accepted':
                    #send an email to the host
                    mail.send(subject='[Tripalocal] Booking confirmed', message='', 
                              sender='Tripalocal <' + Aliases.objects.filter(destination__contains=guest.email)[0].mail + '>',
                              recipients = [Aliases.objects.filter(destination__contains=host.email)[0].mail], 
                              priority='now',  #fail_silently=False, 
                              html_message=loader.render_to_string('experiences/email_booking_confirmed_host.html',
                                                                    {'experience': experience,
                                                                    'booking':booking,
                                                                    'user':guest,
                                                                    'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                                    'LANGUAGE':settings.LANGUAGE_CODE}))


    status = 'success'
    return HttpResponseRedirect('/custom_admin/?status=%s' % (status))
  
def send_confirmation_email_guest(request, **kwargs):
    ids_key = 'admin_panel_booking_id_checkbox'
    all_chosen_key = 'all'
    if ids_key in request.POST:
        chosen_ids = dict(request.POST)['admin_panel_booking_id_checkbox']
        if all_chosen_key in chosen_ids:
            pass
        else: 
            for booking_id in chosen_ids:
                booking_id = int(booking_id)
                booking = Booking.objects.get(id = booking_id)
                experience = Experience.objects.get(id = booking.experience_id)
                guest = User.objects.get(id = booking.user_id)
                host = experience.hosts.all()[0]
                
                if booking.status == 'requested' or booking.status == 'paid':
                    # send an email to the traveler
                    mail.send(subject='[Tripalocal] Your booking request is sent to the host',  message='', 
                              sender='Tripalocal <' + Aliases.objects.filter(destination__contains=host.email)[0].mail + '>',
                              recipients = [Aliases.objects.filter(destination__contains=guest.email)[0].mail], #fail_silently=False,
                              priority='now',
                              html_message=loader.render_to_string('experiences/email_booking_requested_traveler.html',
                                                                     {'experience': experience, 
                                                                      'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                                      'booking':booking,
                                                                      'LANGUAGE':settings.LANGUAGE_CODE}))                    

                if booking.status == 'accepted':
                    # send an email to the traveler
                    mail.send(subject = '[Tripalocal] Booking confirmed', message='', 
                              sender = 'Tripalocal <' + Aliases.objects.filter(destination__contains=host.email)[0].mail + '>',
                              recipients = [Aliases.objects.filter(destination__contains=guest.email)[0].mail], 
                              priority = 'now',  #fail_silently=False, 
                              html_message = loader.render_to_string('experiences/email_booking_confirmed_traveler.html',
                                                                      {'experience': experience,
                                                                      'booking':booking,
                                                                      'user':guest, #not host --> need "my" phone number
                                                                      'experience_url':settings.DOMAIN_NAME + '/experience/' + str(experience.id),
                                                                      'LANGUAGE':settings.LANGUAGE_CODE}))
    status = 'success'
    return HttpResponseRedirect('/custom_admin/?status=%s' % (status))



def superuser_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def _format_time(date_info, time_info):
    return date_info.replace(hour = int(time_info[0]), minute = int(time_info[1]))

def _check_availiability(booking_id, new_datetime):
    changed_booking = Booking.objects.get(id = int(booking_id))
    changed_booking_start = new_datetime
    changed_booking_end = changed_booking_start + timedelta(hours = int(changed_booking.experience.duration))

    host_all_bookings = Booking.objects.filter(user_id = changed_booking.user_id)

    conflict = False
    for host_booking in host_all_bookings:
        host_booking_start = host_booking.datetime 
        host_booking_end = host_booking_start + timedelta(hours = int(host_booking.experience.duration))
        if (changed_booking_start - host_booking_start).total_seconds() > 0 and (changed_booking_start - host_booking_end).total_seconds() < 0:
            conflict = True
        elif (changed_booking_end - host_booking_start).total_seconds() > 0 and (changed_booking_end - host_booking_end).total_seconds() < 0:
            conflict = True
    return conflict

def _calculte_price(booking_list):
    for booking in booking_list:
        host_price = float(booking.experience.price) * float(booking.guest_number)
        full_price = _calculate_full_price(host_price)
        booking.full_price = full_price
        booking.host_price = host_price

def _calculate_full_price(price):
    if type(price)==int or type(price) == float:
        return round(price*(1.00+settings.COMMISSION_PERCENT)*(1.00+settings.STRIPE_PRICE_PERCENT) + settings.STRIPE_PRICE_FIXED,2)