# Generated by Django 5.1.1 on 2025-02-13 20:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('branch', '0004_alter_branch_identyficator'),
    ]

    operations = [
        migrations.CreateModel(
            name='BranchInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='info', to='branch.branch')),
            ],
        ),
    ]
