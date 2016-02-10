import json, os, collections, requests, pytz, base64, sys, string, http.client, ast
from allauth.account.signals import user_signed_up
from datetime import *
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponseRedirect
from experiences.models import NewProduct, NewProductI18n, Provider, OptionGroup, OptionItem, Coordinate
from experiences.views import saveExperienceImage
from experiences.utils import isEnglish
from io import BytesIO
from Tripalocal_V1 import settings
from xml.etree import ElementTree
from import_from_partners.utils import *

username = '7254'
password = 'dHJpcGFsb2NhbFRyaXBhbG9jYWwgUHR5IEx0ZA=='
auth = username + ':' + password
auth = base64.b64encode(auth.encode('ascii'))

def import_experienceoz_products(request):
    if not request.user.is_authenticated() or not request.user.is_staff:
        return HttpResponseRedirect("/")

    if settings.LANGUAGES[0][0] == "zh":
        url_template = "https://tripalocal.experienceoz.com.au/zh/api/syncData?startDate={start_date}&endDate={end_date}&dataType=Product&offset={offset}"
    else:
        url_template = "https://tripalocal.experienceoz.com.au/api/syncData?startDate={start_date}&endDate={end_date}&dataType=Product&offset={offset}"

    start_date = (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")
    end_date = datetime.now().strftime("%d/%m/%Y")
    offset = 0
    current_page = 0
    total_page = 1

    while current_page < total_page:
        kwargs = {
            'start_date': start_date,
            'end_date': end_date,
            'offset': current_page,
        }
        url = url_template.format(**kwargs)
    
        response = requests.get(url,
                                auth=requests.auth.HTTPBasicAuth(
                                username,
                                password))
        if response.status_code == 200 and response.reason == "OK":
            updates = json.loads(response.text)
            current_page += 1
            total_page = int(updates["totalPages"])
            products = updates["productList"]
            partner_id = PARTNER_IDS['experienceoz']
            #the ids of products imported from partners will be in the format:
            #<the original id at the partner side><partner_id><length_of_partner_id>
            #e.g., 59340013
            keys = ["id", "name", "operatorName", "operatorPublicName", "urlSegment",\
                    "bookingRequired", "bookingNotesRequired", "bookingNotesPlaceholder",\
                    "availabilityModel", "description", "productOptionGroups",\
                    "moreInfo", "image", "hotDealMessage", "status", "operatorId", "operatorUrl",\
                    "primaryRegionId", "primaryRegionUrl", "primaryCategoryId", "primaryCategoryUrl",\
                    "timestamp"]

            target_language = settings.LANGUAGES[0][0]
            missing_operators = []
            for product in products:
                product = collections.OrderedDict(sorted(product.items()))
                for key, value in product.items():
                    if key not in keys:
                        raise Exception("New key: " + str(key))

                #add str(len(partner_id))), in case one partner's id is a postfix of another id
                pid = int(str(product['id']) + partner_id + str(len(partner_id)))
                oid = int(str(product['operatorId']) + partner_id + str(len(partner_id)))
                try:
                    operator = Provider.objects.get(user_id=oid)
                except Provider.DoesNotExist:
                    operator = None #get_operator(product['operatorUrl'], partner_id, request)
                if operator:
                    np = NewProduct.objects.filter(abstractexperience_ptr_id = pid)
                    if len(np) > 0:
                        np = np[0]
                    else:
                        np = NewProduct()
                        np.id = pid
                        np.partner = partner_id
                        np.city = convert_location(product['primaryRegionUrl'] if product['primaryRegionUrl'] else "")
                        np.type = product['primaryCategoryUrl'] if product['primaryCategoryUrl'] else ""
                        np.price = 0
                        np.fixed_price = 0
                        np.duration = 1
                        np.guest_number_min = 1
                        np.guest_number_max = 10
                        np.commission = 0
                        np.start_datetime = pytz.timezone("UTC").localize(datetime.utcnow())
                        np.end_datetime = np.start_datetime + timedelta(weeks = 520)

                        np.save()

                        if len(np.suppliers.filter(user_id=oid)) == 0:
                            np.suppliers.add(operator)
                            np.save()

                    npi18n = np.newproducti18n_set.filter(product_id=np.id, language=target_language)
                    if len(npi18n) > 0:
                        npi18n = npi18n[0]
                    else:
                        npi18n = NewProductI18n()
                    npi18n.language = target_language
                    npi18n.title = product['name'] if product['name'] else ""
                    npi18n.background_info = product['urlSegment'] if product['urlSegment'] else ""
                    np.book_in_advance = product['bookingRequired']
                    if product['bookingNotesRequired']:
                        npi18n.ticket_use_instruction = product['bookingNotesPlaceholder'] if product['bookingNotesPlaceholder'] else ""
                    npi18n.description = product['description'] if product['description'] else ""
                    npi18n.combination_options = product['productOptionGroups'] if product['productOptionGroups'] else ""
                    npi18n.service = product['moreInfo'] if product['moreInfo'] else ""
                    npi18n.notice = product['hotDealMessage'] if product['hotDealMessage'] else ""
                    npi18n.location = product['primaryRegionUrl'] if product['primaryRegionUrl'] else ""

                    npi18n.product = np
                    npi18n.save()

                    for group in npi18n.combination_options:
                        og = OptionGroup.objects.filter(original_id=group.get("id"), language = npi18n.language)
                        if len(og) > 0:
                            og = og[0]
                            og.name = group.get("groupName")
                        else:
                            og = OptionGroup(product = np, name = group.get("groupName"), language = npi18n.language, original_id = group.get("id"))
                        og.save()
                        for option in group.get("productOptions"):
                            oi = OptionItem.objects.filter(original_id=option.get("id"), group_id=og.id)
                            if len(oi) > 0:
                                oi = oi[0]
                                oi.name = option.get("name")
                            else:
                                oi_other = OptionItem.objects.filter(original_id=option.get("id"))
                                price = 0
                                retail_price = 0
                                if len(oi_other) > 0:
                                    oi_other = oi_other[0]
                                    price = oi_other.price
                                    retail_price = oi_other.retail_price
                                oi = OptionItem(group = og, name = option.get("name"), price = price, retail_price = retail_price,
                                                original_id = option.get("id"))
                            oi.save()

                    #extension = "." + product['image'].split(".")[-1]
                    #response = requests.get(product['image'])
                    #if response.status_code == 200:
                    #    image_io = BytesIO(response.content)
                    #    image_io.seek(0, 2)  # Seek to the end of the stream, so we can get its length with `image_io.tell()`
                    #    image_file = InMemoryUploadedFile(image_io, None, product['image'].split("/")[-1], "image", image_io.tell(), None, None)
                    #    saveExperienceImage(np, image_file, extension, 1)
                elif product['operatorId'] not in missing_operators:
                    missing_operators.append(product['operatorId'])
                    print(product['operatorId'])
        else:
            raise Exception("Error in updating products")

    #products = NewProduct.objects.filter(partner = PARTNER_IDS["experienceoz"])
    #for np in products:
    #    npi18ns = np.newproducti18n_set.all()
    #    for npi18n in npi18ns:
    #        if npi18n.combination_options is None or len(npi18n.combination_options) == 0:
    #            continue
    #        try:
    #            groups = ast.literal_eval(npi18n.combination_options)
    #        except SyntaxError:
    #            #print(npi18n.id)
    #            continue
    #        for group in groups:
    #            og = OptionGroup.objects.filter(original_id=group.get("id"), language = npi18n.language)
    #            if len(og) > 0:
    #                og = og[0]
    #                og.name = group.get("groupName")
    #            else:
    #                og = OptionGroup(product = np, name = group.get("groupName"), language = npi18n.language, original_id = group.get("id"))
    #            og.save()
    #            for option in group.get("productOptions"):
    #                oi = OptionItem.objects.filter(original_id=option.get("id"), group_id=og.id)
    #                if len(oi) > 0:
    #                    oi = oi[0]
    #                    oi.name = option.get("name")
    #                else:
    #                    oi_other = OptionItem.objects.filter(original_id=option.get("id"))
    #                    price = 0
    #                    retial_price = 0
    #                    if len(oi_other) > 0:
    #                        oi_other = oi_other[0]
    #                        price = oi_other.price
    #                        retail_price = oi_other.retail_price
    #                    oi = OptionItem(group = og, name = option.get("name"), price = price, retail_price = retail_price,
    #                                    original_id = option.get("id"))
    #                oi.save()

    return HttpResponseRedirect("/")

def import_experienceoz_operators(request):
    if not request.user.is_authenticated() or not request.user.is_staff:
        return HttpResponseRedirect("/")

    partner_id = PARTNER_IDS['experienceoz']
    #folder = os.path.join(settings.PROJECT_ROOT, 'import_from_partners', 'experienceoz_operators')
    #for filename in os.listdir(folder):
    #    if os.path.isfile(os.path.join(folder, filename)):
    #        with open(os.path.join(folder, filename), "rb") as file:
    #            operators = json.loads(file.read().decode('utf-8'))['operators']
    #            for operator in operators:
    #                create_operator(operator, partner_id, request)

    if settings.LANGUAGES[0][0] == "zh":
        url_template = "https://tripalocal.experienceoz.com.au/zh/api/syncData?startDate={start_date}&endDate={end_date}&dataType=Operator&offset={offset}"
    else:
        url_template = "https://tripalocal.experienceoz.com.au/api/syncData?startDate={start_date}&endDate={end_date}&dataType=Operator&offset={offset}"

    start_date = (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")
    end_date = datetime.now().strftime("%d/%m/%Y")
    offset = 0
    current_page = 0
    total_page = 1

    while current_page < total_page:
        kwargs = {
            'start_date': start_date,
            'end_date': end_date,
            'offset': current_page,
        }
        url = url_template.format(**kwargs)
    
        response = requests.get(url,
                                auth=requests.auth.HTTPBasicAuth(
                                username,
                                password))
        if response.status_code == 200 and response.reason=="OK":
            updates = json.loads(response.text)
            current_page += 1
            total_page = int(updates["totalPages"])
            operators = updates["operators"]
            partner_id = PARTNER_IDS['experienceoz']
            for operator in operators:
                create_operator(operator, partner_id, request)
        else:
            raise Exception("Error in updating operators")

    return HttpResponseRedirect("/")

def create_operator(operator, partner_id, request):
    oid = int(str(operator['id']) + partner_id + str(len(partner_id)))
    email = "experienceoz_" + str(operator['id']) + ".user@tripalocal.com"
    user = User.objects.filter(id = oid)
    if len(user) > 0:
        user = user[0]
    else:
        user = User(id = oid, email = email, username = "experienceoz_" + str(operator['id']),
                    first_name = operator['name'][:30] if operator['name'] else "",
                    last_name = partner_id,
                    date_joined = datetime.utcnow().replace(tzinfo=pytz.UTC))

        user.save()
        user.set_password(user.username)
        user.save()

        image_url = operator.get('image', None)
        bio = operator.get('summary', operator.get('description', None))
        user_signed_up.send(sender=user.__class__, request=request, user=user,
                            partner_operator = True,
                            image_url = image_url,
                            bio = bio)

    if hasattr(user, "provider") and user.provider is not None:
        provider = user.provider
    else:
        provider = Provider()
        provider.user = user

        provider.partner = partner_id
        provider.company = operator.get('name', "")
        provider.website = operator.get('urlSegment', "")
        provider.email = user.email

    provider.location = operator.get('geolocation', None)
    if 'address' in operator and operator['address'] is not None:
        if provider.location is None:
            provider.location = {}
        provider.location['address'] = operator.get('address')
    provider.save()

    if provider.location and 'longitude' in provider.location\
        and 'latitude' in provider.location and provider.product_suppliers:
        for product in provider.product_suppliers.all():
            if len(product.coordinate_set.all()) == 0:
                coordinates = provider.location
                longitude = coordinates['longitude']
                latitude = coordinates['latitude']
                c = Coordinate(experience=product, order=1, longitude=longitude, latitude=latitude)
                c.save()

    return provider

def get_operator(operatorUrl, partner_id, request):
    base_url = "https://tripalocal.experienceoz.com.au/api/"

    url = base_url + operatorUrl
    response = requests.get(url,
                            auth=requests.auth.HTTPBasicAuth(
                            username,
                            password))
    if response.status_code == 200:
        operator = json.loads(response.text)
        if "id" in operator:
            operator = create_operator(operator, partner_id, request)
            return operator
        else:
            return None
    else:
        return None
