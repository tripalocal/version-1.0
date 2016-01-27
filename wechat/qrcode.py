#https://mp.weixin.qq.com/debug/cgi-bin/apiinfo?t=index&type=%E6%8E%A8%E5%B9%BF%E6%94%AF%E6%8C%81&form=%E6%8D%A2%E5%8F%96%E4%BA%8C%E7%BB%B4%E7%A0%81%E6%8E%A5%E5%8F%A3%20/showqrcode
#http://mp.weixin.qq.com/wiki/18/28fc21e7ed87bec960651f0ce873ef8a.html

import json, requests, os
from django.http import HttpResponseRedirect
from io import BytesIO
from Tripalocal_V1 import settings

APPID = "wx6e6dfd80262310ec"
APPSECRET = ""

def get_token(APPID, APPSECRET):
    args = {'APPID': APPID,'APPSECRET': APPSECRET}
    url_token = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
    url_token = url_token.format(**args)
    response = requests.get(url_token)
    token = None
    if response.status_code == 200:
        token = json.loads(response.text).get("access_token", None)
    return token

def generate_ticket(TOKEN, scene_id, scene_str, permanent=True):
    url_ticket = "https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token={TOKEN}"
    url_ticket = url_ticket.format({"TOKEN":TOKEN})
    args_temp = {"expire_seconds": 604800, "action_name": "QR_SCENE", "action_info": {"scene": {"scene_id": scene_id, "scene_str": scene_str}}}
    args_permanent = {"action_name": "QR_LIMIT_SCENE", "action_info": {"scene": {"scene_id": scene_id, "scene_str": scene_str}}}
    if permanent:
        args = args_permanent
    else:
        args = args_temp

    response = requests.post(url = url_ticket, data = args)
    ticket = None
    url = None
    if response.status_code == 200:
        ticket = json.loads(response.text).get("ticket", None)
        url = json.loads(response.text).get("url", None)
    return ticket

def get_qrcode(ticket,scene_id):
    url_qrcode = "https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket={TICKET}"
    url_qrcode = url_qrcode.format({"TICKET":ticket})
    response = requests.get(url_qrcode)
    path = None
    if response.status_code == 200:
        file = request.FILES['file']
        path = os.path.join(os.path.join(settings.PROJECT_ROOT, 'qrcode'),file.name).replace('\\', '/')
        with open(path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        path = os.path.join('/qrcode',file.name)
    return path

def qrcode(request):
    if not request.user.is_authenticated() or not request.user.is_staff:
        return HttpResponseRedirect("/")

    scene_id = request.GET.get("scene_id",None)
    scene_str = request.GET.get("scene_str", None)
    permanent = reqeust.GET.get("permanent", None)
    token = get_token(APPID, APPSECRET)
    if token and scene_id and scene_str and permanent:
        ticket = generate_ticket(token, scene_id, scene_str, permanent)
        if ticket:
            path = get_qrcode(ticket, scene_id)
            return HttpResponseRedirect(path)

    return HttpResponseRedirect("/")
    