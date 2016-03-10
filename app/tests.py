import django
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

class ViewTest(TestCase):
    """Tests for the application views."""

    def test_home(self):
        """Tests the home page."""
        response = self.client.get('/')
        self.assertContains(response, _("Tripalocal | Experience it like a local"), 1, 200)
        response = self.client.post('http://localhost:8000/',{'start_date': '2016-03-05','end_date': '2016-03-09', 'city': "Melbourne"})
        self.assertContains(response, _("Discover Melbourne"), 1, 200)
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
        response = self.client.get('/aboutus')
        self.assertContains(response, _("Tripalocal | About Us"), 1, 200)
