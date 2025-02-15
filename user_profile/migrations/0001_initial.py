# Generated by Django 5.1.1 on 2024-11-02 13:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfileCentralUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('owner', models.BooleanField(default=False)),
                ('name', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('surname', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('pesel', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('date_of_birth', models.DateField(blank=True, default=None, null=True)),
                ('sex', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('street', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('house_number', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('local_number', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('zip_code', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('city', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('phone_number', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('nip', models.CharField(blank=True, default=None, max_length=255, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
