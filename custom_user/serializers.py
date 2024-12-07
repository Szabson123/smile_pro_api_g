from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from institution.models import Institution, Domain, UserInstitution
from user_profile.models import ProfileCentralUser
from django_tenants.utils import schema_context

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # Get the institutions the user is associated with
        user_institutions = UserInstitution.objects.filter(user=user).select_related('institution')
        institutions = [ui.institution for ui in user_institutions]

        # Get the domains for the institutions
        domains = Domain.objects.filter(tenant__in=institutions).select_related('tenant')
        institution_domain_map = {domain.tenant.id: domain.domain for domain in domains}

        institutions_data = []
        for institution in institutions:
            domain_name = institution_domain_map.get(institution.id)
            domains_list = []

            # Switch to the tenant's schema
            with schema_context(institution.schema_name):
                # Get the user's profiles in this tenant
                profiles = ProfileCentralUser.objects.filter(user=user)
                # For each profile, get the branch
                for profile in profiles:
                    branch = profile.branch
                    if branch:
                        branch_uuid = branch.identyficator
                        # Construct the full domain URL
                        full_domain = f"{domain_name}/{branch_uuid}"
                        domains_list.append(full_domain)

            institution_data = {
                'name': institution.name,
                'address': institution.address,
                'domains': domains_list,
            }
            institutions_data.append(institution_data)

        data['institutions'] = institutions_data
        return data

