from django.db import models
from user_profile.models import ProfileCentralUser

class Event(models.Model):
    name = models.CharField(max_length=255)
    profile = models.ForeignKey(ProfileCentralUser, on_delete=models.CASCADE)
