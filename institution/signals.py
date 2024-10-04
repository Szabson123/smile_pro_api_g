from django.db.models.signals import post_save
from django.dispatch import receiver
from institution.models import Institution, Domain

@receiver(post_save, sender=Institution)
def create_domain_for_institution(sender, instance, created, **kwargs):
    if created:
        domain = Domain()
        domain.domain = f'{instance.schema_name}.localhost'
        domain.tenant = instance
        domain.is_primary = True
        domain.save()
