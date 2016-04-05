import json, os, collections, requests, pytz, base64, sys, string, http.client
from datetime import *
from experiences.models import OptionGroup, OptionItem, NewProduct
from xml.etree import ElementTree

PARTNER_IDS = {"experienceoz":"001", "rezdy":"002"}
USERNAME = "tripalocalapi"
PASSWORD = "c8EAZbRULywU4PnW"
service_action = "https://tripalocal.experienceoz.com.au/d/services/API"#"https://www.tmtest.com.au/d/services/API"#

rezdy_api = "https://api.rezdy.com/latest/"
rezdy_api_key = "97acaed307f441a5a1599a6ecdebffa3"

SOAP_REQUEST_AVAILABILITY = \
''' <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Header>
            <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
		    xmlns:wsu="http://docs.oasisopen.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
            soap:mustUnderstand="1">
                <wsse:UsernameToken wsu:Id="UsernameToken-3">
                    <wsse:Username>{username}</wsse:Username>
                    <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{password}</wsse:Password>
                </wsse:UsernameToken>
            </wsse:Security>
        </soap:Header>
        <soap:Body>
          <ns2:GetAvailability xmlns:ns2="https://experienceoz.com.au/">
             <AvailabilityRequest>
                <ProductId>{product_id}</ProductId>
                <StartDate>{start_date}</StartDate>
             </AvailabilityRequest>
          </ns2:GetAvailability>
        </soap:Body>
    </soap:Envelope>
'''

SOAP_REQUEST_MAKEPURCHASE = \
'''
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
	<soap:Header>
		<wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
        xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
        soap:mustUnderstand="1">
			<wsse:UsernameToken wsu:Id="UsernameToken-1">
				<wsse:Username>{username}</wsse:Username>
				<wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{password}</wsse:Password>
			</wsse:UsernameToken>
	</wsse:Security>
	</soap:Header>
	<soap:Body>
		<ns3:MakePurchase xmlns:ns3="https://experienceoz.com.au/">
			<PurchaseRequest>
				<Customer>
					<FirstName>{first_name}</FirstName>
					<LastName>{last_name}</LastName>
					<ContactNumber>{number}</ContactNumber>
					<Email>{email}</Email>
					<Country>{country}</Country>
					<Postcode>{postcode}</Postcode>
				</Customer>
				<Items>
					<Item>
						<ProductId>{product_id}</ProductId>
						<BookingDate>{booking_date}</BookingDate>
                        <BookingNotes>{booking_notes}</BookingNotes>
                        <ItemOptions>{item_options}</ItemOptions>
					</Item>
				</Items>
			</PurchaseRequest>
		</ns3:MakePurchase>
	</soap:Body>
</soap:Envelope>
'''

