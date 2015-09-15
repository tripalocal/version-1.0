"""
Definition of urls for Tripalocal_V1.
"""
from datetime import datetime
from django.conf.urls import patterns, url
from app.forms import BootstrapAuthenticationForm, SubscriptionForm
from django.views.generic import TemplateView

from experiences.models import Experience
from experiences.views import *
from Tripalocal_V1 import settings
from django.contrib.auth.decorators import login_required

# Uncomment the next lines to enable the admin:
from django.conf.urls import include
from django.contrib import admin

from rest_framework.authtoken import views

from app.decorators import superuser_required
from custom_admin.views.main import BookingView, BookingArchiveView, ExperienceView, PaymentView
from django.conf.urls import *
from django.views.i18n import javascript_catalog

js_info_dict = {
    'packages': ('Tripalocal_V1.app','Tripalocal_V1.experience',),
}

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^jsi18n/$', javascript_catalog, js_info_dict),
    url(r'^$', 'app.views.home', name='home'),
    url(r'^contactus$', 'app.views.contact', name='contact'),
    url(r'^aboutus', 'app.views.about', name='about'),
    url(r'^termsofservice', 'app.views.termsofservice'),
    url(r'^privacypolicy', 'app.views.privacypolicy'),
    url(r'^refundpolicy', 'app.views.refundpolicy'),
    url(r'^email_custom_trip', 'app.views.email_custom_trip'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    #url(r'^experiencelist/$', ExperienceListView.as_view(), name='experiencelist'),
    url(r'^experience/(?P<pk>\d+)/$', ExperienceDetailView.as_view(), name='experiencedetail'),
    url(r'^images/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    url(r'^apk/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.PROJECT_ROOT+'/apk'}),
    url(r'^html/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.PROJECT_ROOT+'/html'}),
    #url(r'^addexperience/(?P<step>[-\w]+)/$', login_required(ExperienceWizard.as_view(FORMS, url_name='experience_add_step', condition_dict={'price': save_exit_price,'overview': save_exit_overview,
    #                                                                                                                                         'detail': save_exit_detail,'photo':save_exit_photo,
    #                                                                                                                                         'location':save_exit_location})), name='experience_add_step'),
    #url(r'^addexperience/$', login_required(ExperienceWizard.as_view(FORMS, url_name='experience_add_step')), name='experience_add'),
    #url(r'^editexperience/$', login_required(ExperienceWizard.as_view(FORMS, url_name='experience_edit_step')), name='experience_edit'),
    #url(r'^editexperience/(?P<step>[-\w]+)/$', login_required(ExperienceWizard.as_view(FORMS, url_name='experience_edit_step', condition_dict={'experience':save_exit_experience, 'price': save_exit_price,'overview': save_exit_overview,
    #                                                                                                                                         'detail': save_exit_detail,'photo':save_exit_photo,
    #                                                                                                                                         'location':save_exit_location})), name='experience_edit_step'),
    url(r'^experiences/new/$', login_required(new_experience)),
    url(r'^manage-listing/(?P<exp_id>.*)/(?P<step>.*)/$', login_required(manage_listing), name='manage_listing'),
    # Continue the first incomplete step.
    url(r'^manage-listing-continue/(?P<exp_id>.*)/$', login_required(manage_listing_continue),
           name='manage_listing_continue'),

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
    url(r'^mytrip/$', 'app.views.mytrip'),
    url(r'^myprofile/$', 'app.views.myprofile'),
    url(r'^mylisting/$', 'app.views.mylisting', name="mylisting"),
    url(r'^myreservation/$', 'app.views.myreservation'),
    url(r'^mycalendar/$', 'app.views.mycalendar'),
    url(r'^reviewexperience/(?P<id>\d+)/$', 'experiences.views.review_experience', name='review_experience'),
    url(r'^booking_request/$', 'experiences.resource.booking_request'),
    url(r'^api-token-auth/', views.obtain_auth_token),
    url(r'^booking_request_xls/$', 'experiences.resource.saveBookingRequestsFromXLS'),
    #url(r'^experience_autosave$', ajax_view, name="ajax_view"),
    #url(r'^experience_availability/$', experience_availability, name='experience_availability'),
    url(r'^itinerary/$', custom_itinerary, name='custom_itinerary'),
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
    url(r'^experience_tags_xls/$', 'experiences.resource.updateExperienceTagsFromXLS'),
    url(r'^service_couponverification/$', 'experiences.resource.service_couponverification', name='service_couponverification'),
    url(r'^service_message/$', 'experiences.resource.service_message'),
    url(r'^service_message_list/$', 'experiences.resource.service_message_list'),
    url(r'^service_publicprofile/$', 'experiences.resource.service_publicprofile'),
    url(r'^service_experiencedetail/$', 'experiences.resource.service_experiencedetail'),
    url(r'^update_files/$', 'experiences.resource.update_files'),

    url(r'^custom_admin/$', superuser_required(ExperienceView.as_view()), name='custom_admin_index'),
    url(r'^custom_admin/booking$', superuser_required(BookingView.as_view()), name='admin_booking'),
    #url(r'^custom_admin/change_time/(?P<booking_id>\d+)$', BookingView.as_view()),
    url(r'^custom_admin/booking-archive/$', superuser_required(BookingArchiveView.as_view()), name='admin_booking_archive'),
    url(r'^custom_admin/payment/$', superuser_required(PaymentView.as_view()), name='admin_payment'),
    url(r'^custom_admin/experience/$', superuser_required(ExperienceView.as_view()), name='admin_experience'),
    url(r'^multidaytrip/$','experiences.views.multi_day_trip'),
    url(r'^unionpay_payment_callback/$','experiences.views.unionpay_payment_callback'),
    url(r'^wechat/product/$', 'app.views.wechat_product', name='wechat_product'),
    url(r'^wechat/(?P<id>\d+)/(?P<email>.*)/(?P<phone_num>.*)/notify/$',
                           'app.views.wechat_payment_notify', name='wechat_payment_notify'),
    url(r'^wechat/generate_order/$', 'app.views.generate_order', name='wechat_generate_order'),
    url(r'^wechat_payment_success/$', TemplateView.as_view(template_name="app/wechat_payment_success.html")),
)
