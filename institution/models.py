from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
import re
from django.core.exceptions import ValidationError
from custom_user.models import CentralUser

class Institution(TenantMixin):
    name = models.CharField(max_length=255)
    schema_name = models.CharField(max_length=63, unique=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    owner_user = models.ForeignKey(CentralUser, on_delete=models.SET_NULL, null=True, blank=True, default=None)
    auto_create_schema = True
    auto_drop_schema = False
    address = models.CharField(max_length=255, default='', null=True, blank=True)
    vat = models.CharField(max_length=255, default='', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.schema_name:
            base_schema_name = self.name.lower().replace(' ', '_')
            base_schema_name = re.sub(r'[^a-z0-9_]', '', base_schema_name)
            if not re.match(r'^[a-z_]', base_schema_name):
                base_schema_name = 'a_' + base_schema_name

            schema_candidate = base_schema_name

            counter = 1
            while Institution.objects.filter(schema_name=schema_candidate).exists():
                counter += 1
                schema_candidate = f"{base_schema_name}_{counter}"
            
            self.schema_name = schema_candidate

        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if not re.match(r'^[a-z_][a-z0-9_]*$', self.schema_name):
            raise ValidationError("Invalid schema_name. Must start with a letter/underscore and contain only lowercase letters, digits, underscores.")

    def __str__(self):
        return self.name

class Domain(DomainMixin):
    pass


class UserInstitution(models.Model):
    user = models.ForeignKey(CentralUser, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'institution')

    def __str__(self):
        return f'{self.user.email} - {self.institution.name}'
