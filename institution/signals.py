from django.db.models.signals import post_save
from django.dispatch import receiver
from institution.models import Institution, Domain
from custom_user.models import CentralUser
from user_profile.models import ProfileCentralUser
from django_tenants.utils import schema_context


@receiver(post_save, sender=Institution)
def create_domain_for_institution(sender, instance, created, **kwargs):
    if created:
        domain = Domain()
        domain.domain = f'{instance.schema_name}.localhost'
        domain.tenant = instance
        domain.is_primary = True
        domain.save()


def create_profile_central_user(sender, tenant, **kwargs):
    central_user = tenant.owner_user
    if central_user:
        with schema_context(tenant.schema_name):
            ProfileCentralUser.objects.create(user=central_user)

# @receiver(post_save, sender=CentralUser)
# def create_profile_for_user(sender, instance, created, **kwargs):
#     if created:
#         tenant_model = get_tenant_model()
#         tenant_instance = tenant_model.objects.get(name='specific_tenant_name')  # Przykład, jak uzyskać instytucję

#         # Przełączamy się na schemat instytucji
#         with schema_context(tenant_instance.schema_name):
#             ProfileCentralUser.objects.create(user=instance, sensitive_data='Sensitive Data Placeholder')