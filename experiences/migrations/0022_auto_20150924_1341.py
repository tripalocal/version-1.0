# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0021_auto_20150924_1231'),
    ]

    operations = [
        migrations.AddField(
            model_name='newproduct',
            name='commission',
            field=models.FloatField(default=0.3),
            preserve_default=True,
        ),
    ]
