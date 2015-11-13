# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0032_auto_20151112_1514'),
    ]

    operations = [
        migrations.AddField(
            model_name='customitinerary',
            name='payment',
            field=models.ForeignKey(blank=True, to='experiences.Payment', null=True),
        ),
    ]
