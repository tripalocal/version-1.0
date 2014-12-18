from django.contrib import admin
from experiences.models import Experience, Photo, WhatsIncluded, RegisteredUser, Review

admin.site.register(Experience)
admin.site.register(Photo)
admin.site.register(WhatsIncluded)
admin.site.register(RegisteredUser)
admin.site.register(Review)

