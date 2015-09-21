# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0015_auto_20150922_0023'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='experience',
            field=models.ForeignKey(to='experiences.AbstractExperience'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='photo',
            name='experience',
            field=models.ForeignKey(to='experiences.AbstractExperience'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='review',
            name='experience',
            field=models.ForeignKey(to='experiences.AbstractExperience'),
            preserve_default=True,
        ),
    ]
