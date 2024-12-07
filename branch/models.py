from django.db import models
import uuid

class Branch(models.Model):
    owner = models.ForeignKey('user_profile.ProfileCentralUser', on_delete=models.CASCADE, null=True, blank=True, related_name='branches_owner')
    name = models.CharField(max_length=255, null=True, blank=True)
    identyficator = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_mother = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name or "Unnamed Branch"