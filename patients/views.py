from django.shortcuts import render
from rest_framework import viewsets, permissions, generics
from .serializers import PatientSerializer, TreatmentListSerializer, TreatmentSerializer, TreatmentPlanSerializer
from .models import Patient, Treatment, TreatmentPlan
from event.models import Absence
from branch.models import Branch
from user_profile.permissions import HasProfilePermission
from rest_framework.exceptions import MethodNotAllowed

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


class TreatmentList(generics.ListAPIView):
    serializer_class = TreatmentListSerializer
    queryset = Treatment.objects.none()
    permission_classes = [HasProfilePermission]


    def get_queryset(self):
        branch_uuid = self.kwargs.get('branch_uuid')
        patient = self.request.query_params.get('patient')
        if branch_uuid and patient:
            return Treatment.objects.filter(
                branch__identyficator=branch_uuid, 
                patient__id=patient
            )
        return Treatment.objects.none()


class TreatmentViewSet(viewsets.ModelViewSet):
    serializer_class = TreatmentSerializer
    permission_classes = [HasProfilePermission]

    def get_queryset(self):
        branch_uuid = self.kwargs.get('branch_uuid')
        return Treatment.objects.filter(branch__identyficator=branch_uuid)

    def perform_create(self, serializer):
        branch_uuid = self.kwargs.get('branch_uuid')
        branch = Branch.objects.get(identyficator=branch_uuid)
        serializer.save(branch=branch)
    
    def list(self, request, *args, **kwargs):
        raise MethodNotAllowed("GET", detail="List action is not allowed for this endpoint.")
    

class TreatmentPlanViewSet(viewsets.ModelViewSet):
    serializer_class = TreatmentPlanSerializer
    permission_classes = [HasProfilePermission]

    def get_queryset(self):
        branch_uuid = self.kwargs.get('branch_uuid')
        patient = self.request.query_params.get('patient')
        if branch_uuid and patient:
            return TreatmentPlan.objects.filter(
                branch__identyficator=branch_uuid, 
                patient__id=patient
            )
        return Treatment.objects.none()

    def perform_create(self, serializer):
        branch_uuid = self.kwargs.get('branch_uuid')
        branch = Branch.objects.get(identyficator=branch_uuid)
        serializer.save(branch=branch)


class PlanTreatmentCreateView(generics.CreateAPIView):
    serializer_class = TreatmentSerializer
    permission_classes = [HasProfilePermission]

    def perform_create(self, serializer):
        branch_uuid = self.kwargs.get('branch_uuid')
        plan_id = self.kwargs.get('plan_id')
        branch = Branch.objects.get(identyficator=branch_uuid)
        treatment_plan = TreatmentPlan.objects.get(pk=plan_id, branch=branch)
        
        serializer.save(branch=branch, treatment_plan=treatment_plan)