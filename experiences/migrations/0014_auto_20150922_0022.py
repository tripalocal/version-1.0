# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0013_add_abstractexperienc_ptr'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experience',
            name='id',
            field = models.AutoField(primary_key=True, db_column='abstractexperience_ptr_id'),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name='experience',
            old_name='id',
            new_name='abstractexperience_ptr',
        ),
    ]
