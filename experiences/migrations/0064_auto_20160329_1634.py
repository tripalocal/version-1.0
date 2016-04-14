# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0063_auto_20160328_1727'),
    ]

    operations = [
        migrations.AddField(
            model_name='optionitem',
            name='max_quantity',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='optionitem',
            name='min_quantity',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='optionitem',
            name='price_type',
            field=models.CharField(null=True, blank=True, max_length=30),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='optionitem',
            name='seats_used',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
