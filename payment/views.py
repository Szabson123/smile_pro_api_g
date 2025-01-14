from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ValidationError

from .serializers import DepositSerializer, ObligationSerializerMain, GetUserHistory
from .models import Deposits, Obligation
from user_profile.permissions import IsOwnerOfInstitution
from patients.models import Patient
from branch.models import Branch

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

class ObligationViewSet(viewsets.ModelViewSet):
    serializer_class = ObligationSerializerMain
    queryset = Obligation.objects.none()
    permission_classes = [IsOwnerOfInstitution]

    def get_queryset(self):
        branch_uuid = self.kwargs.get('branch_uuid')
        patient_id = self.kwargs.get('patient_id')
        
        if not branch_uuid or not patient_id:
            raise ValidationError("Both 'branch_uuid' and 'patient_id' are required.")
        
        queryset = Obligation.objects.filter(branch__identyficator=branch_uuid, patient=patient_id).select_related('branch', 'patient')

        return queryset
    
    def perform_create(self, serializer):
        branch_uuid = self.kwargs.get('branch_uuid')
        patient_id = self.kwargs.get('patient_id')

        branch = get_object_or_404(Branch, identyficator=branch_uuid)
        patient = get_object_or_404(Patient, id=patient_id)

        serializer.save(branch=branch, patient=patient)

        return serializer


class DepositViewSet(viewsets.ModelViewSet):
    serializer_class = DepositSerializer
    queryset = Deposits.objects.none()
    permission_classes = [IsOwnerOfInstitution]

    def get_queryset(self):
        branch_uuid = self.kwargs.get('branch_uuid')
        patient_id = self.kwargs.get('patient_id')
        
        if not branch_uuid or not patient_id:
            raise ValidationError("Both 'branch_uuid' and 'patient_id' are required.")
        
        queryset = Deposits.objects.filter(branch__identyficator=branch_uuid, patient=patient_id).select_related('branch', 'patient')

        return queryset
    
    def perform_create(self, serializer):
        branch_uuid = self.kwargs.get('branch_uuid')
        patient_id = self.kwargs.get('patient_id')

        branch = get_object_or_404(Branch, identyficator=branch_uuid)
        patient = get_object_or_404(Patient, id=patient_id)

        serializer.save(branch=branch, patient=patient)

        return serializer
    

class UserHistoryApiView(APIView):
    permission_classes = [IsOwnerOfInstitution]

    def get(self, request, branch_uuid, patient_id):
        branch = get_object_or_404(Branch, identyficator=branch_uuid)
        patient = get_object_or_404(Patient, id=patient_id)

        deposit_qs = Deposits.objects.filter(branch=branch, patient=patient)
        obligation_qs = Obligation.objects.filter(branch=branch, patient=patient)

        serializer = GetUserHistory(
            instance=patient,
            context={
                'deposit_qs': deposit_qs,
                'obligation_qs': obligation_qs
            }
        )
        return Response(serializer.data, status=200)


