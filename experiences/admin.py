from django.contrib import admin
from django.conf.urls import patterns
from experiences.models import Experience, Photo, WhatsIncluded, Review, Booking, Coupon
from experiences.views import create_experience
from app.models import RegisteredUser
from allauth.socialaccount.models import SocialAccount
from post_office.models import Email

class ExperienceAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(ExperienceAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^add/$', self.admin_site.admin_view(create_experience)),
            (r'^(?P<id>\d+)/$', self.admin_site.admin_view(create_experience)),
        )
        return my_urls + urls

admin.site.register(Experience, ExperienceAdmin)
admin.site.register(Photo)
admin.site.register(WhatsIncluded)
admin.site.register(RegisteredUser)
admin.site.register(Review)
admin.site.register(Booking)
admin.site.register(Coupon)
#admin.site.register(Email)
#admin.site.register(SocialAccount)

