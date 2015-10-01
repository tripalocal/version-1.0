# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0007_auto_20150917_1524'),
    ]

    operations = [
        migrations.AlterField(
            model_name='provider',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
