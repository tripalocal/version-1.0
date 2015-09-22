# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0016_auto_20150922_0917'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewProduct',
            fields=[
                ('abstractexperience_ptr', models.OneToOneField(serialize=False, parent_link=True, auto_created=True, to='experiences.AbstractExperience', primary_key=True)),
                ('price_type', models.CharField(default='NORMAL', max_length=6, choices=[('NORMAL', 'Normal price per person'), ('AGE', 'Price for different age group'), ('DYNAMIC', 'Dynamic price')], help_text='Only one of the price type will take effact.')),
                ('normal_price', models.DecimalField(blank=True, max_digits=6, decimal_places=2, null=True)),
                ('dynamic_price', models.CharField(blank=True, max_length=100)),
                ('adult_price', models.DecimalField(blank=True, max_digits=6, decimal_places=2, null=True)),
                ('children_price', models.DecimalField(blank=True, max_digits=6, decimal_places=2, null=True)),
                ('adult_age', models.IntegerField(blank=True, help_text='Above what age should pay adult price.', null=True)),
                ('duration_in_min', models.IntegerField(blank=True, help_text='How long will it be in minutes?', null=True)),
                ('min_group_size', models.IntegerField(blank=True, null=True)),
                ('book_in_advance', models.IntegerField(blank=True, null=True)),
                ('instant_booking', models.TextField(blank=True)),
                ('free_translation', models.BooleanField(default=False)),
                ('order_on_holiday', models.BooleanField(default=False, help_text='If supplier take order during weekend and holiday particularly instant order during holiday')),
                ('provider', models.ForeignKey(to='experiences.Provider')),
            ],
            options={
                'abstract': False,
            },
            bases=('experiences.abstractexperience',),
        ),
        migrations.CreateModel(
            name='NewProductI18n',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('language', models.CharField(default='en', max_length=3, choices=[('en', 'English'), ('zh', '中文')])),
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
                ('whats_included', models.TextField(blank=True, help_text="What's included in the price (pickup/meal/drink/certificate/photo)")),
                ('pickup_detail', models.TextField(blank=True)),
                ('combination_options', models.TextField(blank=True, help_text='Combination option (for example the client can tick to choose whether to add translator or driver into the tour, and we can set standard price for different durations of such service provided)')),
                ('insurance', models.TextField(blank=True)),
                ('disclaimer', models.TextField(blank=True)),
                ('product', models.ForeignKey(to='experiences.NewProduct')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
