# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.contenttypes.models import ContentType

from django.db import migrations

def add_abstractexperience_ptr(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Experience = apps.get_model("experiences", "Experience")
    AbstractExperience = apps.get_model("experiences", "AbstractExperience")
    exp_type = ContentType.objects.get(app_label="experiences", model="experience")
    for exp in Experience.objects.all():
        aexp = AbstractExperience(id=exp.id, polymorphic_ctype_id=exp_type.id)
        aexp.save()



class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0012_abstractexperience'),
    ]

    operations = [
        migrations.RunPython(add_abstractexperience_ptr)
    ]
