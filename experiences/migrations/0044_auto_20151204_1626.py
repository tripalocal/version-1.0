# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0043_auto_20151204_1532'),
    ]

    operations = [
        migrations.AlterField(
            model_name='provider',
            name='website',
            field=models.CharField(max_length=254, blank=True),
            preserve_default=True,
        ),
    ]
