import datetime, time
import json
import requests

stored_token = None
token_received_time = 0
token_expire_period = 3599

TOKEN_URL = "https://api.telstra.com/v1/oauth/token"
SEND_MSG_URL = "https://api.telstra.com/v1/sms/messages"
CONSUMER_KEY = "WEGYCLEzmzEdQdZSFdBCnlIRAAtdxGK1"
CONSUMER_SECRET = "nGAf7Heze8vO4M1C"


def request_new_token():
    global stored_token, token_expire_period, token_received_time
    payload = {'client_id': CONSUMER_KEY, 'client_secret': CONSUMER_SECRET, 'grant_type': 'client_credentials',
               'scope': 'SMS'}
    r = requests.post(TOKEN_URL, data=payload)
    # r.status_code
    content = r.json()
    stored_token = content['access_token']
    token_expire_period = int(content['expires_in'])
    token_received_time = time.mktime(datetime.datetime.now().timetuple())
    return stored_token


def get_auth_token():
    now = time.mktime(datetime.datetime.now().timetuple())
    if now > token_received_time + token_expire_period:
        return request_new_token()
    else:
        return stored_token


def send_sms(phone_num, msg):
    token = get_auth_token()
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
    payload = {'to': phone_num, 'body': msg}
    requests.post(SEND_MSG_URL, headers=headers, data=json.dumps(payload))

