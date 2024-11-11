from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status

from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

from .models import Event, Office, Absence, VisitType, Tags
from .serializers import EventSerializer, EmployeeScheduleSerializer, AbsenceSerializer, OfficeSerializer, VisitTypeSerializer, TagsSerializer
from user_profile.models import ProfileCentralUser, EmployeeSchedule
from user_profile.permissions import IsOwnerOfInstitution, HasProfilePermission
from datetime import timedelta, datetime

from user_profile.serializers import ProfileCentralUserSerializer
from user_profile.utils import generate_daily_time_slots, mark_occupied_slots


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [HasProfilePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['doctor', 'office', 'patient', 'date']
    

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
        except ProfileCentralUser.DoesNotExist:
            return Response({'error': 'Nie znaleziono lekarza.'}, status=status.HTTP_404_NOT_FOUND)

        if doctor.role != 'doctor':
            return Response({'error': 'Sloty czasowe mogą być generowane tylko dla lekarzy.'}, status=status.HTTP_400_BAD_REQUEST)

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
    if doctor.role != 'doctor':
        return []

    slots = []
    current_date = start_date
    delta = timedelta(days=1)

    while current_date <= end_date:
        daily_slots = generate_daily_time_slots(doctor, current_date, interval_minutes)
        if not daily_slots:
            current_date += delta
            continue

        appointments = Event.objects.filter(
            doctor=doctor,
            date=current_date
        ).select_related('doctor', 'office')

        if office:
            other_appointments = Event.objects.filter(
                date=current_date,
                office=office
            ).exclude(doctor=doctor).select_related('doctor', 'office')
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
    filterset_fields = ['profile']


class EmployeeScheduleViewSet(viewsets.ModelViewSet):
    queryset = EmployeeSchedule.objects.all()
    serializer_class = EmployeeScheduleSerializer
    permission_classes = [HasProfilePermission]


class OfficeViewSet(viewsets.ModelViewSet):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [HasProfilePermission]


class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    permission_classes = [HasProfilePermission]


class VisitTypeViewSet(viewsets.ModelViewSet):
    queryset = VisitType.objects.all()
    serializer_class = VisitTypeSerializer
    permission_classes = [HasProfilePermission]


class AvailableAssistantsView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request):
        data = request.data
        date_str = data.get('date')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')

        if not all([date_str, start_time_str, end_time_str]):
            return Response({'error': 'Brak wymaganych parametrów.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Nieprawidłowy format daty. Użyj YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError:
            return Response({'error': 'Nieprawidłowy format godziny. Użyj HH:MM.'}, status=status.HTTP_400_BAD_REQUEST)

        if start_time >= end_time:
            return Response({'error': 'Godzina początkowa musi być wcześniejsza niż godzina końcowa.'}, status=status.HTTP_400_BAD_REQUEST)

        assistants = ProfileCentralUser.objects.filter(role='assistant')

        available_assistants = []

        for assistant in assistants:
            day_num = date.weekday()
            try:
                schedule = EmployeeSchedule.objects.get(employee=assistant, day_num=day_num)
            except EmployeeSchedule.DoesNotExist:
                continue

            if start_time < schedule.start_time or end_time > schedule.end_time:
                continue 

            conflicting_events = Event.objects.filter(
                doctor=assistant,
                date=date,
                start_time__lt=end_time,
                end_time__gt=start_time
            )

            if conflicting_events.exists():
                continue  

            available_assistants.append(assistant)

        serializer = ProfileCentralUserSerializer(available_assistants, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)