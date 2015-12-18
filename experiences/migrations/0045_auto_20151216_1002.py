# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0044_auto_20151204_1626'),
    ]

    operations = [
        migrations.AddField(
            model_name='newproduct',
            name='related_products',
            field=models.ManyToManyField(related_name='newproduct_related', null=True, blank=True, to='experiences.NewProduct'),
            preserve_default=True,
        ),
    ]
