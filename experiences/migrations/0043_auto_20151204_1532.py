# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0042_auto_20151204_1423'),
    ]

    operations = [
        migrations.AlterField(
            model_name='provider',
            name='email',
            field=models.CharField(max_length=100, blank=True),
            preserve_default=True,
        ),
    ]
