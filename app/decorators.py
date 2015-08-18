__author__ = 'lyy'

import json

from django.http import HttpResponse,Http404
from django.core.exceptions import ImproperlyConfigured

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
                    return decorated_function(request, *args, **kwargs)
            except:
                raise ImproperlyConfigured('Please set a right form class!')
        return  wrapped_function
    return wrap
