# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0049_auto_20151222_1446'),
    ]

    operations = [
        migrations.CreateModel(
            name='OptionGroup',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.TextField()),
                ('product', models.ForeignKey(to='experiences.NewProduct')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OptionItem',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.TextField()),
                ('retail_price', models.FloatField(null=True, blank=True)),
                ('price', models.FloatField(null=True, blank=True)),
                ('group', models.ForeignKey(to='experiences.OptionGroup')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='booking',
            name='option_item',
            field=models.ManyToManyField(to='experiences.OptionItem', related_name='booking_option_item'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='customitineraryrequest',
            name='email',
            field=models.EmailField(max_length=75),
            preserve_default=True,
        ),
    ]
