"""
Definition of urls for Tripalocal_V1.
"""

from datetime import datetime
from django.conf.urls import patterns, url
from app.forms import BootstrapAuthenticationForm, SubscriptionForm

from experiences.models import Experience
from experiences.views import ExperienceListView, ExperienceDetailView, ExperienceWizard, FORMS, experience_booking_confirmation, experience_booking_successful, create_experience, booking_accepted, ByCityExperienceListView
from Tripalocal_V1 import settings

# Uncomment the next lines to enable the admin:
from django.conf.urls import include
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'app.views.home', name='home'),
    #url(r'^contact$', 'app.views.contact', name='contact'),
    #url(r'^about', 'app.views.about', name='about'),
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
    #url(r'^addexperience/$', ExperienceWizard.as_view(FORMS)),
    url(r'^experience_booking_confirmation/$', experience_booking_confirmation, name='experience_booking_confirmation'),
    #url(r'^experience_booking_successful/$', experience_booking_successful, name='experience_booking_successful'),
    #url(r'^createexperience/$', create_experience, name='create_experience'),
    #url(r'^editexperience/(?P<id>\d+)/$', create_experience, name='edit_experience'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'^accounts/', include('allauth.urls')),
    #url(r'^payment/$', charge, name="charge"),
    url(r'^registration_successful', 'app.views.registration_successful', name='registration_successful'),
    url(r'^disclaimer$', 'app.views.disclaimer', name='disclaimer'),
    url(r'^booking/(?P<id>\d+)/$', booking_accepted, name='booking_accepted'),
    url(r'^s/(?P<city>\S+)/$', ByCityExperienceListView, name='ByCityExperienceListView'),
    url(r'^experiences$', 'experiences.views.experiences', name='experiences'),
    url(r'^experiences_ch$', 'experiences.views.experiences_ch', name='experiences_ch'),
    url(r'^PreLaunch/livesite/experiences.html$', 'experiences.views.experiences_pre', name='experiences_pre'),
    url(r'^PreLaunch/livesite/experiences_ch.html$', 'experiences.views.experiences_ch_pre', name='experiences_ch_pre'),
    url(r'^PreLaunch/livesite/experiences_sydney.html$', 'experiences.views.experiences_sydney_pre', name='experiences_sydney_pre'),
    url(r'^freesim/$', 'experiences.views.freeSimPromo', name='freeSimPromo'),
)
