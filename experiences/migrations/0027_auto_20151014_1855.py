# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0026_auto_20151014_1811'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coordinate',
            name='name',
            field=models.CharField(max_length=100, blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='coordinate',
            name='order',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='coordinate',
            name='type',
            field=models.CharField(max_length=100, blank=True, null=True),
            preserve_default=True,
        ),
    ]
