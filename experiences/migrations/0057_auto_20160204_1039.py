# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0056_auto_20160119_1121'),
    ]

    operations = [
        migrations.AddField(
            model_name='provider',
            name='location',
            field=models.CharField(max_length=500, null=True, blank=True),
            preserve_default=True,
        ),
    ]
