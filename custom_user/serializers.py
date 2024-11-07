from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from institution.models import Institution, Domain, UserInstitution

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # Get institutions associated with the user
        user_institutions = UserInstitution.objects.filter(user=user)

        domains = []
        for user_institution in user_institutions:
            institution = user_institution.institution
            institution_domains = Domain.objects.filter(tenant=institution)
            domains.extend([domain.domain for domain in institution_domains])

        data['domains'] = list(set(domains))
        return data

