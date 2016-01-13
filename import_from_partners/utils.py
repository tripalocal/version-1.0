import json, os, collections, requests, pytz, base64, sys, string, http.client
from datetime import *
from experiences.models import OptionGroup, OptionItem
from xml.etree import ElementTree

SOAP_REQUEST_AVAILABILITY = \
''' <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Header>
            <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
		    xmlns:wsu="http://docs.oasisopen.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
            soap:mustUnderstand="1">
                <wsse:UsernameToken wsu:Id="UsernameToken-3">
                    <wsse:Username>tripalocal</wsse:Username>
                    <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">okmnji</wsse:Password>
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
    server_addr = "www.tmtest.com.au"
    service_action = "https://www.tmtest.com.au/d/services/API"

    form_kwargs = {
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

    if response.status_code == 200:
        tree = ElementTree.fromstring(response.text)
        for e in tree.findall('.//Availability'):
            date_string = e[0].text
            d = datetime.strptime(date_string[:-3]+date_string[-2:], "%Y-%m-%d%z")
            status = e[1].text
            if status == 'Available':
                dict = {'available_seat': experience.guest_number_max,
                            'date_string': d.strftime("%d/%m/%Y"),
                            'time_string': "00:00",
                            'datetime': d,
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
                            existing_oi = OptionItem.objects.get(original_id=oi.get("id"))
                            if existing_oi.price != price:
                                existing_oi.price = price
                                existing_oi.save()
                        except OptionItem.DoesNotExist:
                            pass
    return available_date