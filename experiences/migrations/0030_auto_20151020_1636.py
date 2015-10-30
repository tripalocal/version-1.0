# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0029_auto_20151016_1225'),
    ]

    operations = [
        migrations.AddField(
            model_name='newproduct',
            name='type',
            field=models.CharField(default='PUBLIC', max_length=50),
            preserve_default=True,
        ),
    ]
