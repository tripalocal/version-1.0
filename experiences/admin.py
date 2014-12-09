from django.contrib import admin
from experiences.models import Experience, Photo, WhatsIncluded, RegisteredUser

admin.site.register(Experience)
admin.site.register(Photo)
admin.site.register(WhatsIncluded)
admin.site.register(RegisteredUser)
