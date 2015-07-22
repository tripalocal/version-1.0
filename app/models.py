from django.db import models
from django.contrib.auth.models import User
from experiences.models import Experience

class RegisteredUser(models.Model):
    def upload_path(self, name):
        return self.image_url

    user = models.OneToOneField(User, related_name='registereduser')
    image_url = models.CharField(max_length=200)
    image = models.ImageField(upload_to=upload_path)
    phone_number = models.CharField(max_length=15)
    bio = models.TextField()
    rate = models.DecimalField(max_digits=2, decimal_places=1)
    wishlist = models.ManyToManyField(Experience, related_name='user_wishlist')

    def __str__(self):
        return str(self.user.id) + '--' + self.user.email

class Subscription(models.Model):
    email = models.EmailField()
    subscribed_datetime = models.DateTimeField()
    ref_by = models.EmailField()
    ref_link = models.CharField(max_length = 20)

class InstantBookingTimePeriod(models.Model):
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    repeat_end_date = models.DateField()
    repeat = models.BooleanField(default=False)
    repeat_cycle = models.CharField(max_length=50)
    repeat_frequency = models.IntegerField()
    repeat_extra_information = models.CharField(max_length=50)
    user = models.ForeignKey(User)

class BlockOutTimePeriod(models.Model):
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    repeat_end_date = models.DateField()
    repeat = models.BooleanField(default=False)
    repeat_cycle = models.CharField(max_length=50)
    repeat_frequency = models.IntegerField()
    repeat_extra_information = models.CharField(max_length=50)
    user = models.ForeignKey(User)

class Message(models.Model):
    sender = models.ForeignKey(User,related_name='message_sender',unique=False)
    receiver = models.ForeignKey(User,related_name='message_receiver',unique=False)
    datetime_sent = models.DateTimeField()
    datetime_delivered = models.DateTimeField(null=True, blank=True)
    datetime_read = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20)
    content = models.TextField()

class UserPhoto(models.Model):
    def upload_path(self, name):
        return self.directory + self.name

    name = models.CharField(max_length=50)
    directory = models.CharField(max_length=50)
    image = models.ImageField(upload_to=upload_path)
    user = models.ForeignKey(User)
    type = models.CharField(max_length=50)