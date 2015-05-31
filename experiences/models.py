from django.db import models
from django.contrib.auth.models import User
import datetime
from allauth.socialaccount.models import SocialAccount
import hashlib
from Tripalocal_V1 import settings

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
    dynamic_price = models.CharField(max_length=100)

    title = models.CharField(max_length=100)
    description = models.TextField()
    activity = models.TextField()
    interaction = models.TextField()
    dress = models.TextField()
    
    city = models.CharField(max_length=50)
    address = models.TextField()
    meetup_spot = models.TextField()
    
    hosts = models.ManyToManyField(User, related_name='experience_hosts')
    guests = models.ManyToManyField(User, related_name='experience_guests')
    status = models.CharField(max_length=50)

    tags = models.CharField(max_length=500)

    def __str__(self):
        t = self.title if self.title != None else ''
        s = self.status if self.status != None else ''
        return str(self.id) + '--' + t + '--' + s

    class Meta:
        ordering = ['id']

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
        return self.user.username + "--" + self.experience.title

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
 
    def charge(self, price_in_cents, number, exp_month, exp_year, cvc):
        """
        Takes a the price and credit card details: number, exp_month,
        exp_year, cvc.
 
        Returns a tuple: (Boolean, Class) where the boolean is if
        the charge was successful, and the class is response (or error)
        instance.
        """
 
        if self.charge_id: # don't let this be charged twice!
            return False, Exception(message="Already charged.")
 
        try:
            response = self.stripe.Charge.create(
                amount = price_in_cents,
                currency = "aud",
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
                description='Thank you for your purchase!')
 
            self.charge_id = response.id
 
        except self.stripe.CardError as ce:
            # charge failed
            return False, ce
 
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

class Itinerary(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=50)
    start_datettime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    group_size = models.IntegerField()
    city=models.TextField()
    #bookings = models.ManyToManyField(Booking, related_name='itinerary_bookings')

    def __str__(self):
        t = self.name if self.name != None else ''
        return str(self.id) + '--' + str(self.user.id) + '--' + t