# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0023_auto_20150929_1558'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newproduct',
            name='language',
            field=models.CharField(max_length=50, default='english;'),
            preserve_default=True,
        ),
    ]
