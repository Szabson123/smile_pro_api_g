from django.shortcuts import render
from django_tenants.utils import schema_context

from rest_framework.views import APIView
from rest_framework.response import Response

from institution.models import Domain
from user_profile.models import ProfileCentralUser
from .serializers import ProfileCentralUserSerializer

class ProfileListView(APIView):
    """
    Widok zwracający wszystkie profile użytkowników z danego schematu
    na podstawie domeny.
    """

    def get(self, request, *args, **kwargs):
        # Pobranie domeny z żądania (bez portu)
        domain = request.get_host().split(':')[0]

        try:
            # Znalezienie instytucji powiązanej z domeną
            institution_domain = Domain.objects.get(domain=domain)
            schema_name = institution_domain.tenant.schema_name

            # Przełączamy się na odpowiedni schemat przy użyciu schema_context
            with schema_context(schema_name):
                profiles = ProfileCentralUser.objects.all()

                # Serializacja danych profili
                serializer = ProfileCentralUserSerializer(profiles, many=True)
                
            return Response(serializer.data)

        except Domain.DoesNotExist:
            return Response({'error': 'Invalid domain'}, status=400)
