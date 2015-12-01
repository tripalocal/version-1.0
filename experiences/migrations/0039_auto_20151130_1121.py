# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('experiences', '0038_auto_20151125_1606'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='experienceactivity',
            name='experience',
        ),
        migrations.RemoveField(
            model_name='experiencedescription',
            name='experience',
        ),
        migrations.RemoveField(
            model_name='experiencedress',
            name='experience',
        ),
        migrations.RemoveField(
            model_name='experiencedropoffspot',
            name='experience',
        ),
        migrations.RemoveField(
            model_name='experienceinteraction',
            name='experience',
        ),
        migrations.RemoveField(
            model_name='experiencemeetupspot',
            name='experience',
        ),
        migrations.RemoveField(
            model_name='experiencetitle',
            name='experience',
        ),
        migrations.RemoveField(
            model_name='newproduct',
            name='provider',
        ),
        migrations.AddField(
            model_name='booking',
            name='host',
            field=models.ForeignKey(null=True, blank=True, related_name='booking_host', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='newproduct',
            name='suppliers',
            field=models.ManyToManyField(related_name='product_suppliers', to='experiences.Provider'),
        ),
        migrations.AlterField(
            model_name='booking',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='booking_user'),
        ),
        migrations.DeleteModel(
            name='ExperienceActivity',
        ),
        migrations.DeleteModel(
            name='ExperienceDescription',
        ),
        migrations.DeleteModel(
            name='ExperienceDress',
        ),
        migrations.DeleteModel(
            name='ExperienceDropoffSpot',
        ),
        migrations.DeleteModel(
            name='ExperienceInteraction',
        ),
        migrations.DeleteModel(
            name='ExperienceMeetupSpot',
        ),
        migrations.DeleteModel(
            name='ExperienceTitle',
        ),
    ]
