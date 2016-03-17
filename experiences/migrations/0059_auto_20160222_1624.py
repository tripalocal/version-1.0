# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0058_auto_20160208_1611'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='note',
            field=models.TextField(blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='newproduct',
            name='status',
            field=models.CharField(max_length=20, default='Unlisted', choices=[('Listed', 'Listed'), ('Unlisted', 'Unlisted'), ('API incorrect', 'API incorrect')]),
            preserve_default=True,
        ),
    ]
