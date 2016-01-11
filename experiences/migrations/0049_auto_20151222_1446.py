# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0048_auto_20151214_1646'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='whats_included',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
