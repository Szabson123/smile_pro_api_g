# Generated by Django 5.1.1 on 2024-11-10 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0004_remove_doctorschedule_day_of_week_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='doctorschedule',
            name='date',
        ),
        migrations.AddField(
            model_name='doctorschedule',
            name='day_num',
            field=models.IntegerField(default=8),
        ),
    ]
