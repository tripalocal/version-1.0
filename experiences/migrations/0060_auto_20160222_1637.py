# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0059_auto_20160222_1624'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newproduct',
            name='status',
            field=models.CharField(default='Unlisted', max_length=20, choices=[('Listed', 'Listed'), ('Unlisted', 'Unlisted'), ('Unavailable', 'Unavailable')]),
            preserve_default=True,
        ),
    ]
