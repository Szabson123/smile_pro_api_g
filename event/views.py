from rest_framework import viewsets

from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Event
from .serializers import EventSerializer
from user_profile.models import ProfileCentralUser

class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        profile = ProfileCentralUser.objects.filter(user=user).first()
        if profile:
            return Event.objects.filter(profile=profile)
        else:
            return Event.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        profile = ProfileCentralUser.objects.filter(user=user).first()
        if profile:
            serializer.save(profile=profile)
        else:
            raise PermissionDenied("Nie masz uprawnień do tworzenia wydarzeń w tym tenancie.")

    @action(detail=False, methods=['get'])
    def list_all_events(self, request):
        user = self.request.user
        profile = ProfileCentralUser.objects.filter(user=user).first()
        if profile and profile.owner:
            events = Event.objects.all()
            serializer = self.get_serializer(events, many=True)
            return Response(serializer.data)
        else:
            raise PermissionDenied("Nie masz uprawnień do przeglądania wszystkich wydarzeń.")