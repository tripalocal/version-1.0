from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
import datetime
from allauth.socialaccount.models import SocialAccount
import hashlib
from Tripalocal_V1 import settings

class ExperienceTag(models.Model):
    tag = models.CharField(max_length=100)
    language = models.CharField(max_length=2)

class Experience(models.Model):
    type = models.CharField(max_length=50)
    language = models.CharField(max_length=50)

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    repeat = models.BooleanField(default=False)
    repeat_cycle = models.CharField(max_length=50)
    repeat_frequency = models.IntegerField()
    repeat_extra_information = models.CharField(max_length=50)
    allow_instant_booking = models.BooleanField(default=False)
    duration = models.IntegerField()

    guest_number_max = models.IntegerField()
    guest_number_min = models.IntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    currency = models.CharField(max_length=10)
    dynamic_price = models.CharField(max_length=100)

    #title = models.CharField(max_length=100)
    #description = models.TextField()
    #activity = models.TextField()
    #interaction = models.TextField()
    #dress = models.TextField()
    
    city = models.CharField(max_length=50)
    address = models.TextField()
    #meetup_spot = models.TextField()
    
    hosts = models.ManyToManyField(User, related_name='experience_hosts')
    guests = models.ManyToManyField(User, related_name='experience_guests')
    status = models.CharField(max_length=50)

    tags = models.ManyToManyField(ExperienceTag, related_name='experience_tags')

    def __str__(self):
        t = get_experience_title(self, settings.LANGUAGES[0][0])
        if t is None:
            t = ''
        s = self.status if self.status != None else ''
        c = self.city if self.city != None else ''
        return str(self.id) + '--' + t + '--' + s + '--' + c

    class Meta:
        ordering = ['id']

class ExperienceTitle(models.Model):
    title = models.CharField(max_length=100)
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class ExperienceDescription(models.Model):
    description = models.TextField()
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class ExperienceActivity(models.Model):
    activity = models.TextField()
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class ExperienceInteraction(models.Model):
    interaction = models.TextField()
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class ExperienceDress(models.Model):
    dress = models.TextField()
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class ExperienceMeetupSpot(models.Model):
    meetup_spot = models.TextField()
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class ExperienceDropoffSpot(models.Model):
    dropoff_spot = models.TextField()
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class InstantBookingTimePeriod(models.Model):
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    repeat_end_date = models.DateField()
    repeat = models.BooleanField(default=False)
    repeat_cycle = models.CharField(max_length=50)
    repeat_frequency = models.IntegerField()
    repeat_extra_information = models.CharField(max_length=50)
    experience = models.ForeignKey(Experience)

class BlockOutTimePeriod(models.Model):
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    repeat_end_date = models.DateField()
    repeat = models.BooleanField(default=False)
    repeat_cycle = models.CharField(max_length=50)
    repeat_frequency = models.IntegerField()
    repeat_extra_information = models.CharField(max_length=50)
    experience = models.ForeignKey(Experience)

class WhatsIncluded(models.Model):
    item = models.CharField(max_length=50)
    included = models.BooleanField(default=False)
    details = models.TextField()
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class Photo(models.Model):
    def upload_path(self, name):
        return self.directory + self.name

    name = models.CharField(max_length=50)
    directory = models.CharField(max_length=50)
    image = models.ImageField(upload_to=upload_path)
    experience = models.ForeignKey(Experience)

class Review(models.Model):
    user = models.ForeignKey(User)
    experience = models.ForeignKey(Experience)
    comment = models.TextField()
    rate = models.IntegerField()
    datetime = models.DateTimeField()
    personal_comment = models.TextField()
    operator_comment = models.TextField()

    def __str__(self):
        return self.user.email + "--" + self.experience.title

class Coupon(models.Model):
    promo_code = models.CharField(max_length=10)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    rules = models.TextField()
    title = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.promo_code

class Booking(models.Model):
    user = models.ForeignKey(User)
    coupon = models.ForeignKey(Coupon)
    coupon_extra_information = models.TextField()
    guest_number = models.IntegerField()
    experience = models.ForeignKey(Experience)
    datetime = models.DateTimeField()
    status = models.CharField(max_length=50)
    submitted_datetime = models.DateTimeField()
    payment = models.ForeignKey("Payment", related_name="payment")
    refund_id = models.CharField(max_length=50)
    booking_extra_information = models.TextField()
    
    def __str__(self):
        return self.user.email + "--" + get_experience_title(self.experience,settings.LANGUAGES[0][0])

