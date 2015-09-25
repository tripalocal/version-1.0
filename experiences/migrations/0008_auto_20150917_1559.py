# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0007_auto_20150917_1524'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='duration',
            new_name='duration_in_min',
        ),
        migrations.AddField(
            model_name='product',
            name='adult_age',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
