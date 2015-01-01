from django.db import models
from django.contrib.auth.models import User

class RegisteredUser(models.Model):
    def upload_path(self, name):
        return self.image_url

    user = models.OneToOneField(User, related_name='registereduser')
    image_url = models.CharField(max_length=200)
    image = models.ImageField(upload_to=upload_path)
    phone_number = models.CharField(max_length=15)
    bio = models.TextField()
    rate = models.DecimalField(max_digits=2, decimal_places=1)

    def __str__(self):
        return self.user.username

class Subscription(models.Model):
    email = models.EmailField()
    subscribed_datetime = models.DateTimeField()
    ref_by = models.EmailField()
    ref_link = models.CharField(max_length = 20)
