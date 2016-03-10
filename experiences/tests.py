"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import django, django.conf, Tripalocal_V1
from django.test import TestCase
from experiences.utils import *
from experiences.models import *
from experiences.views import *
from builtins import ValueError

# TODO: Configure your database in settings.py and sync before running tests.

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