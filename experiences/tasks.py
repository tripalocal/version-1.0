import os
from django.conf import settings
from celery import Celery
from experiences.telstra_sms_api import send_sms

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tripalocal_V1.settings')

app = Celery('tasks')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.update(
    CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend',
)

@app.task
def schedule_sms(phone_num, msg):
    send_sms(phone_num, msg)

