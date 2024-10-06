from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from institution.models import Institution

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Wywołanie domyślnej metody, która zwróci access i refresh tokeny
        data = super().validate(attrs)
        
        # Użytkownik, który się loguje
        user = self.user

        # Pobieranie instytucji związanej z użytkownikiem
        institution = Institution.objects.filter(owner_user=user).first()

        # Dodanie domeny instytucji do odpowiedzi
        if institution:
            data['domain'] = f'localhost/{institution.schema_name}'

        return data