class Payment(models.Model):
    def __init__(self, *args, **kwargs):
        super(Payment, self).__init__(*args, **kwargs)
 
        # bring in stripe, and get the api key from settings.py
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
 
        self.stripe = stripe
 
    # store the stripe charge id for this sale
    charge_id = models.CharField(max_length=32)
    booking = models.ForeignKey(Booking, related_name="booking")
    street1 = models.CharField(max_length=50)
    street2 = models.CharField(max_length=50)
    city = models.CharField(max_length=20)
    zip_code = models.CharField(max_length=4)
    state = models.CharField(max_length=3)
    country = models.CharField(max_length=15)
    phone_number = models.CharField(max_length=15)
 
    # you could also store other information about the sale
    # but I'll leave that to you!
 
    def charge(self, price_in_cents, currency, number=None, exp_month=None, exp_year=None, cvc=None, stripe_token=None):
        """
        Takes a the price and credit card details: number, currency, exp_month,
        exp_year, cvc.
 
        Returns a tuple: (Boolean, Class) where the boolean is if
        the charge was successful, and the class is response (or error)
        instance.
        """
 
        if self.charge_id: # don't let this be charged twice!
            return False, Exception(message="Already charged.")
 
        try:
            if stripe_token is not None:
                response = self.stripe.Charge.create(
                            amount = price_in_cents,
                            currency = currency.lower(),
                            source = stripe_token,
                            description='')
            else:
                response = self.stripe.Charge.create(
                            amount = price_in_cents,
                            currency = currency.lower(),
                            card = {
                                "number" : number,
                                "exp_month" : exp_month,
                                "exp_year" : exp_year,
                                "cvc" : cvc,
 
                                #### it is recommended to include the address!
                                "address_line1" : self.street1,
                                "address_line2" : self.street2,
                                "address_city" : self.city,
                                "address_zip" : self.zip_code,
                                "address_state" : self.state,
                                "address_country" : self.country,
                            },
                            description='')
 
            self.charge_id = response.id
 
        except self.stripe.CardError as ce:
            # charge failed
            return False, ce
        except Exception as ex:
            return False, ex
 
        return True, response

    def refund(self, charge_id, amount):
        try:
            ch = self.stripe.Charge.retrieve(charge_id)
            if amount != None:
                re = ch.refund(amount = amount) # ch.refunds.create() 
            else:
                re = ch.refund() # ch.refunds.create() 
            booking = Booking.objects.get(payment_id = Payment.objects.get(charge_id = ch.id).id)
            booking.status = "rejected"
            booking.refund_id = re.id
            booking.save()
        except self.stripe.error.StripeError as e:
            return False, e
        except Exception as e:
            return False, e
        return True, re

def get_experience_title(experience, language):
    if experience.experiencetitle_set is not None and len(experience.experiencetitle_set.all()) > 0:
        t = experience.experiencetitle_set.filter(language=language)
        if len(t)>0:
            return t[0].title
        else:
            return experience.experiencetitle_set.all()[0].title
    else:
        return None

def get_experience_activity(experience, language):
    if experience.experienceactivity_set is not None and len(experience.experienceactivity_set.all()) > 0:
        t = experience.experienceactivity_set.filter(language=language)
        if len(t)>0:
            return t[0].activity
        else:
            return experience.experienceactivity_set.all()[0].activity
    else:
        return None

def get_experience_description(experience, language):
    if experience.experiencedescription_set is not None and len(experience.experiencedescription_set.all()) > 0:
        t = experience.experiencedescription_set.filter(language=language)
        if len(t)>0:
            return t[0].description
        else:
            return experience.experiencedescription_set.all()[0].description
    else:
        return None

def get_experience_interaction(experience, language):
    if experience.experienceinteraction_set is not None and len(experience.experienceinteraction_set.all()) > 0:
        t = experience.experienceinteraction_set.filter(language=language)
        if len(t)>0:
            return t[0].interaction
        else:
            return experience.experienceinteraction_set.all()[0].interaction
    else:
        return None

def get_experience_dress(experience, language):
    if experience.experiencedress_set is not None and len(experience.experiencedress_set.all()) > 0:
        t = experience.experiencedress_set.filter(language=language)
        if len(t)>0:
            return t[0].dress
        else:
            return experience.experiencedress_set.all()[0].dress
    else:
        return None

def get_experience_meetup_spot(experience, language):
    if experience.experiencemeetupspot_set is not None and len(experience.experiencemeetupspot_set.all()) > 0:
        t = experience.experiencemeetupspot_set.filter(language=language)
        if len(t)>0:
            return t[0].meetup_spot
        else:
            return experience.experiencemeetupspot_set.all()[0].meetup_spot
    else:
        return None

def get_experience_tags(experience, language):
    tags = []

    if experience.tags is not None and len(experience.tags.all()) > 0:
        t = experience.tags.filter(language=language)
        for i in range(len(t)):
            tags.append(t[i].tag)

    return tags

def get_experience_whatsincluded(experience, language):
    w = WhatsIncluded.objects.filter(experience = experience, language = language)
    for item in w:
        if not item.included and (item.details is None or len(item.details))==0:
            item.details = _('Not included')
    return w

#class Itinerary(models.Model):
#    user = models.ForeignKey(User)
#    name = models.CharField(max_length=50)
#    start_datettime = models.DateTimeField()
#    end_datetime = models.DateTimeField()
#    group_size = models.IntegerField()
#    city=models.TextField()
#    #bookings = models.ManyToManyField(Booking, related_name='itinerary_bookings')

#    def __str__(self):
#        t = self.name if self.name != None else ''
#        return str(self.id) + '--' + str(self.user.id) + '--' + t