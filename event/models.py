from django.db import models
from user_profile.models import ProfileCentralUser

class Event(models.Model):
    name = models.CharField(max_length=255)
    profile = models.ForeignKey(ProfileCentralUser, on_delete=models.CASCADE)

TypeFree = [
    ('zwolnienie', 'Zwolnienie')
    ('urlop', 'Urlop')
    ('inne', 'Inne')
]

class Absence(models.Model):
    profile = models.ForeignKey(ProfileCentralUser, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    type = models.CharField(max_length=30, choices=TypeFree, default='inne')
    reason = models.TextField(null=True, blank=True)