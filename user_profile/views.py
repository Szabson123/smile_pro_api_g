from django.shortcuts import render
from django_tenants.utils import schema_context

from rest_framework.views import APIView
from rest_framework.response import Response
from urllib.parse import urlparse
from institution.models import Domain
from user_profile.models import ProfileCentralUser
from .serializers import ProfileCentralUserSerializer
from django.db import DatabaseError
from django.db import DatabaseError

class ProfileListView(APIView):
    def get(self, request, *args, **kwargs):
        # Pobranie pełnego URL-a
        full_url = request.build_absolute_uri()
        
        # Parsowanie URL-a, by uzyskać domenę
        parsed_url = urlparse(full_url)
        domain = parsed_url.hostname.rstrip('.')  # Usunięcie kropki na końcu
        
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
        except DatabaseError:
            return Response({'error': 'Database error'}, status=500)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

