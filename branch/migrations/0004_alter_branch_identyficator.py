# Generated by Django 5.1.1 on 2024-12-07 11:10

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('branch', '0003_alter_branch_identyficator_alter_branch_owner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='branch',
            name='identyficator',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]