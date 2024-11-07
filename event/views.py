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
from datetime import timedelta, datetime

from user_profile.utils import generate_daily_time_slots, mark_occupied_slots


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [HasProfilePermission]
    

class TimeSlotView(APIView):
    permission_classes = [IsAuthenticated, HasProfilePermission]

    def get(self, request):
        doctor_id = request.query_params.get('doctor_id')
        interval_minutes = int(request.query_params.get('interval', 15))
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        # Validate inputs
        if not all([doctor_id, start_date_str, end_date_str]):
            return Response({'error': 'Missing parameters'}, status=400)

        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

        # Get doctor profile
        try:
            doctor = ProfileCentralUser.objects.get(id=doctor_id, role='doctor')
        except ProfileCentralUser.DoesNotExist:
            return Response({'error': 'Doctor not found'}, status=404)

        slots = get_time_slots_for_date_range(doctor, start_date, end_date, interval_minutes)

        return Response(slots)


def get_time_slots_for_date_range(doctor, start_date, end_date, interval_minutes):
    slots = []
    current_date = start_date
    while current_date <= end_date:
        daily_slots = generate_daily_time_slots(doctor, current_date, interval_minutes)
        # Fetch appointments for the doctor on the current date
        appointments = Event.objects.filter(
            profile=doctor,
            date=current_date
        )
        daily_slots = mark_occupied_slots(daily_slots, appointments)
        slots.extend(daily_slots)
        current_date += timedelta(days=1)
    return slots