from django.shortcuts import render
from rest_framework import viewsets

from .serializers import BranchSerializer
from .models import Branch


class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    queryset = Branch.objects.none()
    
    
