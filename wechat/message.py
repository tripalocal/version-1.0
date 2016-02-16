import requests, logging
from rest_framework import status
from rest_framework.response import Response

def receive_message(request):
    data = request.data
    logger = logging.getLogger("Tripalocal_V1")
    logger.info(data)
    return Response({"success":True}, status=status.HTTP_200_OK)