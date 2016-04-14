# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0065_auto_20160329_1810'),
    ]

    operations = [
        migrations.AddField(
            model_name='customitinerary',
            name='guests',
            field=models.IntegerField(blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customitinerary',
            name='profit',
            field=models.IntegerField(blank=True, null=True),
            preserve_default=True,
        ),
    ]
