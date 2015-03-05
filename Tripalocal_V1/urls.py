"""
Definition of urls for Tripalocal_V1.
"""

from datetime import datetime
from django.conf.urls import patterns, url
from app.forms import BootstrapAuthenticationForm, SubscriptionForm

from experiences.models import Experience
from experiences.views import *
from Tripalocal_V1 import settings
from django.contrib.auth.decorators import login_required

# Uncomment the next lines to enable the admin:
from django.conf.urls import include
from django.contrib import admin

from rest_framework.authtoken import views

from django.conf.urls import *
#from experiences.resource import ajax_view

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'app.views.home', name='home'),
    url(r'^contactus$', 'app.views.contact', name='contact'),
    url(r'^aboutus', 'app.views.about', name='about'),
    url(r'^termsofservice', 'app.views.termsofservice'),
    url(r'^privacypolicy', 'app.views.privacypolicy'),
    url(r'^refundpolicy', 'app.views.refundpolicy'),
    #url(r'^login/$',
    #    'django.contrib.auth.views.login',
    #    {
    #        'template_name': 'app/login.html',
    #        'authentication_form': BootstrapAuthenticationForm,
    #        'extra_context':
    #        {
    #            'title':'Log in',
    #            'year':datetime.now().year,
    #        }
    #    },
    #    name='login'),
    #url(r'^logout$',
    #    'django.contrib.auth.views.logout',
    #    {
    #        'next_page': '/',
    #    },
    #    name='logout'),

    #url(r'^signup/$', 'app.views.signup', name='signup'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    #url(r'^experiencelist/$', ExperienceListView.as_view(), name='experiencelist'),
    url(r'^experience/(?P<pk>\d+)/$', ExperienceDetailView.as_view(), name='experiencedetail'),
    url(r'^images/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    url(r'^addexperience/(?P<step>[-\w]+)/$', login_required(ExperienceWizard.as_view(FORMS, url_name='experience_add_step', condition_dict={'price': save_exit_price,'overview': save_exit_overview,
                                                                                                                                             'detail': save_exit_detail,'photo':save_exit_photo,
                                                                                                                                             'location':save_exit_location})), name='experience_add_step'),
    #url(r'^addexperience/$', login_required(ExperienceWizard.as_view(FORMS, url_name='experience_add_step')), name='experience_add'),
    #url(r'^editexperience/$', login_required(ExperienceWizard.as_view(FORMS, url_name='experience_edit_step')), name='experience_edit'),
    url(r'^editexperience/(?P<step>[-\w]+)/$', login_required(ExperienceWizard.as_view(FORMS, url_name='experience_edit_step', condition_dict={'experience':save_exit_experience, 'price': save_exit_price,'overview': save_exit_overview,
                                                                                                                                             'detail': save_exit_detail,'photo':save_exit_photo,
                                                                                                                                             'location':save_exit_location})), name='experience_edit_step'),
    url(r'^experience_booking_confirmation/$', experience_booking_confirmation, name='experience_booking_confirmation'),
    url(r'^experience_booking_successful/$', experience_booking_successful, name='experience_booking_successful'),
    #url(r'^createexperience/$', create_experience, name='create_experience'),
    #url(r'^editexperience/(?P<id>\d+)/$', create_experience, name='edit_experience'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'^accounts/', include('allauth.urls')),
    #url(r'^payment/$', charge, name="charge"),
    url(r'^registration_successful', 'app.views.registration_successful', name='registration_successful'),
    url(r'^disclaimer$', 'app.views.disclaimer', name='disclaimer'),
    url(r'^booking/(?P<id>\d+)/$', booking_accepted, name='booking_accepted'),
<<<<<<< HEAD
    url(r'^s/(?P<city>\S+)/$', ByCityExperienceListView, name='ByCityExperienceListView'),  
    url(r'^freesim/$', 'experiences.views.freeSimPromo', name='freeSimPromo'),
    url(r'^mytrip/$', 'app.views.mytrip'),
    url(r'^myprofile/$', 'app.views.myprofile'),
    url(r'^mylisting/$', 'app.views.mylisting'),
    url(r'^myreservation/$', 'app.views.myreservation'),
    url(r'^mycalendar/$', 'app.views.mycalendar'),
    url(r'^reviewexperience/(?P<id>\d+)/$', 'experiences.views.review_experience', name='review_experience'),
    url(r'^booking_request/$', 'experiences.resource.booking_request'),
    url(r'^api-token-auth/', views.obtain_auth_token),
    url(r'^booking_request_xls/$', 'experiences.resource.saveBookingRequestsFromXLS'),
    #url(r'^experience_autosave$', ajax_view, name="ajax_view"),
    url(r'^experience_availability/$', experience_availability, name='experience_availability'),
=======
    url(r'^s/(?P<city>\S+)/$', ByCityExperienceListView, name='ByCityExperienceListView'),
    url(r'^experiences$', 'experiences.views.experiences', name='experiences'),
    url(r'^experiences_ch$', 'experiences.views.experiences_ch', name='experiences_ch'),
    url(r'^prelaunch/livesite/experiences$', 'experiences.views.experiences_pre', name='experiences_pre'),
    url(r'^prelaunch/livesite/experiences_ch$', 'experiences.views.experiences_ch_pre', name='experiences_ch_pre'),

    url(r'^s/(?P<city>\S+)/$', ByCityExperienceListView, name='ByCityExperienceListView'),
>>>>>>> 35d82b2097a46c5c659ae49ee2f5e183958f0ee3
)