SOAP_REQUEST_RECEIPT = \
'''
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
	<soap:Header>
		<wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
		xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
		soap:mustUnderstand="1">
			<wsse:UsernameToken wsu:Id="UsernameToken-2">
				<wsse:Username>{username}</wsse:Username>
				<wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{password}</wsse:Password>
			</wsse:UsernameToken>
		</wsse:Security>
	</soap:Header>
	<soap:Body>
		<ns3:Receipt xmlns:ns3="https://experienceoz.com.au/">
			<ReceiptPurchaseRequest id="{purchase_id}">
				<ReferenceNumber>{reference_number}</ReferenceNumber>
			</ReceiptPurchaseRequest>
		</ns3:Receipt>
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

def get_experienceoz_availability(product_id, start_date, experience, available_options, available_date):

    form_kwargs = {
        'username': USERNAME,
        'password': PASSWORD,
        'product_id': product_id,
        'start_date': start_date,
    }
    body = SOAP_REQUEST_AVAILABILITY.format(**form_kwargs)

    headers = {"Accept": "application/soap+xml, multipart/related, text/*", 
               "Content-Type": "text/xml; charset=UTF-8",
               "Content-Length": str(len(body)),
              }

    response = requests.post(url=service_action,
                             headers = headers,
                             data = body)

    if response.status_code == 200 and response.ok:
        tree = ElementTree.fromstring(response.text)
        for e in tree.findall('.//Availability'):
            date_string = e[0].text
            d = datetime.strptime(date_string[:-3]+date_string[-2:], "%Y-%m-%d%z")
            status = e[1].text
            if status == 'Available':
                dict = {'available_seat': experience.guest_number_max,
                            'date_string': d.strftime("%d/%m/%Y"),
                            'time_string': "00:00",
                            #'datetime': d,
                            'instant_booking': False}
                available_options.append(dict)
                new_date = ((d.strftime("%d/%m/%Y"), d.strftime("%d/%m/%Y")),)
                available_date += new_date

                option_groups = e[2].findall('.//ProductOptionGroup')
                for op in option_groups:
                    op_id = op.get("id")
                    op_name = op[0].text
                    option_items = op.findall(".//ProductOption")
                    for oi in option_items:
                        oi_id = oi.get("id")
                        oi_name = oi[0].text
                        price = float(oi[1].text)
                        try:
                            existing_ois = OptionItem.objects.filter(original_id=oi.get("id"))
                            for existing_oi in existing_ois:
                                if existing_oi.price != price:
                                    existing_oi.price = price
                                    existing_oi.save()
                        except OptionItem.DoesNotExist:
                            pass
    return available_date

def experienceoz_makepurchase(first_name, last_name, number, email, country, postcode, product, booking_date, booking_extra_information, note=None):
    #convert booking_extra_information into 
    #<ItemOption>
	#	<ProductOptionId></ProductOptionId>
	#	<Quantity></Quantity>
	#</ItemOption>
    #<ItemOption>
	#	<ProductOptionId></ProductOptionId>
	#	<Quantity></Quantity>
	#</ItemOption>
    options = json.loads(booking_extra_information)
    item_options = ""
    for k, v in options.items():
        item_options += "<ItemOption><ProductOptionId>"+str(k)+"</ProductOptionId><Quantity>"+str(v)+"</Quantity></ItemOption>"

    number = number.strip() #not working???
    form_kwargs = {
        'username': USERNAME,
        'password': PASSWORD,
        'first_name':first_name,
        'last_name':last_name,
        'email':email,
        'number':number,
        'country':country.upper(),
        'postcode':postcode,
        'product_id': str(product.id)[:-(len(str(product.partner))+1)],
        'booking_date': booking_date,
        'booking_notes': note if note else "",
        'item_options':item_options
    }
    body = SOAP_REQUEST_MAKEPURCHASE.format(**form_kwargs)

    headers = {"Accept": "application/soap+xml, multipart/related, text/*", 
               "Content-Type": "text/xml; charset=UTF-8",
               "Content-Length": str(len(body)),
              }

    response = requests.post(url=service_action,
                             headers = headers,
                             data = body)

    if response.status_code == 200 and response.ok:
        tree = ElementTree.fromstring(response.text)
        purchase = tree.find('.//Purchase')
        price = float(purchase[1].text)
        vouchers = []
        profits = 0.0
        for v in purchase.findall('.//Voucher'):
            vouchers.append(v.attrib['id'])
            profits += float(v[3].text)
        #update commission
        try:
            p = NewProduct.objects.get(id=v[0].attrib['id'])
            new_c = round(float(v[3].text)/(float(v[1].text)-float(v[3].text)),3)
            if p.commission == 0:
                p.commission = new_c
            elif new_c < p.commission:
                p.commission = new_c
                p.save()
        except Exception:
            pass

        return {"success":True, "purchase_id":purchase.attrib['id'], "price":price, "vouchers":vouchers, "profits":profits}
    else:
        return {"success":False}

def experienceoz_receipt(booking):
    form_kwargs = {
        'username': USERNAME,
        'password': PASSWORD,
        'purchase_id':booking.whats_included,
        'reference_number':booking.id,
    }

    body = SOAP_REQUEST_RECEIPT.format(**form_kwargs)

    headers = {"Accept": "application/soap+xml, multipart/related, text/*", 
               "Content-Type": "text/xml; charset=UTF-8",
               "Content-Length": str(len(body)),
              }

    response = requests.post(url=service_action,
                             headers = headers,
                             data = body)

    if response.status_code == 200 and response.ok:
        tree = ElementTree.fromstring(response.text)
        link = tree.find('.//TicketPDFLink')
        return {"success":True, "link":link.text}
    else:
        return {"success":False}

def get_rezdy_availability(available_options, available_date, product_code, start_time_local, end_time_local, limit=100, offset=0):
    url_template = rezdy_api + \
                   "availability?productCode={product_code}&startTimeLocal={start_time_local}" + \
                   "&endTimeLocal={end_time_local}&limit={limit}&offset={offset}&apiKey=" + \
                   rezdy_api_key
    kwargs = {
        'product_code': product_code,
        'start_time_local': start_time_local,
        'end_time_local': end_time_local,
        'limit': limit,
        'offset': offset,
    }
    url = url_template.format(**kwargs)
    response = requests.get(url)
    if response.status_code == 200 and response.reason == "OK":
        sessions = json.loads(response.text)
        for session in sessions['sessions']:
            start = datetime.strptime(session['startTimeLocal'], "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(session['endTimeLocal'], "%Y-%m-%d %H:%M:%S")
            for i in range((end-start).days):
                d = start + timedelta(days=i)
                dict = {'available_seat': session['seatsAvailable'],
                        'date_string': d.strftime("%d/%m/%Y"),
                        'time_string': "00:00",
                        #'datetime': d,
                        'instant_booking': False}
                available_options.append(dict)
                new_date = ((d.strftime("%d/%m/%Y"), d.strftime("%d/%m/%Y")),)
                available_date += new_date
    return available_date