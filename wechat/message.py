import requests, logging
from hashlib import sha1
from rest_framework import status
from rest_framework.decorators import api_view
from django.http import HttpResponse
from xml.etree import ElementTree

@api_view(['GET'])
def receive_message(request):
    data = request.GET
    signature = data.get("signature", None)
    timestamp = data.get("timestamp", None)
    nonce = data.get("nonce", None)
    echostr = data.get("echostr", None)

    if signature and timestamp and nonce:
        logger = logging.getLogger("Tripalocal_V1")
        token = "tripalocalqwer"
        sorted_string = ''.join(sorted((token, timestamp, nonce)))
        sorted_string = sha1(sorted_string.encode('utf-8'))

        #logger.info(sorted_string.hexdigest() + " " + signature + \
        #            timestamp + " " + nonce + " " + echostr)
        if sorted_string.hexdigest() == signature:
            logger.info(request.raw_post_data)
            return HttpResponse(echostr)
        else:
            return HttpResponse("wrong signature")
    else:
        return HttpResponse("missing parameters")
