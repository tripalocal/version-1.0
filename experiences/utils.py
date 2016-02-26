import os, pytz, string, random, decimal, requests, json
from PIL import Image, ImageEnhance

from Tripalocal_V1 import settings
from unionpay.util.helper import load_config
from datetime import timedelta, date
from copy import deepcopy

def isEnglish(s):
    try:
        s.decode('ascii') if isinstance(s, bytes) else s.encode('ascii')
    except UnicodeDecodeError:
        return False
    except UnicodeEncodeError:
        return False
    else:
        return True

def experience_fee_calculator(price, commission_rate):
    if type(price)==int or type(price) == float:
        COMMISSION_PERCENT = round(commission_rate/(1-commission_rate),3)
        return round(price*(1.00+COMMISSION_PERCENT), 0)*(1.00+settings.STRIPE_PRICE_PERCENT) + settings.STRIPE_PRICE_FIXED

    return price

def convert_currency(price, current_currency, target_currency, conversion=None):
    '''
    add the parameter of "conversion" to avoid reading local files
    '''
    if not (type(price)==int or type(price) == float or type(price) == decimal.Decimal):
        return price
    if not conversion:
        file_name = 'experiences/currency_conversion_rate/' + current_currency.upper() + '.yaml'
        conversion = load_config(os.path.join(settings.PROJECT_ROOT, file_name).replace('\\', '/'))
    return round(float(price)*float(conversion.get(target_currency.upper(), 1.00)), 2)

def get_total_price(experience, guest_number=0, adult_number=0, child_number=0, extra_information=None, language=None):
    '''
    return total price, not including commission or service fee
    either use guest_number, or adult_number + child_number, the latter has a higher priority
    extra_information: for experienceoz products, it indicates which optionitem is chosen, e.g., {"1243":1, "2344":2}
    '''
    if extra_information:
        price = 0
        i = 0
        items = json.loads(extra_information)
        language = settings.LANGUAGES[0][0] if language is None else language
        for og in experience.optiongroup_set.filter(language=language):
            for oi in og.optionitem_set.all():
                if str(oi.original_id) in items.keys():
                    price += oi.price*items.get(str(oi.original_id))
                    i += 1
                    if i == len(items.keys()):
                        break
            if i == len(items.keys()):
                break
        if i == len(items.keys()):
            if experience.currency.lower() != "aud":
                price = convert_currency(price, "aud", experience.currency)
            return price
        else:
            raise ValueError("OptionItem mismatch")

    if type(guest_number) != int or guest_number < 0:
        guest_number = 0
    if type(adult_number) != int or adult_number < 0:
        adult_number = 0
    if type(child_number) != int or child_number < 0:
        child_number = 0

    if adult_number > 0 or child_number > 0:
        guest_number = adult_number

    subtotal_price = 0.0
    if experience.children_price is not None and experience.children_price > 0:
        subtotal_price += float(experience.children_price) * float(child_number)
    else:
        guest_number += child_number

    if experience.dynamic_price and type(experience.dynamic_price) == str:
        price = experience.dynamic_price.split(',')
        if len(price)+experience.guest_number_min-2 == experience.guest_number_max:
        #these is comma in the end, so the length is max-min+2
            if guest_number <= experience.guest_number_min:
                subtotal_price += float(experience.price) * float(experience.guest_number_min)
            else:
                subtotal_price += float(price[guest_number-experience.guest_number_min]) * float(guest_number)
        else:
            #wrong dynamic settings
            subtotal_price += float(experience.price)*float(guest_number)
    else:
        if guest_number <= experience.guest_number_min:
            subtotal_price += float(experience.price) * float(experience.guest_number_min)
        else:
            subtotal_price += float(experience.price)*float(guest_number)

    return subtotal_price + experience.fixed_price

def get_timezone(city):
    timezones = load_config(os.path.join(settings.PROJECT_ROOT, 'experiences/time_zone/time_zone.yaml').replace('\\', '/'))
    return timezones.get(city.lower(), settings.TIME_ZONE)

def email_account_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def get_weather(lat, lon, time):
    api_address = "https://api.forecast.io/forecast/0a73fa455425979752f12c2afe2441ba/" + str(lat) + "," + str(lon) + "," + str(time)
    payload = {'units': 'si', 'exclude': 'currently,minutely,hourly,alerts,flags'}
    r = requests.get(api_address, params=payload)
    if r.status_code is requests.codes.ok:
        return r.json()
    else:
        r.raise_for_status()

def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

@static_vars(dict={"Melbourne":{"max_experience_id":0,"experiences":[],"itineraries_last_updated":"2000-01-01 00:00:00","daily_itineraries":[]}})
def recent_search(action, new_search=None):
    '''
    action: get, update, clear
    new_search: add the new item to the dict/update an existing item
    '''
    if action is not None:
        if action.lower()=="get":
            return recent_search.dict
        elif action.lower()=="update" and new_search is not None:
            for k, v in new_search.items():
                if k not in recent_search.dict:
                    recent_search.dict[k] = deepcopy(v)
                else:
                    for experience in v['experiences']:
                        if recent_search.dict[k]['max_id'] < experience['id']:
                            recent_search.dict[k]['experiences'].append(experience)
                    recent_search.dict[k]['max_id'] = v['max_id']
        elif action.lower()=="clear":
            recent_search.dict.clear()

#http://code.activestate.com/recipes/362879-watermark-with-pil/
def reduce_opacity(im, opacity):
    """Returns an image with reduced opacity."""
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im

def watermark(im, mark, position, opacity=1):
    """Adds a watermark to an image."""
    if opacity < 1:
        mark = reduce_opacity(mark, opacity)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    # create a transparent layer the size of the image and draw the
    # watermark in that layer.
    layer = Image.new('RGBA', im.size, (0,0,0,0))
    if position == 'tile':
        for y in range(0, im.size[1], mark.size[1]):
            for x in range(0, im.size[0], mark.size[0]):
                layer.paste(mark, (x, y))
    elif position == 'scale':
        # scale, but preserve the aspect ratio
        ratio = min(float(70) / mark.size[0], float(70) / mark.size[1])
        w = int(mark.size[0] * ratio)
        h = int(mark.size[1] * ratio)
        mark = mark.resize((w, h))
        layer.paste(mark, ((im.size[0] - w), (im.size[1] - h)))
    else:
        layer.paste(mark, position)
    # composite the watermark with the layer
    return Image.composite(layer, im, layer)

#im = Image.open('test.png')
#mark = Image.open('overlay.png')
#watermark(im, mark, 'tile', 0.5).show()
#watermark(im, mark, 'scale', 1.0).show()
#watermark(im, mark, (100, 100), 0.5).show()