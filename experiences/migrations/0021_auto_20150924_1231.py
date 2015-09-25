# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0020_auto_20150923_1809'),
    ]

    operations = [
        migrations.RenameField(
            model_name='newproducti18n',
            old_name='whats_included',
            new_name='whatsincluded',
        ),
        migrations.RenameField(
            model_name='newproduct',
            old_name='normal_price',
            new_name='price',
        ),
    ]
