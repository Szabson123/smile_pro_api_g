from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from institution.models import Institution, Domain, UserInstitution
from custom_user.models import CentralUser
from user_profile.models import ProfileCentralUser
from django_tenants.utils import schema_context
from django.conf import settings
from django_tenants.utils import tenant_context

import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Institution)
def create_domain_for_institution(sender, instance, created, **kwargs):
    if created:
        sanitized_schema_name = instance.schema_name.replace('_', '-')
        domain = Domain()
        domain.domain = f'{sanitized_schema_name}.localhost'
        domain.tenant = instance
        domain.is_primary = True
        domain.save()

@receiver(pre_save, sender=Institution)
def store_owner_user_old_value(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Institution.objects.get(pk=instance.pk)
            instance._owner_user_old = old_instance.owner_user
        except Institution.DoesNotExist:
            instance._owner_user_old = None
    else:
        instance._owner_user_old = None

@receiver(post_save, sender=Institution)
def handle_owner_user_change(sender, instance, **kwargs):
    central_user = instance.owner_user
    old_owner_user = getattr(instance, '_owner_user_old', None)

    if central_user and old_owner_user != central_user:
        try:
            UserInstitution.objects.get_or_create(user=central_user, institution=instance)

        except Exception as e:
            logger.error(f'Error handling owner_user change: {e}')


