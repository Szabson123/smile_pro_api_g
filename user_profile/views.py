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

from branch.models import Branch


# Lista pracowników na zasadzie Imie nazwiko rola
class ProfileListView(ListAPIView):
    serializer_class = ProfileCentralUserSerializer
    permission_classes = [IsOwnerOfInstitution]
    
    def get_queryset(self):
        branch_uuid = self.kwargs.get('branch_uuid')
        return ProfileCentralUser.objects.filter(branch__identyficator=branch_uuid)

class CurrentProfile(APIView):
    permission_classes = [HasProfilePermission]

    def get(self, request, *args, **kwargs):
        branch_uuid = self.kwargs.get('branch_uuid')
        serializer = MeProfileSerializer(request.user, context={'request': request, 'branch_uuid': branch_uuid})
        return Response(serializer.data)

# Cały CRUD Związany z pracownikami 
class EmployeeProfileViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsOwnerOfInstitution]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role']

    def get_queryset(self):
        branch_uuid = self.kwargs.get('branch_uuid')
        return ProfileCentralUser.objects.filter(branch__identyficator=branch_uuid)

    def perform_create(self, serializer):
        branch_uuid = self.kwargs.get('branch_uuid')
        branch = Branch.objects.get(identyficator=branch_uuid)
        self.request.branch = branch
        # Dodanie branch do walidacji
        serializer.save(branch=branch)
    
