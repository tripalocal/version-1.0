import pytz
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.test import Client
from django.test import TestCase
from django.contrib.auth.models import User
from experiences.models import Booking,Experience,ExperienceI18n

class BaseDatabaseSetup(object):
    def setUp(self):
        # Create a super user, a host user and a guest user.
        user_super = User.objects.create_superuser(id=1, username='testing_super_user', password='123qwe', email='super@gmail.com')
        user_host = User.objects.create_user(id=2, username='testing_host_user', password='123qwe', email='host@gmail.com')
        user_guest = User.objects.create_user(id=3, username='testing_guest_user', password='123qwe', email='guest@gmail.com')

        #Create a experience and its i18n info.
        test_exp = Experience.objects.create(id = 1,
                                             start_datetime=datetime.utcnow().replace(tzinfo=pytz.UTC).replace(minute=0),
                                             end_datetime=datetime.utcnow().replace(tzinfo=pytz.UTC).replace(minute=0) + relativedelta(years=10),
                                             duration=3,
                                             city='Melbourne',
                                             guest_number_max=10,
                                             guest_number_min=1,
                                             repeat_frequency=1,
                                             price=100)
        ExperienceI18n.objects.create(id=1, experience_id=1, language='en', title='exp_1_en_title', description='exp_1_en_des')
        ExperienceI18n.objects.create(id=2, experience_id=1, language='zh', title='exp_1_zh_title', description='exp_1_zh_des')

        #Set the existing user as hosts.
        test_exp.hosts.add(user_host)

class ExperienceViewTestCase(BaseDatabaseSetup, TestCase):

    def setUp(self):
        super(ExperienceViewTestCase, self).setUp()

    def test_experience_view_change_status_valid_user(self):
        client = Client()
        # Test for valid parameters.
        client.login(username='super@gmail.com', password='123qwe')
        response = client.post('/custom_admin/experience/',
                               {'operation': 'post_status', 'status': 'Listed', 'object_id': '1'},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(str(response.content, encoding='utf8'))
        self.assertEqual(data['success'], True)
        client.login(username='super@gmail.com', password='123qwe')
        response = client.post('/custom_admin/experience/',
                               {'operation': 'post_status', 'status': 'Draft', 'object_id': '1'},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(str(response.content, encoding='utf8'))
        self.assertEqual(data['success'], True)
        client.login(username='super@gmail.com', password='123qwe')
        response = client.post('/custom_admin/experience/',
                               {'operation': 'post_status', 'status': 'Unlisted', 'object_id': '1'},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(str(response.content, encoding='utf8'))
        self.assertEqual(data['success'], True)
        client.login(username='super@gmail.com', password='123qwe')
        response = client.post('/custom_admin/experience/',
                               {'operation': 'post_status', 'status': 'Submitted', 'object_id': '1'},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(str(response.content, encoding='utf8'))
        self.assertEqual(data['success'], True)

        # Test for invalid operation  parameter.
        response = client.post('/custom_admin/experience/',
                               {'operation': 'post_st', 'status': 'Listed', 'object_id': '1'},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(str(response.content, encoding='utf8'))
        self.assertEqual(data['success'], False)

        # Test for invalid status parameter.
        response = client.post('/custom_admin/experience/',
                               {'operation': 'post_status', 'status': 'Lid', 'object_id': '1'},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(str(response.content, encoding='utf8'))
        self.assertEqual(data['success'], False)


        # Test for invalid object_id parameter.
        response = client.post('/custom_admin/experience/',
                               {'operation': 'post_status', 'status': 'Lid', 'object_id': '3'},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(str(response.content, encoding='utf8'))
        self.assertEqual(data['success'], False)

        # Test for invalid parameters.
        response = client.post('/custom_admin/experience/',
                               {'operation': 'post_staus', 'status': 'Lid', 'object_id': '3'},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(str(response.content, encoding='utf8'))
        self.assertEqual(data['success'], False)

    def test_experience_view_change_status_invalid_user(self):
        client = Client()
        # Test for valid parameters.
        client.login(username='testing_host_user', password='123qwe')
        response = client.post('/custom_admin/experience/',
                       {'operation': 'post_status', 'status': 'Listed', 'object_id': '1'},
                       HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual('', str(response.content,'utf8'))

class BookingViewTestCase(BaseDatabaseSetup, TestCase):
    def setUp(self):
        super(BookingViewTestCase, self).setUp()
        Booking.objects.create(id=1,
                               user_id=3,
                               guest_number=2,
                               experience_id=1,
                               datetime=datetime.now(),
                               status='paid',
                               submitted_datetime=datetime.now(),
                               coupon_id=1,
                               payment_id=1)

    def test__booking_view_upload_review(self):
        client = Client()
        client.login(username='super@gmail.com', password='123qwe')
        #Test for valid parameters.
        response = client.post('/custom_admin/booking',
                               {'operation': 'upload_review', 'review': 'Hello', 'object_id': 1, 'rate': 2},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(str(response.content, encoding='utf8'))
        self.assertEqual(data['success'], True)

        # Test for invalid parameters.
        # Invalid operation.
        response = client.post('/custom_admin/booking',
                               {'operation': 'upload', 'review': 'Hello', 'object_id': 1, 'rate': 2},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(str(response.content, encoding='utf8'))
        self.assertEqual(data['success'], False)
        # Invalid object_id.
        response = client.post('/custom_admin/booking',
                               {'operation': 'upload_review', 'review': 'Hello', 'object_id': 'dsadas', 'rate': 2},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(str(response.content, encoding='utf8'))
        self.assertEqual(data['success'], False)
        # Invalid rate.
        response = client.post('/custom_admin/booking',
                               {'operation': 'upload_review', 'review': 'Hello', 'object_id': 1, 'rate': 'dsadas'},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = json.loads(str(response.content, encoding='utf8'))
        self.assertEqual(data['success'], False)

    def test_booking_view_upload_review_invalid_user(self):
        client = Client()
        # Test for valid parameters.
        client.login(username='host@gmail.com', password='123qwe')
        response = client.post('/custom_admin/booking',
                               {'operation': 'upload_review', 'review': 'Hello', 'object_id': 1, 'rate': 2},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual('', str(response.content,'utf8'))