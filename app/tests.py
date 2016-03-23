import django
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.admin import User
from app.views import getreservation
from app.models import get_user_bio
from Tripalocal_V1 import settings

class ViewTest(TestCase):
    """Tests for the application views."""

    def test_home(self):
        """Tests the home page."""
        response = self.client.get('/')
        self.assertContains(response, _("Tripalocal | Experience it like a local"), 1, 200)

        #invalid form --> homepage
        response = self.client.post('http://localhost:8000/',{'start_date': '','end_date': '', 'city': ""})
        self.assertContains(response, _("Tripalocal | Experience it like a local"), 1, 200)

        response = self.client.post('http://localhost:8000/',{'start_date': '2016-03-05','end_date': '2016-03-09', 'city': "Melbourne"})
        self.assertContains(response, _("Discover Melbourne"), 1, 200)

        #can't use {'start_date': None}
        response = self.client.post('http://localhost:8000/',{'start_date': '','end_date': '', 'city': "Melbourne"})
        self.assertContains(response, _("Discover Melbourne"), 1, 200)

        response = self.client.post('http://localhost:8000/',{'start_date': '','end_date': '2016-03-09', 'city': "Melbourne"})
        self.assertContains(response, _("Discover Melbourne"), 1, 200)

        response = self.client.post('http://localhost:8000/',{'start_date': '2016-03-05','end_date': '', 'city': "Melbourne"})
        self.assertContains(response, _("Discover Melbourne"), 1, 200)

    def test_contact(self):
        """Tests the contact page."""
        response = self.client.get('/contactus')
        self.assertContains(response, _("Tripalocal | Contact us"), 1, 200)

    def test_about(self):
        """Tests the about page."""
        response = self.client.get('/aboutus/')
        self.assertContains(response, _("Tripalocal | About Us"), 1, 200)

    def test_mylisting(self):
        #not logged in --> login page
        response = self.client.get('/mylisting/', follow=True)
        self.assertContains(response, "login_form", 2, 200)

        #logged in
        self.client.login(username='apptest@tripalocal.com', password='apptest1234')
        response = self.client.get('/mylisting/', follow=True)
        self.assertContains(response, "All listings", 1, 200)

    def test_getreservation(self):
        user = User.objects.get(id=1)
        r = getreservation(user)
        self.assertTrue("past_reservations" in r)
        self.assertTrue("current_reservations" in r)

        self.assertRaises(AttributeError, getreservation, None)

    def test_myreservation(self):
        #not logged in --> login page
        response = self.client.get('/myreservation/', follow=True)
        self.assertContains(response, "login_form", 2, 200)

        #logged in
        self.client.login(username='apptest@tripalocal.com', password='apptest1234')
        response = self.client.get('/myreservation/', follow=True)
        self.assertContains(response, "tab_area", 1, 200)

    def test_mytrip(self):
        #not logged in --> login page
        response = self.client.get('/mytrip/', follow=True)
        self.assertContains(response, "login_form", 2, 200)

        #logged in
        self.client.login(username='apptest@tripalocal.com', password='apptest1234')
        response = self.client.get('/mytrip/', follow=True)
        self.assertContains(response, "tab_area", 1, 200)

    def test_myprofile(self):
        #not logged in --> login page
        response = self.client.get('/myprofile/', follow=True)
        self.assertContains(response, "login_form", 2, 200)

        response = self.client.get('/myprofile/?user_id=1', follow=True)
        self.assertContains(response, "login_form", 2, 200)

        #logged in
        self.client.login(username='apptest@tripalocal.com', password='apptest1234')
        response = self.client.get('/myprofile/', follow=True)
        self.assertContains(response, "tab_area", 1, 200)

        response = self.client.post('/myprofile/', {"phone_number":"1234567", "bio":"apptest account"})
        self.assertEqual("1234567", User.objects.get(email="apptest@tripalocal.com").registereduser.phone_number)
        self.assertEqual("apptest account",
                         get_user_bio(User.objects.get(email="apptest@tripalocal.com").registereduser, settings.LANGUAGES[0][0]))
        self.assertContains(response, "tab_area", 1, 200)