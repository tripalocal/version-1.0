# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0031_auto_20151020_1725'),
    ]

    operations = [
        migrations.AddField(
            model_name='customitinerary',
            name='submitted_datetime',
            field=models.DateTimeField(null=True),
        ),
    ]
