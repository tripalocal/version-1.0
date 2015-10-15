# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0024_auto_20150930_1741'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coordinate',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('longitude', models.FloatField()),
                ('latitude', models.FloatField()),
                ('type', models.TextField()),
                ('order', models.IntegerField()),
                ('experience', models.ForeignKey(to='experiences.AbstractExperience')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
