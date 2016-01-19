# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0055_auto_20160117_1303'),
    ]

    operations = [
        migrations.AddField(
            model_name='newproduct',
            name='note',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
