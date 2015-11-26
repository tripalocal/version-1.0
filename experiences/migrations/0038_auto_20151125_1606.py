# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0037_auto_20151123_1206'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomItineraryRequest',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('is_first_time', models.BooleanField(default=True)),
                ('destinations', models.TextField()),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('adults_number', models.IntegerField(default=1)),
                ('children_number', models.IntegerField(default=0)),
                ('tags', models.TextField()),
                ('whatsincluded', models.TextField()),
                ('budget', models.TextField()),
                ('requirements', models.TextField(blank=True, null=True)),
                ('customer_name', models.CharField(max_length=40)),
                ('email', models.EmailField(max_length=254)),
                ('wechat', models.CharField(max_length=50)),
                ('mobile', models.CharField(max_length=50)),
            ],
        ),
    ]
