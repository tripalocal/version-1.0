"""
Definition of views.
"""

from django.shortcuts import render, render_to_response
from django.http import HttpRequest, HttpResponseRedirect
from django.template import RequestContext, loader
from datetime import datetime
from django import forms
from django.contrib.auth import authenticate, login
from app.forms import UserCreateForm
from allauth.account.signals import password_reset
from allauth.account.views import PasswordResetFromKeyDoneView 
from django.dispatch import receiver
from app.forms import SubscriptionForm
from app.models import Subscription
from django.core.mail import send_mail
from django.contrib import messages
import string, random, pytz

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

def home(request):
    """Renders the home page."""

    context = RequestContext(request)
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            try: 
                Subscription.objects.get(email = form.data['email'])
                messages.add_message(request, messages.INFO, 'It seems you already subscribed. Thank you.')
            except Subscription.DoesNotExist:
                ref = request.GET.get('ref')
                ref_link=id_generator(size=8)

                try:
                    ref_by = Subscription.objects.get(ref_link = ref)
                    new_sub = Subscription(email = form.data['email'], subscribed_datetime = datetime.utcnow().replace(tzinfo=pytz.utc), ref_by = ref_by.email, ref_link=ref_link)
                    #send an email to the referal
                    counter = len(Subscription.objects.filter(ref_by = ref_by.email))
                    if counter%5 < 4:
                        send_mail('[Tripalocal] Someone has signed up because of you!', '', 'Tripalocal <enquiries@tripalocal.com>',
                                    [ref_by.email], fail_silently=False, 
                                    html_message=loader.render_to_string('app/email_new_referral.html', {'ref_url':'http://www.tripalocal.com?ref='+ref_by.ref_link, 'counter':counter%5+1, 'left':5-1-counter%5}))
                    else:
                        send_mail('[Tripalocal] Free experience!', '', 'Tripalocal <enquiries@tripalocal.com>',
                                    [ref_by.email], fail_silently=False, 
                                    html_message=loader.render_to_string('app/email_free_experience.html', {'ref_url':'http://www.tripalocal.com?ref='+ref_by.ref_link}))
                except Subscription.DoesNotExist:
                    new_sub = Subscription(email = form.data['email'], subscribed_datetime = datetime.utcnow().replace(tzinfo=pytz.utc), ref_link=ref_link)
                finally:    
                    new_sub.save()
                    #send an email to the new subscriber
                    send_mail('[Tripalocal] Welcome', '', 'Tripalocal <enquiries@tripalocal.com>',
                                [form.data['email']], fail_silently=False, html_message=loader.render_to_string('app/email_welcome.html', {'ref_url':'http://www.tripalocal.com?ref='+ref_link}))
                    #messages.add_message(request, messages.INFO, 'Thank you for subscribing.')
                    return render_to_response('app/welcome.html', {'ref_url':'http://www.tripalocal.com?ref='+ref_link}, context)
    else:
        form = SubscriptionForm()
    return render_to_response('app/index.html', {'form': form, 'subscribed':"none"}, context)

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        context_instance = RequestContext(request,
        {
            'title':'Contact',
            'message':'Your contact page.',
            'year':datetime.now().year,
        })
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        context_instance = RequestContext(request,
        {
            'title':'About',
            'message':'Your application description page.',
            'year':datetime.now().year,
        })
    )

def signup(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            new_user = authenticate(username=request.POST['username'],
                                    password=request.POST['password1'])
            login(request, new_user)
            return HttpResponseRedirect("/")
    else:
        form = UserCreateForm()
    return render(request, "app/signup.html", {
        'form': form,
    })

def registration_successful(request):

    if request.user.is_authenticated():
        #send an email
        send_mail('[Tripalocal] Successfully registered', '', 'Tripalocal <enquiries@tripalocal.com>',
                    [request.user.email], fail_silently=False, html_message=loader.render_to_string('app/email_registration_successful.html'))
        return render(
            request,
            'app/registration_successful.html',
            context_instance = RequestContext(request, {})
        )
    else:
        return HttpResponseRedirect("/accounts/login/")

@receiver(password_reset)
def password_reset(request, user, **kwargs):
    PasswordResetFromKeyDoneView.user_reset = user
    PasswordResetFromKeyDoneView.reset_datetime = datetime.utcnow()

def current_datetime(request):
    import datetime
    return {'current_datetime':datetime.datetime.utcnow()}

def disclaimer(request):
    
    return render(
        request,
        'app/disclaimer.html',
        context_instance = RequestContext(request)
    )


def ByCityExperienceListView(request, city):
    return render_to_response('app/index.html', {'form': form, 'subscribed':"none"}, context)
