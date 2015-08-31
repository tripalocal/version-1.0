# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0002_experience_commission'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experience',
            name='duration',
            field=models.FloatField(),
            preserve_default=True,
        ),
    ]
