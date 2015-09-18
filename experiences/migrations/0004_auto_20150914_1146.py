# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0003_auto_20150831_1147'),
    ]

    operations = [
        migrations.CreateModel(
            name='WechatBooking',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('datetime', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('trade_no', models.CharField(max_length=64)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WechatProduct',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('price', models.DecimalField(max_digits=6, decimal_places=2)),
                ('valid', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='wechatbooking',
            name='product',
            field=models.ForeignKey(to='experiences.WechatProduct'),
            preserve_default=True,
        ),
    ]
