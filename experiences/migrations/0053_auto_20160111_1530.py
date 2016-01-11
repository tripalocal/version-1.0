# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0052_auto_20160108_1518'),
    ]

    operations = [
        migrations.AddField(
            model_name='optiongroup',
            name='language',
            field=models.CharField(max_length=3, default='en', choices=[('en', 'English'), ('zh', '中文')]),
            preserve_default=True,
        ),
    ]
