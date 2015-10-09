# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import app.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0002_auto_20151007_2035'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPageViewRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('time_arrived', models.DateTimeField()),
                ('time_left', models.DateTimeField(blank=True, null=True)),
                ('experience', models.ForeignKey(to='experiences.AbstractExperience')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
