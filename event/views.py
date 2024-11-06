from rest_framework import viewsets

from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Event
from .serializers import EventSerializer
from user_profile.models import ProfileCentralUser
from user_profile.permissions import IsOwnerOfInstitution, HasProfilePermission


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [HasProfilePermission]
    
