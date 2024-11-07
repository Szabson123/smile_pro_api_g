from rest_framework import viewsets, status

from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

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
    parser_classes = [JSONParser]

    def post(self, request):
        data = request.data
        doctor_id = data.get('doctor_id')
        interval_minutes = data.get('interval', 15)
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')

        if not all([doctor_id, start_date_str, end_date_str]):
            return Response({'error': 'Brak wymaganych parametrów.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            interval_minutes = int(interval_minutes)
            if interval_minutes <= 0:
                raise ValueError
        except ValueError:
            return Response({'error': 'Nieprawidłowa wartość interwału.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if start_date > end_date:
                return Response({'error': 'Data początkowa musi być wcześniejsza lub równa dacie końcowej.'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'Nieprawidłowy format daty. Użyj YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            doctor = ProfileCentralUser.objects.get(id=doctor_id)
            if doctor.role != 'doctor':
                return Response({'error': 'Użytkownik nie jest lekarzem.'}, status=status.HTTP_400_BAD_REQUEST)
        except ProfileCentralUser.DoesNotExist:
            return Response({'error': 'Nie znaleziono lekarza.'}, status=status.HTTP_404_NOT_FOUND)

        slots = get_time_slots_for_date_range(doctor, start_date, end_date, interval_minutes)

        return Response(slots, status=status.HTTP_200_OK)



def get_time_slots_for_date_range(doctor, start_date, end_date, interval_minutes):
    slots = []
    current_date = start_date
    delta = timedelta(days=1)
    while current_date <= end_date:
        daily_slots = generate_daily_time_slots(doctor, current_date, interval_minutes)
        appointments = Event.objects.filter(
            profile=doctor,
            date=current_date
        )
        daily_slots = mark_occupied_slots(daily_slots, appointments)
        slots.extend(daily_slots)
        current_date += delta
    return slots