from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from institution.models import Institution, Domain, UserInstitution

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        user_institutions = UserInstitution.objects.filter(user=user).select_related('institution')
        institutions = [ui.institution for ui in user_institutions]

        domains = Domain.objects.filter(tenant__in=institutions).select_related('tenant')

        institution_domain_map = {domain.tenant.id: domain.domain for domain in domains}

        institutions_data = []
        for institution in institutions:
            domain = institution_domain_map.get(institution.id)
            institution_data = {
                'name': institution.name,
                'address': institution.address,
                'domain': domain,
            }
            institutions_data.append(institution_data)

        data['institutions'] = institutions_data
        return data

