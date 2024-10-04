from django.db import models
from django_tenants.utils import get_tenant_model
from django.conf import settings

class ProfileCentralUser(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # odniesienie do CentralUser
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)

    def __str__(self):
        return f'Profile for {self.user.email}'