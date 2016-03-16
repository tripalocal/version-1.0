"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import django, django.conf, Tripalocal_V1, pytz, stripe
from django.test import TestCase
from experiences.utils import *
from experiences.models import *
from experiences.views import *
from builtins import ValueError
from datetime import datetime
from dateutil.relativedelta import relativedelta

# TODO: Configure your database in settings.py and sync before running tests.

def create_stripe_token():
    stripe.api_key = settings.STRIPE_SECRET_KEY
    token = stripe.Token.create(
                card={
                "number": '4242424242424242',
                "exp_month": 12,
                "exp_year": 2017,
                "cvc": '123'
                },
            )
    return token["id"]

class UtilsTest(TestCase):
    def test_isEnglish(self):
        self.assertTrue(isEnglish("test"))
        self.assertFalse(isEnglish("测试"))
        self.assertTrue(isEnglish(""))
        self.assertFalse(isEnglish(None))

    def test_experience_fee_calculator(self):
        self.assertEqual(experience_fee_calculator(None, None), None)
        self.assertEqual(experience_fee_calculator("", None), "")
        self.assertEqual(experience_fee_calculator(100, -0.1), 100)
        self.assertEqual(experience_fee_calculator(100, 1), 100)
        self.assertEqual(experience_fee_calculator(100, 0), 100)
        self.assertEqual(experience_fee_calculator(100, 0.2), 125)

    def test_convert_currency(self):
        self.assertEqual(convert_currency(None, "", ""), None)
        self.assertEqual(convert_currency(100, None, ""), 100)
        self.assertEqual(convert_currency(100, "", ""), 100)
        self.assertEqual(convert_currency(100, "aud", "aud"), 100)
        self.assertEqual(convert_currency(100, "aud", "xxx"), 100)
        self.assertEqual(convert_currency(100, "aud", "cny", [100]), 100)
        self.assertEqual(convert_currency(100, "AUD", "cny", {"xxx":1}), 100)
        self.assertEqual(convert_currency(100, "AUD", "cny"), 480)
        self.assertEqual(convert_currency(100, "AUD", "cny", {}), 480)
        self.assertEqual(convert_currency(100, "AUD", "cny", {"CNY":4.5}), 450)

    def test_get_total_price(self):
        experience = NewProduct.objects.get(id=700013)
        self.assertRaises(ValueError, get_total_price, experience, 1, 1, 1,"{\"1243\":1, \"2344\":2}")
        self.assertAlmostEqual(1232.72, get_total_price(experience, 1, 1, 1,"{\"54531\":2, \"57164\":3}"))

        experience = NewProduct.objects.get(id=981)
        self.assertAlmostEqual(30, get_total_price(experience, None, None, None))
        self.assertAlmostEqual(30, get_total_price(experience, -1, -2, 0))
        self.assertAlmostEqual(60, get_total_price(experience, 2, 0, 0))
        self.assertAlmostEqual(69, get_total_price(experience, 2, 1, 3))
        self.assertAlmostEqual(69, get_total_price(experience, 0, 1, 3))

        experience = Experience.objects.get(id=59)
        self.assertAlmostEqual(400, get_total_price(experience, None, None, None))
        self.assertAlmostEqual(400, get_total_price(experience, -1, -2, 0))
        self.assertAlmostEqual(400, get_total_price(experience, 2, 0, 0))
        self.assertAlmostEqual(383.48, get_total_price(experience, 2, 1, 3))
        self.assertAlmostEqual(383.48, get_total_price(experience, 0, 1, 3))

    def test_get_timezone(self):
        self.assertRaises(AttributeError, get_timezone, None)
        self.assertEqual("Australia/Melbourne", get_timezone(""))
        self.assertEqual("Australia/Melbourne", get_timezone("melbourne"))
        self.assertEqual("Australia/Sydney", get_timezone("sydney"))

    def test_email_account_generator(self):
        email = email_account_generator()
        self.assertTrue(len(email) == 10 and email.isalnum() and email.islower())
        email = email_account_generator(0)
        self.assertTrue(len(email) == 10 and email.isalnum() and email.islower())
        email = email_account_generator("&)(&98YIO")
        self.assertTrue(len(email) == 10 and email.isalnum() and email.islower())
        email = email_account_generator(16, "&)(&98YIO")
        self.assertTrue(len(email) == 16 and email.isalnum() and email.islower())
        email = email_account_generator(9, None)
        self.assertTrue(len(email) == 9 and email.isalnum() and email.islower())
        email = email_account_generator(30)
        self.assertTrue(len(email) == 10 and email.isalnum() and email.islower())
        email = email_account_generator(7, "a")
        self.assertTrue(email=="aaaaaaa")

