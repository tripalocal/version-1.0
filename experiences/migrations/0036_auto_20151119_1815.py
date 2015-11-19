# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0035_auto_20151115_1414'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experience',
            name='tags',
            field=models.ManyToManyField(to='experiences.ExperienceTag', related_name='experience_tags', blank=True),
        ),
        migrations.AlterField(
            model_name='newproduct',
            name='tags',
            field=models.ManyToManyField(to='experiences.ExperienceTag', related_name='newproduct_tags', blank=True),
        ),
    ]
