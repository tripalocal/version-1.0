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
    url(r'^s/(?P<city>\S+)/$', SearchView, name='SearchView'),  
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
    #url(r'^itinerary/$', custom_itinerary, name='custom_itinerary'),
    url(r'^service_search/$', 'experiences.resource.service_search', name='service_search'),
    url(r'^service_mytrip/$', 'experiences.resource.service_mytrip', name='service_mytrip'),
    url(r'^service_myreservation/$', 'experiences.resource.service_myreservation', name='service_myreservation'),
    url(r'^service_acceptreservation/$', 'experiences.resource.service_acceptreservation', name='service_acceptreservation'),
    url(r'^service_login/$', 'experiences.resource.service_login', name='service_login'),
    url(r'^service_signup/$', 'experiences.resource.service_signup', name='service_signup'),
    url(r'^service_logout/$', 'experiences.resource.service_logout', name='service_logout'),
    url(r'^service_facebook_login/$', 'experiences.resource.service_facebook_login', name='service_facebook_login'),
    url(r'^service_booking/$', 'experiences.resource.service_booking', name='service_booking'),
    url(r'^itinerary_booking_confirmation/$', itinerary_booking_confirmation, name='itinerary_booking_confirmation'),
    url(r'^itinerary_booking_successful/$', itinerary_booking_successful, name='itinerary_booking_successful'),
    url(r'^service_experience/$', 'experiences.resource.service_experience', name='service_experience'),
    url(r'^service_myprofile/$', 'experiences.resource.service_myprofile', name='service_myprofile'),
    url(r'^service_wishlist/$', 'experiences.resource.service_wishlist', name='service_wishlist'),
    #url(r'^service_email/$', 'experiences.resource.service_email', name='service_email'),
)
