import logging
from django.http import HttpResponseServerError

class ForceDefaultLanguageMiddleware(object):
    """
    Ignore Accept-Language HTTP headers
    
    This will force the I18N machinery to always choose settings.LANGUAGE_CODE
    as the default initial language, unless another one is set via sessions or cookies
    
    Should be installed *before* any middleware that checks request.META['HTTP_ACCEPT_LANGUAGE'],
    namely django.middleware.locale.LocaleMiddleware
    """
    def process_request(self, request):
        if 'HTTP_ACCEPT_LANGUAGE' in request.META:
            del request.META['HTTP_ACCEPT_LANGUAGE']

#http://stackoverflow.com/questions/3823280/ioerror-request-data-read-error
class HandleExceptionMiddleware:

    def process_exception(self, request, exception):
        if isinstance(exception, OSError) and 'request data read error' in unicode(exception):
            logging.getLogger("Tripalocal_V1").info('%s %s: %s: Request was canceled by the client.' % (
                    request.build_absolute_uri(), request.user, exception))
            return HttpResponseServerError()