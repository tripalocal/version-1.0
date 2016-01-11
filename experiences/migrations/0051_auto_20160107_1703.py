# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0050_auto_20160106_1813'),
    ]

    operations = [
        migrations.AddField(
            model_name='customitinerary',
            name='end_datetime',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customitinerary',
            name='start_datetime',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
