import json, os, collections, requests, pytz, base64, sys, string, http.client
from allauth.account.signals import user_signed_up
from datetime import *
from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponseRedirect
from experiences.models import NewProduct, NewProductI18n, Provider, OptionGroup, OptionItem
from experiences.views import saveExperienceImage
from io import BytesIO
from Tripalocal_V1 import settings

PARTNER_IDS = {"experienceoz":"001"}

SOAP_REQUEST_AVAILABILITY = \
'''<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Header>
        <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" 
        xmlns:wsu="http://docs.oasisopen.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
        soap:mustUnderstand="1">
            <wsse:UsernameToken wsu:Id="UsernameToken-3">
                <wsse:Username>tripalocalapi</wsse:Username>
                <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">JpwBSYJqzpU7UG7K</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soap:Header>
    <soap:Body>
        <ns2:getAvailability xmlns:ns2="http://experienceoz.com.au/">
            <AvailabilityRequest>
                <ProductId>{product_id}</ProductId>
                <StartDate>{start_date}</StartDate>
            </AvailabilityRequest>
        </ns2:getAvailability>
    </soap:Body>
</soap:Envelope>
'''

def convert_location(city):
    locations = {'cairns':'Cairns','port-douglas':'Cairns','sydney':'Sydney','melbourne':'Melbourne',
                'brisbane':'Brisbane','hobart':'Hobart','launceston':'GRTAS','adelaide':'Adelaide',
                'gold-coast':'Goldcoast','sunshine-coast':'GRQLD','byron-bay':'GRNSW','perth':'Perth',
                'darwin':'Darwin','auckland':'Auckland','west-coast':'Westcoast','doubtful-sound':'Doubtfulsound',
                'rotorua':'Rotorua','bay-of-islands':'Bayofislands','christchurch':'Christchurch','canberra':'Canberra',
                'wellington':'Wellington','port-arthur':'GRTAS','broome':'GRWA','qld-other':'GRQLD',
                'nsw-other':'GRNSW','townsville':'GRQLD','whitsundays':'GRQLD','alice-springs':'Alicesprings',
                'queenstown':'Queenstown','hanmer-springs':'Canterbury','mt-cook':'Canterbury','marlborough':'Marlborough',
                'hervey-bay':'GRQLD','milford-sound':'Milfordsound','snowy-mountains':'GRNSW','taupo':'Taupo',
                'ningaloo-reef':'GRWA','margaret-river':'GRWA','the-coromandel':'Coromandel','ayers-rock':'GRNA',
                'te-anau':'Teanau','stewart-island':'Stewartisland','cradle-coast':'GRTAS','hawkes-bay':'Hawkesbay',
                'port-stephens':'GRNSW','wa-other':'GRWA','kaikoura':'Canterbury'}
    return locations.get(city, city)

def import_experienceoz_products(request):
    if not request.user.is_authenticated() or not request.user.is_staff:
        return HttpResponseRedirect("/")

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

    target_language = request.GET.get('language','en')
    file_name = os.path.join(settings.PROJECT_ROOT, 'import_from_partners', 'experienceoz_' + target_language + '.json')
    missing_operators = []
    with open(file_name, "rb") as file:
        products = json.loads(file.read().decode("utf-8"))
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
                operator = get_operator(product['operatorUrl'], partner_id, request)
            if operator:
                np = NewProduct.objects.filter(abstractexperience_ptr_id = pid)
                if len(np) > 0:
                    np = np[0]
                    now = pytz.timezone(np.get_timezone()).localize(datetime.now())
                    now_string = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+now.strftime("%z")
                    now_string = now_string[:-2] + ":" + now_string[-2:]
                    #check_experienceoz_availability(product['id'], now_string)
                    #continue
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

                npi18n = np.newproducti18n_set.all()
                if len(npi18n) > 0 and npi18n[0].language == target_language:
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
                    try:
                        og = OptionGroup.objects.get(original_id=group.get("id"))
                        og.name = group.get("groupName")
                    except OptionGroup.DoesNotExist:
                        og = OptionGroup(product = np, name = group.get("groupName"), language = target_language, original_id = group.get("id"))
                    og.save()
                    for option in group.get("productOptions"):
                        try:
                            oi = OptionItem.objects.get(original_id=option.get("id"))
                            oi.name = option.get("name")
                        except OptionItem.DoesNotExist:
                            oi = OptionItem(group = og, name = option.get("name"), price = 0, retail_price = 0, original_id = option.get("id"))
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

    return HttpResponseRedirect("/")

def import_experienceoz_operators(request):
    if not request.user.is_authenticated() or not request.user.is_staff:
        return HttpResponseRedirect("/")

    partner_id = PARTNER_IDS['experienceoz']
    folder = os.path.join(settings.PROJECT_ROOT, 'import_from_partners', 'experienceoz_operators')
    for filename in os.listdir(folder):
        if os.path.isfile(os.path.join(folder, filename)):
            with open(os.path.join(folder, filename), "rb") as file:
                operators = json.loads(file.read().decode('utf-8'))['operators']
                for operator in operators:
                    create_operator(operator, partner_id, request)

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
    if hasattr(user, "provider"):
        provider = user.provider
    else:
        provider = Provider()
        provider.user = user
    provider.partner = partner_id
    provider.company = operator['name'] if operator['name'] else ""
    provider.website = operator['urlSegment'] if operator['urlSegment'] else ""
    provider.email = user.email
    provider.save()
    return provider

def get_operator(operatorUrl, partner_id, request):
    username = '7254'
    password = 'dHJpcGFsb2NhbFRyaXBhbG9jYWwgUHR5IEx0ZA=='
    auth = username + ':' + password
    auth = base64.b64encode(auth.encode('ascii'))
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

def check_experienceoz_availability(product_id, start_date):
    server_addr = "www.tmtest.com.au"
    service_action = "https://www.tmtest.com.au/d/services/API"

    form_kwargs = {
        'product_id': product_id,
        'start_date': start_date,
    }
    body = SOAP_REQUEST_AVAILABILITY.format(**form_kwargs)

    #body = body.encode('utf-8')

    headers = {"Accept": "application/soap+xml, multipart/related, text/*", 
               "Content-Type": "text/xml; charset=UTF-8",
               "Content-Length": str(len(body)),
              }

    response = requests.post(url=service_action,
                             headers = headers,
                             data = body)

    response = response
    #request = http.client.HTTPConnection(server_addr)
    #request.putrequest("GET", service_action)
    #request.putheader("Accept", "application/soap+xml, application/dime, multipart/related, text/*")
    #request.putheader("Content-Type", "text/xml; charset=utf-8")
    #request.putheader("Cache-Control", "no-cache")
    #request.putheader("Pragma", "no-cache")
    #request.putheader("SOAPAction", service_action)
    #request.putheader("Content-Length", str(len(body)))
    #request.endheaders()
    #request.send(body)
    #response = request.getresponse().read()