from django.db import models

class Subscription(models.Model):
    email = models.EmailField()
    subscribed_datetime = models.DateTimeField()
    ref_by = models.EmailField()
    ref_link = models.CharField(max_length = 20)
