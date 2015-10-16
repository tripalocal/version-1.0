# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0028_auto_20151016_1104'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='adult_number',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='booking',
            name='children_number',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='customitinerary',
            name='status',
            field=models.CharField(max_length=10, default='draft'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='booking',
            name='booking_extra_information',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='booking',
            name='coupon',
            field=models.ForeignKey(null=True, blank=True, to='experiences.Coupon'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='booking',
            name='payment',
            field=models.ForeignKey(null=True, blank=True, related_name='payment', to='experiences.Payment'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='booking',
            name='refund_id',
            field=models.CharField(max_length=50, null=True, blank=True),
            preserve_default=True,
        )
    ]
