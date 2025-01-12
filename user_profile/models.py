from django.db import models
from django_tenants.utils import get_tenant_model
from django.conf import settings
from institution.models import Institution
from branch.models import Branch

UserRoles = [
    ('user', 'User'),
    ('doctor', 'Doctor'),
    ('assistant', 'Assistant'),
    ('reception', 'Reception'),
    ('none', 'None') 
]


class ProfileCentralUser(models.Model):
    # admin
    branch = models.ForeignKey('branch.Branch', on_delete=models.CASCADE, null=True, blank=True, related_name='profile_central_user')
    role = models.CharField(max_length=30, choices=UserRoles, default='none')
    is_admin = models.BooleanField(default=False)

    # personal
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name='profile')
    name = models.CharField(max_length=255, default=None, blank=True, null=True)
    surname = models.CharField(max_length=255, default=None, blank=True, null=True)
    pesel = models.CharField(max_length=255, default=None, blank=True, null=True)
    date_of_birth = models.DateField(default=None, blank=True, null=True)
    sex = models.CharField(max_length=255, default=None, blank=True, null=True)

    # address
    street = models.CharField(max_length=255, default=None, blank=True, null=True)
    house_number = models.CharField(max_length=255, default=None, blank=True, null=True)
    local_number = models.CharField(max_length=255, default=None, blank=True, null=True)
    zip_code = models.CharField(max_length=255, default=None, blank=True, null=True)
    city = models.CharField(max_length=255, default=None, blank=True, null=True)

    # contact
    phone_number = models.CharField(max_length=255, default=None, blank=True, null=True)

    # administrator data
    nip = models.CharField(max_length=255, default=None, blank=True, null=True)
    
    def __str__(self):
        return f'Profile for {self.user.email}'
    

class EmployeeSchedule(models.Model):
    employee = models.ForeignKey(ProfileCentralUser, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='schedules', default=None)
    day_num = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
