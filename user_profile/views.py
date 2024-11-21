from django.shortcuts import render
from django_tenants.utils import schema_context
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from rest_framework.views import APIView

from .serializers import ProfileCentralUserSerializer, MeProfileSerializer
from user_profile.serializers import EmployeeProfileSerializer
from user_profile.models import ProfileCentralUser, UserRoles
from user_profile.permissions import HasProfilePermission, IsOwnerOfInstitution

# Lista pracowników na zasadzie Imie nazwiko rola
class ProfileListView(ListAPIView):
    serializer_class = ProfileCentralUserSerializer
    permission_classes = [IsOwnerOfInstitution]
    
    def get_queryset(self):
        
        return ProfileCentralUser.objects.all()


class CurrentProfile(APIView):
    permission_classes = [HasProfilePermission]

    def get(self, request):
        serializer = MeProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)

# Cały CRUD Związany z pracownikami 
class EmployeeProfileViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsOwnerOfInstitution]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role']

    def get_queryset(self):
        return ProfileCentralUser.objects.all()

    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['POST'])    
    def change_role(self, request):
        profile = self.get_object()
        new_role = request.data.get('role')
        
        if new_role not in dict(UserRoles):
            return Response({'error': 'Nie ma takiej roli'}, status=status.HTTP_400_BAD_REQUEST)
        
        profile.role = new_role
        profile.save()
        
        return Response({'status': "Rola została zmieniona"}, status=status.HTTP_200_OK)