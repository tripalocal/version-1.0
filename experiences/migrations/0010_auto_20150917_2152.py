# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0009_auto_20150917_1642'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='adult_age',
            field=models.IntegerField(null=True, help_text='Above what age should pay adult price.', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='product',
            name='duration_in_min',
            field=models.IntegerField(null=True, help_text='How long will it be in minutes?', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='product',
            name='order_on_holiday',
            field=models.BooleanField(default=False, help_text='If supplier take order during weekend and holiday particularly instant order during holiday'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='product',
            name='price_type',
            field=models.CharField(max_length=6, choices=[('NORMAL', 'Normal price per person'), ('AGE', 'Price for different age group'), ('DYNAMIC', 'Dynamic price')], default='NORMAL', help_text='Only one of the price type will take effact.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='producti18n',
            name='combination_options',
            field=models.TextField(help_text='Combination option (for example the client can tick to choose whether to add translator or driver into the tour, and we can set standard price for different durations of such service provided)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='producti18n',
            name='whats_included',
            field=models.TextField(help_text="What's included in the price (pickup/meal/drink/certificate/photo)", blank=True),
            preserve_default=True,
        ),
    ]
