__author__ = 'lyy'

import json

from django.http import HttpResponse,Http404
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME

def ajax_form_validate(form_class=None):
    def wrap(decorated_function):
        def wrapped_function(request, *args, **kwargs):
            try:
                init_data = dict()
                for attr in request.POST:
                    if attr in form_class.__dict__['base_fields']:
                        init_data[attr] = request.POST[attr]
                form = form_class(data = init_data)
                form.is_bound = True
                if not form.is_valid():
                    return HttpResponse(json.dumps({'success': False, "server_info": 'Form validate Failed.'}), content_type='application/json')
                else:
                    return decorated_function(request, form=form, *args, **kwargs)
            except:
                raise ImproperlyConfigured('Please set a right form class!')
        return  wrapped_function
    return wrap


def superuser_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

