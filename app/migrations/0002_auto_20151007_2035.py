# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import app.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userpageviewstatistics',
            name='experience',
            field=models.ForeignKey(to='experiences.AbstractExperience'),
            preserve_default=True,
        ),
    ]
