from post_office import mail
from genderize import Genderize

class MailSupportMixin(object):
    subject = None
    message = None
    sender = None
    recipients = None
    priority = 'now'
    html_message = None

    def send_mail(self, **kwargs):
        mail.send(subject = self.subject,
                  message = self.message,
                  sender = self.sender,
                  recipients = self.recipients,
                  priority = self.priority,
                  html_message = self.html_message)
