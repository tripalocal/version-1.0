# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('experiences', '0006_wechatbooking_paid'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('price_type', models.CharField(choices=[('NORMAL', 'Normal price per person'), ('AGE', 'Price for different age group'), ('DYNAMIC', 'Dynamic price')], default='NORMAL', max_length=6)),
                ('normal_price', models.DecimalField(null=True, max_digits=6, decimal_places=2, blank=True)),
                ('dynamic_price', models.CharField(blank=True, max_length=100)),
                ('adult_price', models.DecimalField(null=True, max_digits=6, decimal_places=2, blank=True)),
                ('children_price', models.DecimalField(null=True, max_digits=6, decimal_places=2, blank=True)),
                ('duration', models.IntegerField(null=True, blank=True)),
                ('min_group_size', models.IntegerField(null=True, blank=True)),
                ('book_in_advance', models.IntegerField(null=True, blank=True)),
                ('instant_booking', models.TextField(blank=True)),
                ('free_translation', models.BooleanField(default=False)),
                ('order_on_holiday', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductI18n',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('language', models.CharField(choices=[('en', 'English'), ('zh', '中文')], default='en', max_length=3)),
                ('title', models.CharField(max_length=100)),
                ('location', models.TextField(blank=True)),
                ('background_info', models.TextField(blank=True)),
                ('description', models.TextField(blank=True)),
                ('service', models.TextField(blank=True)),
                ('highlights', models.TextField(blank=True)),
                ('schedule', models.TextField(blank=True)),
                ('ticket_use_instruction', models.TextField(blank=True)),
                ('refund_policy', models.TextField(blank=True)),
                ('notice', models.TextField(blank=True)),
                ('tips', models.TextField(blank=True)),
                ('whats_included', models.TextField(blank=True)),
                ('pickup_detail', models.TextField(blank=True)),
                ('combination_options', models.TextField(blank=True)),
                ('insurance', models.TextField(blank=True)),
                ('disclaimer', models.TextField(blank=True)),
                ('product', models.ForeignKey(to='experiences.Product')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Provider',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('company', models.CharField(max_length=100)),
                ('website', models.CharField(blank=True, max_length=50)),
                ('email', models.CharField(blank=True, max_length=30)),
                ('phone_number', models.CharField(blank=True, max_length=15)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='product',
            name='provider',
            field=models.ForeignKey(to='experiences.Provider'),
            preserve_default=True,
        ),
    ]
