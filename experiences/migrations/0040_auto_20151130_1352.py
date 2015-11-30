# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0039_auto_20151130_1121'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='coupon_extra_information',
            field=models.TextField(blank=True, null=True),
        ),
    ]
