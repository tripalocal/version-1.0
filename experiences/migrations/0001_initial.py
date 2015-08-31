# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import experiences.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BlockOutTimePeriod',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('repeat_end_date', models.DateField()),
                ('repeat', models.BooleanField(default=False)),
                ('repeat_cycle', models.CharField(max_length=50)),
                ('repeat_frequency', models.IntegerField()),
                ('repeat_extra_information', models.CharField(max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('coupon_extra_information', models.TextField()),
                ('guest_number', models.IntegerField()),
                ('datetime', models.DateTimeField()),
                ('status', models.CharField(max_length=50)),
                ('submitted_datetime', models.DateTimeField()),
                ('refund_id', models.CharField(max_length=50)),
                ('booking_extra_information', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('promo_code', models.CharField(max_length=10)),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('rules', models.TextField()),
                ('title', models.CharField(max_length=50)),
                ('description', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Experience',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('type', models.CharField(max_length=50)),
                ('language', models.CharField(max_length=50)),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('repeat', models.BooleanField(default=False)),
                ('repeat_cycle', models.CharField(max_length=50)),
                ('repeat_frequency', models.IntegerField()),
                ('repeat_extra_information', models.CharField(max_length=50)),
                ('allow_instant_booking', models.BooleanField(default=False)),
                ('duration', models.IntegerField()),
                ('guest_number_max', models.IntegerField()),
                ('guest_number_min', models.IntegerField()),
                ('price', models.DecimalField(max_digits=6, decimal_places=2)),
                ('currency', models.CharField(max_length=10)),
                ('dynamic_price', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=50)),
                ('address', models.TextField()),
                ('status', models.CharField(max_length=50)),
                ('guests', models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='experience_guests')),
                ('hosts', models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='experience_hosts')),
            ],
            options={
                'ordering': ['id'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExperienceActivity',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('activity', models.TextField()),
                ('language', models.CharField(max_length=2)),
                ('experience', models.ForeignKey(to='experiences.Experience')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExperienceDescription',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('description', models.TextField()),
                ('language', models.CharField(max_length=2)),
                ('experience', models.ForeignKey(to='experiences.Experience')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExperienceDress',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('dress', models.TextField()),
                ('language', models.CharField(max_length=2)),
                ('experience', models.ForeignKey(to='experiences.Experience')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExperienceDropoffSpot',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('dropoff_spot', models.TextField()),
                ('language', models.CharField(max_length=2)),
                ('experience', models.ForeignKey(to='experiences.Experience')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExperienceI18n',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('title', models.CharField(max_length=100, null=True)),
                ('description', models.TextField(null=True)),
                ('language', models.CharField(max_length=2, null=True)),
                ('activity', models.TextField(null=True)),
                ('interaction', models.TextField(null=True)),
                ('dress', models.TextField(null=True)),
                ('meetup_spot', models.TextField(null=True)),
                ('dropoff_spot', models.TextField(null=True)),
                ('experience', models.ForeignKey(to='experiences.Experience')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExperienceInteraction',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('interaction', models.TextField()),
                ('language', models.CharField(max_length=2)),
                ('experience', models.ForeignKey(to='experiences.Experience')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExperienceMeetupSpot',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('meetup_spot', models.TextField()),
                ('language', models.CharField(max_length=2)),
                ('experience', models.ForeignKey(to='experiences.Experience')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExperienceTag',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('tag', models.CharField(max_length=100)),
                ('language', models.CharField(max_length=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExperienceTitle',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('title', models.CharField(max_length=100)),
                ('language', models.CharField(max_length=2)),
                ('experience', models.ForeignKey(to='experiences.Experience')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InstantBookingTimePeriod',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('repeat_end_date', models.DateField()),
                ('repeat', models.BooleanField(default=False)),
                ('repeat_cycle', models.CharField(max_length=50)),
                ('repeat_frequency', models.IntegerField()),
                ('repeat_extra_information', models.CharField(max_length=50)),
                ('experience', models.ForeignKey(to='experiences.Experience')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('charge_id', models.CharField(max_length=32)),
                ('street1', models.CharField(max_length=50)),
                ('street2', models.CharField(max_length=50)),
                ('city', models.CharField(max_length=20)),
                ('zip_code', models.CharField(max_length=4)),
                ('state', models.CharField(max_length=3)),
                ('country', models.CharField(max_length=15)),
                ('phone_number', models.CharField(max_length=15)),
                ('booking', models.ForeignKey(to='experiences.Booking', related_name='booking')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('directory', models.CharField(max_length=50)),
                ('image', models.ImageField(upload_to=experiences.models.Photo.upload_path)),
                ('experience', models.ForeignKey(to='experiences.Experience')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('comment', models.TextField()),
                ('rate', models.IntegerField()),
                ('datetime', models.DateTimeField()),
                ('personal_comment', models.TextField()),
                ('operator_comment', models.TextField()),
                ('experience', models.ForeignKey(to='experiences.Experience')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WhatsIncluded',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('item', models.CharField(max_length=50)),
                ('included', models.BooleanField(default=False)),
                ('details', models.TextField()),
                ('language', models.CharField(max_length=2)),
                ('experience', models.ForeignKey(to='experiences.Experience')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='experience',
            name='tags',
            field=models.ManyToManyField(to='experiences.ExperienceTag', related_name='experience_tags'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='booking',
            name='coupon',
            field=models.ForeignKey(to='experiences.Coupon'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='booking',
            name='experience',
            field=models.ForeignKey(to='experiences.Experience'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='booking',
            name='payment',
            field=models.ForeignKey(to='experiences.Payment', related_name='payment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='booking',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='blockouttimeperiod',
            name='experience',
            field=models.ForeignKey(to='experiences.Experience'),
            preserve_default=True,
        ),
    ]
