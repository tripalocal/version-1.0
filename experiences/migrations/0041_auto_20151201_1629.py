# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0040_auto_20151130_1352'),
    ]

    operations = [
        migrations.AddField(
            model_name='newproduct',
            name='partner',
            field=models.CharField(null=True, blank=True, max_length=100),
            preserve_default=True,
        ),
    ]
