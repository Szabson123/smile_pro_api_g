from django.db.models.signals import post_save
from django.dispatch import receiver
from institution.models import Institution, Domain
from custom_user.models import CentralUser
from user_profile.models import ProfileCentralUser
from django_tenants.utils import schema_context
from django.conf import settings

@receiver(post_save, sender=Institution)
def create_domain_for_institution(sender, instance, created, **kwargs):
    if created:
        domain = Domain()
        domain.domain = f'localhost/{instance.schema_name}'
        domain.tenant = instance
        domain.is_primary = True
        domain.save()

@receiver(post_save, sender=Institution)
def create_profile_central_user(sender, instance, **kwargs):
    central_user = instance.owner_user
    if central_user:
        with schema_context(instance.schema_name):
            profile, created = ProfileCentralUser.objects.get_or_create(user=central_user)

