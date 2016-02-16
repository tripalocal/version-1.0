# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0054_auto_20160111_1617'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='total_price',
            field=models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True),
            preserve_default=True,
        ),
    ]
