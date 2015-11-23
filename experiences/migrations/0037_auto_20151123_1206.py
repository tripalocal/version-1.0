# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0036_auto_20151119_1815'),
    ]

    operations = [
        migrations.AddField(
            model_name='experience',
            name='fixed_price',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='newproduct',
            name='fixed_price',
            field=models.FloatField(default=0.0),
        ),
    ]
