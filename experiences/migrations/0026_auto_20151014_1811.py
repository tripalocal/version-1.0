# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0025_auto_20151014_1729'),
    ]

    operations = [
        migrations.AddField(
            model_name='coordinate',
            name='name',
            field=models.TextField(null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='coordinate',
            name='order',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='coordinate',
            name='type',
            field=models.TextField(null=True),
            preserve_default=True,
        ),
    ]
