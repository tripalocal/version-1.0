# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0053_auto_20160111_1530'),
    ]

    operations = [
        migrations.AddField(
            model_name='optiongroup',
            name='original_id',
            field=models.IntegerField(blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='optionitem',
            name='original_id',
            field=models.IntegerField(blank=True, null=True),
            preserve_default=True,
        ),
    ]
