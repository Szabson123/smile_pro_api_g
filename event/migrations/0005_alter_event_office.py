# Generated by Django 5.1.1 on 2024-11-10 18:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0004_office_event_office_planchange'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='office',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='event.office'),
        ),
    ]
