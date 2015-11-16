# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0034_auto_20151114_1559'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='phone_number',
            field=models.CharField(max_length=50),
        ),
    ]
