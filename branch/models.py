from django.db import models
import uuid

class Branch(models.Model):
    name = models.CharField(max_length=255)
    identyficator = models.CharField(max_length=36)
    is_mother = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.identyficator:
            self.identyficator = str(uuid.uuid4())
        super().save(*args, **kwargs)