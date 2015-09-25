# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0018_auto_20150923_1427'),
    ]

    operations = [
        migrations.AddField(
            model_name='newproduct',
            name='currency',
            field=models.CharField(max_length=10, default='aud'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='newproduct',
            name='status',
            field=models.CharField(choices=[('Listed', 'Listed'), ('Unlisted', 'Unlisted')], default='Unlisted', max_length=20),
            preserve_default=True,
        ),
    ]
