# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0061_auto_20160224_1114'),
    ]

    operations = [
        migrations.AddField(
            model_name='newproduct',
            name='original_id',
            field=models.TextField(blank=True, null=True),
            preserve_default=True,
        ),
    ]
