def isEnglish(s):
    try:
        s.decode('ascii') if isinstance(s, bytes) else s.encode('ascii')
    except UnicodeDecodeError:
        return False
    except UnicodeEncodeError:
        return False
    else:
        return True

def get_total_price(experience, guest_number, adult_number=0, children_number=0):
    '''
    return total price, not including commission or service fee
    either use guest_number, or adult_number + children_number, the latter has a higher priority
    '''
    if adult_number > 0 or children_number > 0:
        guest_number = adult_number

    subtotal_price = 0.0    
    if experience.children_price is not None and experience.children_price > 0:
        subtotal_price += float(experience.children_price) * float(children_number)
    else:
        guest_number += children_number

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
        subtotal_price += float(experience.price)*float(guest_number)

    return subtotal_price