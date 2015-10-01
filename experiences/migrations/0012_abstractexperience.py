# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('experiences', '0009_auto_20150917_1642'),
    ]

    operations = [
        migrations.CreateModel(
            name='AbstractExperience',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('polymorphic_ctype', models.ForeignKey(related_name='polymorphic_experiences.abstractexperience_set+', editable=False, null=True, to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
