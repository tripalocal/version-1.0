from django.contrib import admin
from django.conf.urls import patterns
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from experiences.models import Experience, Photo, WhatsIncluded, Review, Booking, Coupon, WechatProduct, WechatBooking, \
    NewProduct, NewProductI18n, Provider, Payment, Coordinate
from experiences.views import create_experience, saveExperienceImage
from app.models import RegisteredUser
from allauth.socialaccount.models import SocialAccount
from post_office.models import Email
from Tripalocal_V1 import settings
import os

class ExperienceAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(ExperienceAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^add/$', self.admin_site.admin_view(create_experience)),
            (r'^(?P<id>\d+)/$', self.admin_site.admin_view(create_experience)),
        )
        return my_urls + urls

class WechatBookingAdmin(admin.ModelAdmin):
     list_display = ('product', 'email', 'phone_num', 'paid')


class ProviderInline(admin.StackedInline):
    model = Provider
    can_delete = False


class UserAdmin(UserAdmin):
    inlines = (ProviderInline,)


class ProductI18nInline(admin.StackedInline):
    model = NewProductI18n
    verbose_name = "Product detail"
    extra = 1


class ProductPhotoInline(admin.TabularInline):
    model = Photo
    extra = 3

class ExperienceCoordinateInline(admin.TabularInline):
    model = Coordinate
    extra = 5

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductPhotoInline, ProductI18nInline, ExperienceCoordinateInline]

    def get_queryset(self, request):
        qs = super(ProductAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(suppliers__id__exact=Provider.objects.get(id=request.user.id).id)

    # def get_form(self, request, obj=None, **kwargs):
        # fieldsets = (
        #     ('Admin', {'fields': ('provider', 'status',)}),
        #     ('Product summary', {
        #         'fields': (
        #             'city', 'duration', 'min_group_size', 'max_group_size', 'book_in_advance', 'instant_booking',
        #             'free_translation',
        #             'order_on_holiday')
        #     }),
        #     ('Pricing rule', {
        #         'fields': ('price_type', 'normal_price', 'dynamic_price', 'adult_price', 'children_price', 'adult_age')
        #     }),
        # )
        #
        # fieldsets2 = (
        #     ('Product summary', {
        #         'fields': (
        #             'city', 'duration', 'min_group_size', 'max_group_size', 'book_in_advance', 'instant_booking',
        #             'free_translation',
        #             'order_on_holiday')
        #     }),
        #     ('Pricing rule', {
        #         'fields': ('price_type', 'normal_price', 'dynamic_price', 'adult_price', 'children_price', 'adult_age')
        #     }),
        # )
        # if not request.user.is_superuser:
        #     self.fieldsets = fieldsets2
        # else:
        #     self.fieldsets = fieldsets
        # return super(ProductAdmin, self).get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and len(obj.suppliers.filter(user_id__in=[request.user.id])) == 0:
            obj.suppliers.add(Provider.objects.get(id=request.user.id))
        super(ProductAdmin, self).save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        if request.FILES and len(request.FILES) > 0 and formset.prefix == 'photo_set':
            instances = formset.save(commit=False)
            for obj in formset.deleted_objects:
                obj.delete()
            i = 0

            for instance in instances:
                id = instance.experience.id
                i = len(Photo.objects.filter(experience_id=id))
                photo = request.FILES['photo_set-' + str(i) + '-image']
                name, extension = os.path.splitext(photo.name)

                saveExperienceImage(instance.experience, photo, extension, i+1)

                i += 1
            formset.save_m2m()
        else:
            super(ProductAdmin, self).save_formset(request, form, formset, change)

class ProviderAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(ProviderAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = []
        if not request.user.is_superuser:
            self.exclude.append('user')
        return super(ProviderAdmin, self).get_form(request, obj, **kwargs)

class BookingAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(BookingAdmin,self).get_form(request, obj,**kwargs)
        # form class is created per request by modelform_factory function
        # so it's safe to modify
        #we modify the the queryset
        if obj is not None:
            form.base_fields['host'].queryset = form.base_fields['host'].queryset.filter(id=obj.experience.get_host(obj).id)
        return form

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Payment)
admin.site.register(Experience, ExperienceAdmin)
admin.site.register(Photo)
admin.site.register(WhatsIncluded)
admin.site.register(RegisteredUser)
admin.site.register(Review)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Coupon)
admin.site.register(WechatProduct)
admin.site.register(WechatBooking, WechatBookingAdmin)
admin.site.register(NewProduct, ProductAdmin)
admin.site.register(Provider, ProviderAdmin)
#admin.site.register(Email)
#admin.site.register(SocialAccount)

