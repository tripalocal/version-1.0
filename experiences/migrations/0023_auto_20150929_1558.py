# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0022_auto_20150924_1341'),
    ]

    operations = [
        migrations.AddField(
            model_name='newproduct',
            name='tags',
            field=models.ManyToManyField(related_name='newproduct_tags', to='experiences.ExperienceTag'),
            preserve_default=True,
        ),
    ]
