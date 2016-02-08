# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0057_auto_20160204_1039'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='option_item',
        ),
        migrations.AddField(
            model_name='booking',
            name='partner_product',
            field=models.TextField(blank=True, null=True),
            preserve_default=True,
        ),
    ]
