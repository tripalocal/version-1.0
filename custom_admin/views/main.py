from django.views.generic.edit import FormMixin
from django.views.generic import ListView
from django.http import Http404
from django.utils.decorators import method_decorator

from app.decorators import ajax_form_validate
from app.base import AjaxDisptcherProcessorMixin
from app.utils import MailSupportMixin
from experiences.models import Booking, Experience
from custom_admin.views.base import BookingInfoMixin
from custom_admin.forms import BookingForm, ExperienceUploadForm
from custom_admin.views.base import StatusGenerator
from custom_admin.mail import MailService

class AdminCommonOperation(object):

    @method_decorator(ajax_form_validate(form_class=BookingForm))
    def post(self, request, **kwargs):
        return self._process_request_with_general_return(request, model_class=Booking, **kwargs)

    def _manipulate_multi_change_statuses(self, request, booking_list, **kwargs):
        booking_list= list(booking_list)
        for booking in booking_list:
            booking.change_status(new_status=kwargs['form'].cleaned_data['status'])
        return {'id':[booking.id for booking in booking_list]}

class ExperienceView(AjaxDisptcherProcessorMixin, FormMixin, ListView):
    model = Experience
    template_name = 'custom_admin/experiences.html'
    context_object_name = 'experience_list'
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super(ExperienceView, self).get_context_data(**kwargs)
        for exp in context['experience_list']:
            exp.get_experience_i18n_info()
        return context

    @method_decorator(ajax_form_validate(form_class=ExperienceUploadForm))
    def post(self, request, **kwargs):
        return self._process_request_with_general_return(request, model_class=Experience, **kwargs)

    def _manipulate_post_status(self, request, experience, **kwargs):
        experience.change_status(kwargs['form'].cleaned_data['status'])

class BookingView(AjaxDisptcherProcessorMixin, BookingInfoMixin, MailSupportMixin, AdminCommonOperation, ListView):
    model = Booking
    template_name = 'custom_admin/bookings.html'
    form_class = BookingForm
    context_object_name = 'booking_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(BookingView, self).get_context_data(**kwargs)
        context['form'] = self.form_class()
        return context

    def _manipulate_upload_review(self, request, booking, **kwargs):
        booking.upload_review(rate=kwargs['form'].cleaned_data['rate'], review=kwargs['form'].cleaned_data['review'])
        booking_list = [booking]
        status_generator = StatusGenerator(booking_list)
        status_generator.generate_status_description()
        return {'status_description': booking_list[0].status_description, 'id':booking_list[0].id, 'colour':booking_list[0].colour, 'actions': booking_list[0].actions}

    def _manipulate_change_time(self, request, booking, **kwargs):
        new_datetime = booking.change_time(new_date=kwargs['form'].cleaned_data['new_date'], new_time=kwargs['form'].cleaned_data['new_time'])
        return {'new_datetime': new_datetime.strftime("%d %b %Y %H:%M"), 'id':booking.id}

    def _manipulate_change_status(self, request, booking, **kwargs):
        new_status = booking.change_status(new_status=kwargs['form'].cleaned_data['status'])
        booking_list = [booking]
        status_generator = StatusGenerator(booking_list)
        status_generator.generate_status_description()
        return {'status_description': booking_list[0].status_description, 'new_status': new_status, 'id':booking.id, 'actions': booking_list[0].actions}

    def _manipulate_send_mail(self, request, booking_list, **kwargs):
        recipient = request.POST['recipient']
        booking_list = list(booking_list)
        mail_service = MailService()
        for booking in booking_list:
            booking_status = booking.status
            mail_service.set_mail_info(booking)
            send_mail = None
            if recipient == 'host':
                if booking_status == 'requested' or booking_status == 'paid':
                    mail_service.send_notification_email_to_host()
                elif booking_status == 'accepted':
                    mail_service.send_confirmation_email_to_host()
            elif recipient == 'guest':
                if booking_status == 'requested' or booking_status == 'paid':
                    mail_service.send_notification_email_to_guest()
                elif booking_status == 'accepted':
                    mail_service.send_confirmation_email_to_guest()
            else:
                raise Http404('Wrong request parameter.')

class BookingArchiveView(AjaxDisptcherProcessorMixin, BookingInfoMixin, AdminCommonOperation, ListView):
    model = Booking
    template_name = 'custom_admin/booking-archives.html'
    form_class = BookingForm
    context_object_name = 'booking_list'
    paginate_by = 10

class PaymentView(BookingInfoMixin, ListView):
    model = Booking
    template_name = 'custom_admin/payment.html'
    context_object_name = 'booking_list'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(PaymentView, self).get_context_data(**kwargs)
        for booking in context['booking_list']:
            booking.attach_guest_price()
        return context