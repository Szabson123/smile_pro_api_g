from django.db import models
import uuid

from user_profile.models import ProfileCentralUser

class Branch(models.Model):
    owner = models.ForeignKey(ProfileCentralUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    identyficator = models.CharField(max_length=36)
    is_mother = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.identyficator:
            self.identyficator = str(uuid.uuid4())
        super().save(*args, **kwargs)