from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status

from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

from .models import Event, Office, Absence
from .serializers import EventSerializer, DoctorScheduleSerializer, AbsenceSerializer, OfficeSerializer
from user_profile.models import ProfileCentralUser, DoctorSchedule
from user_profile.permissions import IsOwnerOfInstitution, HasProfilePermission
from datetime import timedelta, datetime

from user_profile.utils import generate_daily_time_slots, mark_occupied_slots


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [HasProfilePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['profile', 'office', 'patient', 'date']
    

class TimeSlotView(APIView):
    permission_classes = [IsAuthenticated, HasProfilePermission]
    parser_classes = [JSONParser]

    def post(self, request):
        data = request.data
        doctor_id = data.get('doctor_id')
        office_id = data.get('office_id')  
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

        if office_id:
            try:
                office = Office.objects.get(id=office_id)
            except Office.DoesNotExist:
                return Response({'error': 'Nie znaleziono gabinetu.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            office = None
        slots = get_time_slots_for_date_range(doctor, start_date, end_date, interval_minutes, office)

        return Response(slots, status=status.HTTP_200_OK)

def get_time_slots_for_date_range(doctor, start_date, end_date, interval_minutes, office):
    slots = []
    current_date = start_date
    delta = timedelta(days=1)

    while current_date <= end_date:
        daily_slots = generate_daily_time_slots(doctor, current_date, interval_minutes)
        if not daily_slots:
            current_date += delta
            continue  

        appointments = Event.objects.filter(
            profile=doctor,
            date=current_date
        ).select_related('profile', 'office')

        if office:
            other_appointments = Event.objects.filter(
                date=current_date,
                office=office
            ).exclude(profile=doctor).select_related('profile', 'office')
        else:
            other_appointments = []

        daily_slots = mark_occupied_slots(daily_slots, appointments, other_appointments, office)
        slots.extend(daily_slots)
        current_date += delta
    return slots


class AbsenceViewSet(viewsets.ModelViewSet):
    queryset = Absence.objects.all()
    serializer_class = AbsenceSerializer
    permission_classes = [HasProfilePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['profile', 'date']


class DoctorScheduleViewSet(viewsets.ModelViewSet):
    queryset = DoctorSchedule.objects.all()
    serializer_class = DoctorScheduleSerializer
    permission_classes = [HasProfilePermission]


class OfficeViewSet(viewsets.ModelViewSet):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [HasProfilePermission]