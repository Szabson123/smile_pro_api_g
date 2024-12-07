from django.shortcuts import render
from rest_framework import viewsets, permissions
from .serializers import PatientSerializer
from .models import Patient
from event.models import Absence
from branch.models import Branch
from user_profile.permissions import HasProfilePermission

class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    permission_classes = [HasProfilePermission]

    def get_queryset(self):
        branch_uuid = self.kwargs.get('branch_uuid')
        return Patient.objects.filter(branch__identyficator=branch_uuid)

    def perform_create(self, serializer):
        branch_uuid = self.kwargs.get('branch_uuid')
        branch = Branch.objects.get(identyficator=branch_uuid)
        serializer.save(branch=branch)

