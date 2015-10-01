# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0019_auto_20150923_1447'),
    ]

    operations = [
        migrations.RenameField(
            model_name='newproduct',
            old_name='max_group_size',
            new_name='guest_number_max',
        ),
        migrations.RenameField(
            model_name='newproduct',
            old_name='min_group_size',
            new_name='guest_number_min',
        ),
        migrations.RenameField(
            model_name='newproduct',
            old_name='duration_in_min',
            new_name='duration',
        ),
        migrations.AlterField(
            model_name='newproduct',
            name='duration',
            field=models.FloatField(blank=True, help_text='How long will it be in hours?', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='newproduct',
            name='end_datetime',
            field=models.DateTimeField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='newproduct',
            name='start_datetime',
            field=models.DateTimeField(null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='blockouttimeperiod',
            name='experience',
            field=models.ForeignKey(to='experiences.AbstractExperience'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='instantbookingtimeperiod',
            name='experience',
            field=models.ForeignKey(to='experiences.AbstractExperience'),
            preserve_default=True,
        ),
    ]
