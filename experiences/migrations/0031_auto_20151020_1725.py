# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0030_auto_20151020_1636'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newproduct',
            name='type',
            field=models.CharField(max_length=50, default='PublicProduct'),
            preserve_default=True,
        ),
    ]
