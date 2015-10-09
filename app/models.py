from django.db import models
from django.contrib.auth.models import User
from experiences.models import Experience, AbstractExperience

class RegisteredUser(models.Model):
    def upload_path(self, name):
        return self.image_url

    user = models.OneToOneField(User, related_name='registereduser')
    image_url = models.CharField(max_length=200)
    image = models.ImageField(upload_to=upload_path)
    phone_number = models.CharField(max_length=15)
    rate = models.DecimalField(max_digits=2, decimal_places=1)
    wishlist = models.ManyToManyField(Experience, related_name='user_wishlist')

    def __str__(self):
        return str(self.user.id) + '--' + self.user.email

class RegisteredUserBio(models.Model):
    bio = models.TextField()
    language = models.CharField(max_length=2)
    registereduser = models.ForeignKey(RegisteredUser)

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

class UserPageViewStatistics(models.Model):
    user = models.ForeignKey(User)
    experience = models.ForeignKey(AbstractExperience)
    times_viewed = models.IntegerField(default=0)
    average_length = models.FloatField(default=0.0)

def get_user_bio(registereduser, language):
    if registereduser.registereduserbio_set is not None and len(registereduser.registereduserbio_set.all()) > 0:
        b = registereduser.registereduserbio_set.filter(language=language)
        if len(b)>0:
            return b[0].bio
        else:
            return registereduser.registereduserbio_set.all()[0].bio
    else:
        return ""

def save_user_bio(registereduser, newbio, language):
    if registereduser.registereduserbio_set is not None:
        b = registereduser.registereduserbio_set.filter(language=language)
        if len(b)>0:
            b[0].bio=newbio
            b[0].save()
        else:
            bio = RegisteredUserBio(bio=newbio, language=language, registereduser=registereduser)
            bio.save()
    else:
        bio = RegisteredUserBio(bio=newbio, language=language, registereduser=registereduser)
        bio.save()