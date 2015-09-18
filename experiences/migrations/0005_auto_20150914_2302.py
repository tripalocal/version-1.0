# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0004_auto_20150914_1146'),
    ]

    operations = [
        migrations.AddField(
            model_name='wechatbooking',
            name='email',
            field=models.CharField(max_length=25, default=''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='wechatbooking',
            name='phone_num',
            field=models.CharField(max_length=15, default=''),
            preserve_default=True,
        ),
    ]
