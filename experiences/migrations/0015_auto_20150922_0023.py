# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0014_auto_20150922_0022'),
    ]

    operations = [
        migrations.RunSQL("ALTER TABLE `experiences_experience` ADD CONSTRAINT FOREIGN KEY (`abstractexperience_ptr_id`) REFERENCES `experiences_abstractexperience` (`id`);"),
    ]
