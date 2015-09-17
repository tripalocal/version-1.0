from django.core.management.base import BaseCommand
from experiences.models import Product, ProductI18n, Provider
from openpyxl import load_workbook


def create_product(i, d, lang):
    for key, value in d.items():
        if not value:
            d[key] = ''

    provider, created = Provider.objects.get_or_create(company=d['company'])

    product = Product(provider=provider, instant_booking=d['instant_booking'])
    product.save()
    product_i18n = ProductI18n(product=product, language=lang, location=d['location'],
                               background_info=d['background_info'], description=d['description'], service=d['service'],
                               highlights=d['highlights'], schedule=d['schedule'],
                               ticket_use_instruction=d['ticket_use_instruction'], refund_policy=d['refund_policy'],
                               notice=d['notice'], tips=d['tips'], whats_included=d['whats_included'],
                               pickup_detail=d['pickup_detail'], combination_options=d['combination_options'],
                               insurance=d['insurance'], disclaimer=d['disclaimer'])
    try:
        product_i18n.save()
    except:
        print(i)


class Command(BaseCommand):
    args = '<filename.xlsx>'
    help = 'Parse travel products from spreadsheet.'

    def handle(self, *args, **options):
        input_filename = args[0]
        wb = load_workbook(input_filename)
        for sheet in wb:
            for i, row in enumerate(sheet.rows):
                if i != 0 and row[1].value:
                    data = {'company': row[1].value, 'location': row[2].value, 'background_info': row[4].value,
                            'description': row[5].value, 'service': row[6].value, 'highlights': row[7].value,
                            'schedule': row[8].value,
                            'instant_booking': row[13].value, 'ticket_use_instruction': row[14].value,
                            'refund_policy': row[15].value, 'notice': row[16].value, 'tips': row[17].value,
                            'whats_included': row[18].value,
                            'combination_options': row[21].value, 'pickup_detail': row[22].value,
                            'insurance': row[23].value,
                            'disclaimer': row[24].value}
                    create_product(i, data, 'en')
