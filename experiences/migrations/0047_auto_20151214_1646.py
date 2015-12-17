# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0046_auto_20151211_1211'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='total_price',
            field=models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True),
            preserve_default=True,
        ),
    ]
