from django.db import models
import uuid


class Branch(models.Model):
    owner = models.ForeignKey('user_profile.ProfileCentralUser', on_delete=models.CASCADE, null=True, blank=True, related_name='branches_owner')
    name = models.CharField(max_length=255, null=True, blank=True)
    identyficator = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_mother = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name or "Unnamed Branch"
    

class BranchInfo(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='info')
    bdo_number = models.CharField(max_length=255)
    regon = models.CharField(max_length=255)
    nip = models.CharField(max_length=255)
    v_register_code = models.CharField(max_length=255)
    additional_name = models.CharField(max_length=255)
    town = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    post_code = models.CharField(max_length=255)
    bank = models.CharField(max_length=255)
    bank_acc = models.CharField(max_length=255)