from django.db import models
from django_tenants.utils import get_tenant_model
from django.conf import settings
from institution.models import Institution

class ProfileCentralUser(models.Model):
    # admin
    owner = models.BooleanField(default=False)

    # personal
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=255, default=None, blank=True, null=True)
    surname = models.CharField(max_length=255, default=None, blank=True, null=True)
    pesel = models.CharField(max_length=255, default=None, blank=True, null=True)
    date_of_birth = models.DateField(default=None, blank=True, null=True)
    sex = models.CharField(max_length=255, default=None, blank=True, null=True)

    # adress
    street = models.CharField(max_length=255, default=None, blank=True, null=True)
    house_number = models.CharField(max_length=255, default=None, blank=True, null=True)
    local_number = models.CharField(max_length=255, default=None, blank=True, null=True)
    zip_code = models.CharField(max_length=255, default=None, blank=True, null=True)
    city = models.CharField(max_length=255, default=None, blank=True, null=True)

    # conntact
    phone_number = models.CharField(max_length=255, default=None, blank=True, null=True)

    # administrator data
    nip = models.CharField(max_length=255, default=None, blank=True, null=True)
    

    def __str__(self):
        return f'Profile for {self.user.email}'