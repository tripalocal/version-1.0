# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0005_auto_20150914_2302'),
    ]

    operations = [
        migrations.AddField(
            model_name='wechatbooking',
            name='paid',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