class ViewsTest(TestCase):
    def test_set_initial_currency(self):
        request = self.client.request(method="GET").wsgi_request
        set_initial_currency(self.client.request(method="GET").wsgi_request)
        self.assertEqual("AUD", request.session["custom_currency"])

        request.session["custom_currency"] = "CNY"
        set_initial_currency(request)
        self.assertEqual("CNY", request.session["custom_currency"])

    def test_convert_experience_price(self):
        request = self.client.request(method="GET").wsgi_request
        experience = Experience.objects.get(id=59)
        self.assertIsNone(convert_experience_price(request, experience))

        request.session["custom_currency"] = "CNY"
        convert_experience_price(request, experience)
        self.assertEqual(0, experience.dynamic_price.find("960.0,614.69,"))
        self.assertEqual("CNY", experience.currency)

        experience = NewProduct.objects.get(id=700013)
        request.session["custom_currency"] = "AUD"
        set = convert_experience_price(request, experience)
        self.assertEqual(2, len(set))
        self.assertAlmostEqual(278.95, set[0]["optionitem_set"][0]["price"])
        self.assertEqual("AUD", experience.currency.upper())

        request.session["custom_currency"] = "CNY"
        set = convert_experience_price(request, experience)
        self.assertEqual(2, len(set))
        self.assertAlmostEqual(278.95*4.8, set[0]["optionitem_set"][0]["price"])
        self.assertEqual("CNY", experience.currency.upper())

    def test_get_available_experiences(self):
        self.assertRaises(AttributeError, get_available_experiences, None, None, None, None)
        self.assertRaises(AttributeError, get_available_experiences, None,
                          pytz.timezone('UTC').localize(datetime.now()),
                          pytz.timezone('UTC').localize(datetime.now()) + relativedelta(days=1),
                          None)
        exps = get_available_experiences("experience",
                          pytz.timezone('UTC').localize(datetime.now()),
                          pytz.timezone('UTC').localize(datetime.now()) + relativedelta(days=1),
                          "Melbourne,")
        self.assertEqual(70, len(exps))
        exps = get_available_experiences("experience",
                          pytz.timezone('UTC').localize(datetime.now()),
                          pytz.timezone('UTC').localize(datetime.now()) + relativedelta(days=1),
                          "Melbourne,",1)
        self.assertEqual(74, len(exps))

    def test_experience_booking_confirmation(self):
        #book a partner product via stripe
        token = create_stripe_token()
        response = self.client.post("/experience_booking_confirmation/", {"user_id": 1,
                                                                    "experience_id": 700013,
                                                                    "date": "2016-03-18",
                                                                    "time": "15:00",
                                                                    "adult_number": 2,
                                                                    "child_number": 3,
                                                                    "status": "Requested",
                                                                    "promo_code": "",
                                                                    "first_name": "first",
                                                                    "last_name": "last",
                                                                    "phone_number": "+61 412341234",
                                                                    "coupon_extra_information": "",
                                                                    "booking_extra_information": "",
                                                                    "partner_product_information": "{\"54531\":2, \"57164\":3}",
                                                                    "custom_currency": "AUD",
                                                                    "stripeToken": token})
        self.assertContains(response, "Successful Booking", 1, 200)

        #book an experience via stripe
        token = create_stripe_token()
        response = self.client.post("/experience_booking_confirmation/", {"user_id": 1,
                                                                    "experience_id": 20,
                                                                    "date": "2016-03-18",
                                                                    "time": "15:00",
                                                                    "adult_number": 2,
                                                                    "child_number": 3,
                                                                    "status": "Requested",
                                                                    "promo_code": "",
                                                                    "first_name": "first",
                                                                    "last_name": "last",
                                                                    "phone_number": "+61 412341234",
                                                                    "coupon_extra_information": "",
                                                                    "booking_extra_information": "",
                                                                    "partner_product_information": "",
                                                                    "custom_currency": "AUD",
                                                                    "stripeToken": token})
        self.assertContains(response, "Successful Booking", 1, 200)

    def test_search_experience(self):
        self.assertEqual(56, len(search_experience("%Melbourne%", "zh")))

    def test_getAvailableOptions(self):
        experience = NewProduct.objects.get(id=852)
        available_options = []
        available_date = ()
        available_date = getAvailableOptions(experience, available_options, available_date,
                                             pytz.timezone(experience.get_timezone()).localize(datetime(2016, 3, 18, 0)))
        self.assertEqual(31, len(available_date))
        self.assertEqual(31*14, len(available_options))

    def test_get_related_experiences(self):
        request = self.client.request(method="GET").wsgi_request
        request.session["custom_currency"] = "CNY"
        #has been booked
        experience = Experience.objects.get(id=20)
        self.assertEqual(2, len(get_related_experiences(experience, request)))
        #has been tagged
        experience = Experience.objects.get(id=30)
        self.assertEqual(2, len(get_related_experiences(experience, request)))
        #other
        experience = NewProduct.objects.get(id=1001)
        self.assertEqual(2, len(get_related_experiences(experience, request)))

    def test_get_experience_popularity(self):
        experience = Experience.objects.get(id=20)
        #SELECT experience_id, count(experience_id)
        #FROM app_userpageviewrecord
        #where time_arrived >= NOW() - INTERVAL 30 DAY and 
        #(select type from experiences_experience where abstractexperience_ptr_id=experience_id) in ('PRIVATE', 'NONPRIVATE')
        #group by experience_id 
        #order by count(experience_id) desc;
        self.assertAlmostEqual(100-100*5/248, get_experience_popularity(experience))

        experience = Experience.objects.get(id=651)
        #SELECT experience_id, count(experience_id)
        #FROM app_userpageviewrecord
        #where time_arrived >= NOW() - INTERVAL 30 DAY and 
        #(select type from experiences_experience where abstractexperience_ptr_id=experience_id) in ('ITINERARY')
        #group by experience_id 
        #order by count(experience_id) desc;
        self.assertAlmostEqual(100-100*7/8, get_experience_popularity(experience))

        experience = NewProduct.objects.get(id=852)
        #SELECT experience_id, count(experience_id)
        #FROM app_userpageviewrecord
        #where time_arrived >= NOW() - INTERVAL 30 DAY and experience_id in 
        #(select abstractexperience_ptr_id from experiences_newproduct)
        #group by experience_id 
        #order by count(experience_id) desc;
        self.assertAlmostEqual(100-100*7/640, get_experience_popularity(experience))