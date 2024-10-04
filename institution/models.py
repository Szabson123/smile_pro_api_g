from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
import re
from django.core.exceptions import ValidationError

class Institution(TenantMixin):
    name = models.CharField(max_length=255)
    schema_name = models.CharField(max_length=63, unique=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    auto_create_schema = True
    auto_drop_schema = False

    def save(self, *args, **kwargs):
        if not self.schema_name:
            # Generowanie schema_name na podstawie name
            schema_name = self.name.lower().replace(' ', '_')
            # Usuwanie niedozwolonych znaków
            schema_name = re.sub(r'[^a-z0-9_]', '', schema_name)
            # Upewnienie się, że nie zaczyna się od cyfry
            if not re.match(r'^[a-z_]', schema_name):
                schema_name = 'a_' + schema_name
            self.schema_name = schema_name
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if not re.match(r'^[a-z_][a-z0-9_]*$', self.schema_name):
            raise ValidationError("Invalid schema_name. It must start with a letter or underscore and contain only lowercase letters, numbers, and underscores.")

    def __str__(self):
        return self.name

class Domain(DomainMixin):
    pass
