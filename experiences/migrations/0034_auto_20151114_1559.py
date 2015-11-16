# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0033_auto_20151112_1749'),
    ]

    operations = [
        migrations.AddField(
            model_name='experience',
            name='children_price',
            field=models.DecimalField(null=True, blank=True, max_digits=6, decimal_places=2),
        ),
    ]
