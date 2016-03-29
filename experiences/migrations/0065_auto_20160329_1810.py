# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0064_auto_20160329_1634'),
    ]

    operations = [
        migrations.AddField(
            model_name='optiongroup',
            name='type',
            field=models.CharField(max_length=30, blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='optionitem',
            name='description',
            field=models.TextField(blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='optionitem',
            name='image',
            field=models.TextField(blank=True, null=True),
            preserve_default=True,
        ),
    ]
