from django.shortcuts import render
from rest_framework import viewsets, permissions, generics, filters, status
from .serializers import PatientSerializer, TreatmentListSerializer, TreatmentSerializer, TreatmentPlanSerializer
from .models import Patient, Treatment, TreatmentPlan
from event.models import Absence
from branch.models import Branch
from user_profile.permissions import HasProfilePermission
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.views import APIView
from rest_framework.response import Response
import random
from rest_framework.pagination import PageNumberPagination
from event.renderers import ORJSONRenderer
from rest_framework.filters import SearchFilter

class CustomPatientPagination(PageNumberPagination):
    page_size = 100
    max_page_size = 200


class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    filterset_fields = ['id', 'name', 'surname', 'email']
    ordering_fields = ['id', 'name', 'surname', 'email']
    ordering = ['name']
    pagination_class = CustomPatientPagination
    renderer_classes = [ORJSONRenderer]
    filter_backends = [SearchFilter]
    search_fields = ['name', 'surname', 'email']

    def get_queryset(self):
        branch_uuid = self.kwargs.get('branch_uuid')
        queryset = Patient.objects.filter(branch__identyficator=branch_uuid).select_related('branch')
        return queryset

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
        patient = self.kwargs.get('patient_id')
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
        patient = self.kwargs.get('patient_id')
        return Treatment.objects.filter(branch__identyficator=branch_uuid, patient__id=patient)

    def perform_create(self, serializer):
        branch_uuid = self.kwargs.get('branch_uuid')
        branch = Branch.objects.get(identyficator=branch_uuid)
        patient = self.kwargs.get('patient_id')
        serializer.save(branch=branch, patient=patient)
    
    def list(self, request, *args, **kwargs):
        raise MethodNotAllowed("GET", detail="List action is not allowed for this endpoint.")
    

class TreatmentPlanViewSet(viewsets.ModelViewSet):
    serializer_class = TreatmentPlanSerializer
    permission_classes = [HasProfilePermission]

    def get_queryset(self):
        branch_uuid = self.kwargs.get('branch_uuid')
        patient = self.kwargs.get('patient_id')
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


class TreatmentInPlanCreateView(generics.CreateAPIView):
    serializer_class = TreatmentSerializer
    permission_classes = [HasProfilePermission]

    def perform_create(self, serializer):
        branch_uuid = self.kwargs.get('branch_uuid')
        plan_id = self.kwargs.get('plan_id')
        branch = Branch.objects.get(identyficator=branch_uuid)
        treatment_plan = TreatmentPlan.objects.get(pk=plan_id, branch=branch)
        
        serializer.save(branch=branch, treatment_plan=treatment_plan)


class GeneratePatientsView(APIView):
    """
    Widok do automatycznego tworzenia 50 000 pacjentów.
    """

    def post(self, request, *args, **kwargs):
        branch_uuid = self.kwargs.get('branch_uuid')
        branch = Branch.objects.get(identyficator=branch_uuid)
        number_of_patients = 500

        patients_data = []
        for i in range(number_of_patients):
            patients_data.append({
                "name": f"Patient{i}",
                "surname": f"Surname{i}",
                "age": random.randint(1, 100)
            })

        serializer = PatientSerializer(data=patients_data, many=True)
        if serializer.is_valid():
            serializer.save(branch=branch)
            return Response(
                {"message": f"{number_of_patients} patients have been created successfully."},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
