from django.db import models
from user_profile.models import ProfileCentralUser


class Office(models.Model):
    name = models.CharField(max_length=255)


class Event(models.Model):
    name = models.CharField(max_length=255)
    profile = models.ForeignKey(ProfileCentralUser, on_delete=models.CASCADE)
    date = models.DateField(default=None)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, blank=True, null=True)
    start_time = models.TimeField(default=None)
    end_time = models.TimeField(default=None)

TypeFree = [
    ('zwolnienie', 'Zwolnienie'),
    ('urlop', 'Urlop'),
    ('inne', 'Inne'),
]


class Absence(models.Model):
    profile = models.ForeignKey(ProfileCentralUser, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    type = models.CharField(max_length=30, choices=TypeFree, default='inne')
    reason = models.TextField(null=True, blank=True)


class PlanChange(models.Model):
    doctor = models.ForeignKey(ProfileCentralUser, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()