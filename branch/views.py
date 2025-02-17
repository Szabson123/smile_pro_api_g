from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets

from .serializers import BranchSerializer
from .models import Branch
from user_profile.permissions import IsOwnerOfInstitution


class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    queryset = Branch.objects.none()
    permission_classes = [IsOwnerOfInstitution]
    

    
    
    
