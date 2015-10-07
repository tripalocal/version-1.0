# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import app.models


class Migration(migrations.Migration):

    dependencies = [
	    ('experiences', '0024_auto_20150930_1741'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPageViewStatistics',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('times_viewed', models.IntegerField(default=0)),
                ('average_length', models.FloatField(default=0.0)),
                ('experience', models.ForeignKey(to='experiences.Experience')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
