from django.conf import settings

def geo_postfix(request):
    return {'GEO_POSTFIX': settings.GEO_POSTFIX}
