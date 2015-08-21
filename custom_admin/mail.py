from django.template import loader

from tripalocal_messages.models import Aliases
from Tripalocal_V1 import settings
from post_office import mail

class MailService(object):

    def set_mail_info(self, booking):
        self.booking = booking
        self.experience = booking.get_experience()
        self.guest = booking.get_guest()
        self.host = booking.get_hosts()[0]

    def send_notification_email_to_host(self):
        self.subject = '[Tripalocal] ' + self.guest.first_name + ' has requested your experience'
        self.message=''
        self.sender = 'Tripalocal <' + Aliases.objects.filter(destination__contains=self.guest.email)[0].mail + '>'
        self.recipients = [Aliases.objects.filter(destination__contains=self.host.email)[0].mail]
        self.priority = 'now'
        self.html_message = loader.render_to_string('experiences/email_booking_requested_host.html',
                                                                     {'experience': self.experience,
                                                                      'booking':self.booking,
                                                                      'user_first_name':self.guest.first_name,
                                                                      'experience_url':settings.DOMAIN_NAME + '/experience/' + str(self.experience.id),
                                                                      'accept_url': settings.DOMAIN_NAME + '/booking/' + str(self.booking.id) + '?accept=yes',
                                                                      'reject_url': settings.DOMAIN_NAME + '/booking/' + str(self.booking.id) + '?accept=no'})
        self.send_mail()

    def send_confirmation_email_to_host(self):
        self.subject = '[Tripalocal] Booking confirmed'
        self.message=''
        self.sender = 'Tripalocal <' + Aliases.objects.filter(destination__contains=self.guest.email)[0].mail + '>'
        self.recipients = [Aliases.objects.filter(destination__contains=self.host.email)[0].mail]
        self.priority = 'now'
        self.html_message=loader.render_to_string('experiences/email_booking_confirmed_host.html',
                                                        {'experience': self.experience,
                                                        'booking':self.booking,
                                                        'user':self.guest,
                                                        'experience_url':settings.DOMAIN_NAME + '/experience/' + str(self.experience.id)})
        self.send_mail()

    def send_notification_email_to_guest(self):
        self.subject = '[Tripalocal] You booking request is sent to the host'
        self.message = ''
        self.sender = 'Tripalocal <' + Aliases.objects.filter(destination__contains=self.host.email)[0].mail + '>'
        self.recipients = [Aliases.objects.filter(destination__contains=self.guest.email)[0].mail]
        self.priority = 'now'
        self.html_message=loader.render_to_string('experiences/email_booking_requested_traveler.html',
                                                         {'experience': self.experience,
                                                          'experience_url':settings.DOMAIN_NAME + '/experience/' + str(self.experience.id),
                                                          'booking':self.booking})
        self.send_mail()

    def send_confirmation_email_to_guest(self):
        self.subject = '[Tripalocal] Booking confirmed'
        self.message = ''
        self.sender = 'Tripalocal <' + Aliases.objects.filter(destination__contains=self.host.email)[0].mail + '>'
        self.recipients = [Aliases.objects.filter(destination__contains=self.guest.email)[0].mail]
        self.priority = 'now'
        self. html_message = loader.render_to_string('experiences/email_booking_confirmed_traveler.html',
                                                                      {'experience': self.experience,
                                                                      'booking':self.booking,
                                                                      'user':self.guest,
                                                                      'experience_url':settings.DOMAIN_NAME + '/experience/' + str(self.experience.id)})
        self.send_mail()

    def send_mail(self, **kwargs):
        print(self.html_message)
        mail.send(subject = self.subject,
                  message = self.message,
                  sender = self.sender,
                  recipients = self.recipients,
                  priority = self.priority,
                  html_message = self.html_message)
