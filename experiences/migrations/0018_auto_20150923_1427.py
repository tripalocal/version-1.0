# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0017_auto_20150922_1351'),
    ]

    operations = [
        migrations.AddField(
            model_name='newproduct',
            name='city',
            field=models.CharField(max_length=50, default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='newproduct',
            name='language',
            field=models.CharField(max_length=50, default='english'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='newproduct',
            name='max_group_size',
            field=models.IntegerField(blank=True, null=True),
            preserve_default=True,
        ),
    ]
