# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0060_auto_20160222_1637'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newproduct',
            name='status',
            field=models.CharField(max_length=20, default='Unlisted', choices=[('Listed', 'Listed'), ('Unlisted', 'Unlisted'), ('Unavailable', 'Unavailable'), ('Incorrect', 'Incorrect')]),
            preserve_default=True,
        ),
    ]
