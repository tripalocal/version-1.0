import os, pytz, string, random, decimal

from Tripalocal_V1 import settings
from unionpay.util.helper import load_config

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

def get_total_price(experience, guest_number=0, adult_number=0, child_number=0):
    '''
    return total price, not including commission or service fee
    either use guest_number, or adult_number + child_number, the latter has a higher priority
    '''
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