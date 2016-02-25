# -*- coding=utf-8 -*-

import hashlib
import re
from random import Random
import requests


def smart_str(v):
    s = str(v)
    return s

def format_url(params, api_key=None):
    url = "&".join(['%s=%s' % (key, params[key]) for key in sorted(params) if params[key]])
    if api_key:
        url = '%s&key=%s' % (url, api_key)
    return url


def calculate_sign(params, api_key):
    #签名步骤一：按字典序排序参数, 在string后加入KEY
    encoded_url = format_url(params, api_key).encode('utf-8')
    #签名步骤二：MD5加密, 所有字符转为大写
    return hashlib.md5(encoded_url).hexdigest().upper()


def dict_to_xml(params, sign=None):
    xml = ["<xml>",]
    for (k, v) in params.items():
        if (v.isdigit()):
            xml.append('<%s>%s</%s>' % (k, v, k))
        else:
            xml.append('<%s><![CDATA[%s]]></%s>' % (k, v, k))
    if sign:
        xml.append('<sign><![CDATA[%s]]></sign></xml>' % sign)
    else:
        xml.append('</xml>')
    return ''.join(xml)


def xml_to_dict(xml):
    if xml[0:5].upper() != "<XML>" and xml[-6].upper() != "</XML>":
        return None, None

    result = {}
    sign = None
    content = ''.join(xml[5:-6].strip().split('\n'))

    pattern = re.compile(r"<(?P<key>.+)>(?P<value>.+)</(?P=key)>")
    m = pattern.match(content)
    while(m):
        key = m.group("key").strip()
        value = m.group("value").strip()
        if value != "<![CDATA[]]>":
            pattern_inner = re.compile(r"<!\[CDATA\[(?P<inner_val>.+)\]\]>")
            inner_m = pattern_inner.match(value)
            if inner_m:
                value = inner_m.group("inner_val").strip()
            if key == "sign":
                sign = value
            else:
                result[key] = value

        next_index = m.end("value") + len(key) + 3
        if next_index >= len(content):
            break
        content = content[next_index:]
        m = pattern.match(content)

    return sign, result


def validate_post_xml(xml, appid, mch_id, api_key):
    sign, params = xml_to_dict(xml)
    if (not sign) or (not params):
        return None

    remote_sign = calculate_sign(params, api_key)
    if sign != remote_sign:
        return None

    if params["appid"] != appid or params["mch_id"] != mch_id:
        return None

    return params


def random_str(randomlength=8):
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    random = Random()
    return "".join([chars[random.randint(0, len(chars) - 1)] for i in range(randomlength)])


def post_xml(url, xml):
    return requests.post(url, data=xml)
