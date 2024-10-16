from django.shortcuts import render
from rest_framework import viewsets, permissions
from .serializers import PatientSerializer
from .models import Patient


class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    queryset = Patient.objects.all()
    permission_classes = [permissions.AllowAny]


