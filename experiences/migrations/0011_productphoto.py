# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import experiences.models


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0010_auto_20150917_2152'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductPhoto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('image', models.ImageField(upload_to=experiences.models.ProductPhoto.upload_path)),
                ('product', models.ForeignKey(related_name='photos', to='experiences.Product')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
