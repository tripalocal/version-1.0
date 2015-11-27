from datetime import datetime, timezone, timedelta

from experiences.models import Booking, Review
from django.utils.timezone import localtime
from Tripalocal_V1 import settings

class BookingInfoMixin(object):
    def get_context_data(self, **kwargs):
        context = super(BookingInfoMixin, self).get_context_data(**kwargs)
        # Add booking info to the context.
        booking_list = context['booking_list']
        for booking in booking_list:
            booking.experience.title = booking.experience.get_information(settings.LANGUAGES[0][0]).title
        status_generator = StatusGenerator(booking_list)
        status_generator.generate_status_description()
        context['booking_list'] = booking_list
        # Add user name to the context.
        context['user_name'] = self.request.user.username
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
    def __init__(self, booking_list=None):
        self.booking_list = booking_list
        self.now_time = datetime.now(timezone.utc)

    def generate_status_description(self):
        if not self.booking_list:
            return None
        for booking in self.booking_list:
            self.now_time = datetime.now(timezone.utc)
            if booking.status == 'rejected' or booking.status == 'accepted' or booking.status == 'requested' or booking.status == 'no_show' or booking.status == 'paid':
                manipulate_function_name = '_manipulate_' + booking.status + '_booking'
                manipulate_function = getattr(self, manipulate_function_name)
                manipulate_function(booking)
                booking.datetime = localtime(booking.datetime)
                booking.datetime = booking.datetime.strftime("%d %b %Y %H:%M")
            else:
                temp = booking.status.split('_')
                previous_status = ''
                for ele in temp:
                    if ele != 'archived':
                        previous_status = previous_status + '_' + ele
                previous_status = previous_status[1:]

                manipulate_function_name = '_manipulate_' + previous_status + '_booking'
                manipulate_function = getattr(self, manipulate_function_name)
                manipulate_function(booking)
                booking.datetime = localtime(booking.datetime)
                booking.datetime = booking.datetime.strftime("%d %b %Y %H:%M")

    def _manipulate_requested_booking(self, booking):
        time_after_booking_submission = self.now_time - booking.submitted_datetime
        # The submission time has been beyond the current time, which means there's an
        # internal error.
        if (time_after_booking_submission.days < 0):
            booking.status_description = 'Server external error.'
            booking.colour = 'red'
            booking.actions = []
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
            booking.actions = []
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
        booking.status_description = ''
        booking.colour = ''
        booking.actions = []

    def _manipulate_paid_booking(self, booking):
        self._manipulate_requested_booking(booking)

    #def _manipulate_draft_booking(self, booking):
    #    self._manipulate_requested_booking(booking)