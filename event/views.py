from drf_spectacular.utils import extend_schema, OpenApiParameter
from collections import defaultdict
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, mixins
from intervaltree import IntervalTree

import datetime as dt
from django.db.models import Q

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

from .models import Event, Office, Absence, VisitType, Tags, PlanChange
from .serializers import EventSerializer, EmployeeScheduleSerializer, AbsenceSerializer, OfficeSerializer, VisitTypeSerializer, TagsSerializer, EventCalendarSerializer, TimeSlotRequestSerializer, TimeSlotSerializer
from .filters import EventFilter
from .utlis import *
from .renderers import ORJSONRenderer

from user_profile.models import ProfileCentralUser, EmployeeSchedule
from user_profile.permissions import IsOwnerOfInstitution, HasProfilePermission
from datetime import timedelta, datetime

from user_profile.serializers import ProfileCentralUserSerializer
from user_profile.utils import generate_daily_time_slots, mark_occupied_slots


class EventViewSet(mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = Event.objects.select_related('doctor', 'office', 'assistant', 'patient').all()
    serializer_class = EventSerializer
    permission_classes = [HasProfilePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EventFilter


class EventCalendarViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet do wyświetlania listy eventów w kalendarzu.
    """
    queryset = Event.objects.select_related('doctor', 'office').all()
    serializer_class = EventCalendarSerializer
    permission_classes = [HasProfilePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EventFilter


class TimeSlotView(APIView):
    permission_classes = [IsAuthenticated, HasProfilePermission]
    parser_classes = [JSONParser]
    renderer_classes = [ORJSONRenderer]

    def post(self, request):
        serializer = TimeSlotRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        doctor_id = validated_data['doctor_id']
        office_id = validated_data.get('office_id')
        interval_minutes = validated_data['interval']
        start_date = validated_data['start_date']
        end_date = validated_data['end_date']

        if start_date > end_date:
            return Response({'error': 'Data początkowa musi być wcześniejsza lub równa dacie końcowej.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            doctor = ProfileCentralUser.objects.get(id=doctor_id)
        except ProfileCentralUser.DoesNotExist:
            return Response({'error': 'Nie znaleziono lekarza.'}, status=status.HTTP_404_NOT_FOUND)

        if doctor.role != 'doctor':
            return Response({'error': 'Sloty czasowe mogą być generowane tylko dla lekarzy.'}, status=status.HTTP_400_BAD_REQUEST)

        office = None
        if office_id:
            try:
                office = Office.objects.get(id=office_id)
            except Office.DoesNotExist:
                return Response({'error': 'Nie znaleziono gabinetu.'}, status=status.HTTP_404_NOT_FOUND)

        # Generate time slots
        slots = get_time_slots_for_date_range(doctor, start_date, end_date, interval_minutes, office)
        serialized_slots = TimeSlotSerializer(slots, many=True)
        return Response(serialized_slots.data, status=status.HTTP_200_OK)


def get_time_slots_for_date_range(doctor, start_date, end_date, interval_minutes, office):
    if doctor.role != 'doctor':
        return []

    slots = []
    delta = timedelta(days=1)
    date_range = (start_date, end_date)

    # Convert interval to minutes
    interval_duration = interval_minutes

    # Fetch doctor's appointments (they don't overlap)
    doctor_appointments = Event.objects.filter(
        doctor=doctor,
        date__range=date_range
    ).values('date', 'start_time', 'end_time')

    # Fetch other appointments in the office if office is provided
    if office:
        other_appointments = Event.objects.filter(
            date__range=date_range,
            office=office
        ).exclude(doctor=doctor).values('date', 'start_time', 'end_time')
    else:
        other_appointments = []

    # Group doctor's appointments by date (no need to merge)
    doctor_busy_intervals_by_date = defaultdict(list)
    for appt in doctor_appointments:
        doctor_busy_intervals_by_date[appt['date']].append((
            time_to_minutes(appt['start_time']),
            time_to_minutes(appt['end_time'])
        ))

    # Group and merge other appointments by date
    other_busy_intervals_by_date = defaultdict(list)
    for appt in other_appointments:
        other_busy_intervals_by_date[appt['date']].append((
            time_to_minutes(appt['start_time']),
            time_to_minutes(appt['end_time'])
        ))

    for date in other_busy_intervals_by_date:
        intervals = sorted(other_busy_intervals_by_date[date])
        merged_intervals = merge_intervals(intervals)
        other_busy_intervals_by_date[date] = merged_intervals

    # Fetch plan changes and schedules
    plan_changes = PlanChange.objects.filter(
        doctor=doctor,
        date__range=date_range
    ).values('date', 'start_time', 'end_time')
    plan_changes_by_date = {pc['date']: (
        time_to_minutes(pc['start_time']),
        time_to_minutes(pc['end_time'])
    ) for pc in plan_changes}

    schedules = EmployeeSchedule.objects.filter(
        employee=doctor
    ).values('day_num', 'start_time', 'end_time')
    schedules_by_day = {s['day_num']: (
        time_to_minutes(s['start_time']),
        time_to_minutes(s['end_time'])
    ) for s in schedules}

    current_date = start_date
    while current_date <= end_date:
        if current_date in plan_changes_by_date:
            working_hours = [plan_changes_by_date[current_date]]
        else:
            day_num = current_date.weekday()
            schedule = schedules_by_day.get(day_num)
            if schedule:
                working_hours = [schedule]
            else:
                current_date += delta
                continue

        # Get busy intervals for the current date
        doctor_busy_intervals = doctor_busy_intervals_by_date.get(current_date, [])
        other_busy_intervals = other_busy_intervals_by_date.get(current_date, [])

        # Since doctor's appointments don't overlap, no need to merge doctor's busy intervals
        # Combine busy intervals (doctor's and other's appointments)
        combined_busy_intervals = doctor_busy_intervals + other_busy_intervals
        if other_busy_intervals:
            combined_busy_intervals = merge_intervals(combined_busy_intervals)

        # Subtract busy intervals from working hours to get free intervals
        free_intervals = subtract_intervals(working_hours, combined_busy_intervals)

        # Generate slots from free intervals
        slots.extend(generate_slots(free_intervals, current_date, interval_duration))

        current_date += delta

    return slots

def time_to_minutes(t):
    return t.hour * 60 + t.minute

def minutes_to_time(m):
    return dt.time(m // 60, m % 60)

def merge_intervals(intervals):
    if not intervals:
        return []
    intervals.sort()
    merged = [intervals[0]]
    for current in intervals[1:]:
        last_start, last_end = merged[-1]
        current_start, current_end = current
        if current_start <= last_end:
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append(current)
    return merged

def subtract_intervals(working_hours, busy_intervals):
    tree = IntervalTree()
    for start, end in working_hours:
        tree[start:end] = 'free'
    for start, end in busy_intervals:
        tree.chop(start, end)
    free_intervals = [(iv.begin, iv.end) for iv in sorted(tree)]
    return free_intervals

def generate_slots(free_intervals, current_date, interval_minutes):
    slots = []
    for start_min, end_min in free_intervals:
        num_slots = (end_min - start_min) // interval_minutes
        for i in range(num_slots):
            slot_start_min = start_min + i * interval_minutes
            slot_end_min = slot_start_min + interval_minutes
            slot_start = datetime.combine(current_date, minutes_to_time(slot_start_min))
            slot_end = datetime.combine(current_date, minutes_to_time(slot_end_min))
            slots.append({
                'start': slot_start,
                'end': slot_end,
                'status': 'wolny',
                'occupied_by': None,
            })
    return slots

def subtract_intervals(working_hours, busy_intervals):
    # Subtract busy intervals from working hours to get free intervals
    free_intervals = []
    for work_start, work_end in working_hours:
        temp_intervals = [(work_start, work_end)]
        for busy_start, busy_end in busy_intervals:
            new_intervals = []
            for interval_start, interval_end in temp_intervals:
                # No overlap
                if busy_end <= interval_start or busy_start >= interval_end:
                    new_intervals.append((interval_start, interval_end))
                else:
                    # Overlap exists
                    if interval_start < busy_start:
                        new_intervals.append((interval_start, busy_start))
                    if busy_end < interval_end:
                        new_intervals.append((busy_end, interval_end))
            temp_intervals = new_intervals
        free_intervals.extend(temp_intervals)
    return free_intervals




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

    @extend_schema(
        description="Sprawdza dostępnych asystentów w danym przedziale czasowym.",
        parameters=[
            OpenApiParameter("date", type=str, description="Data w formacie YYYY-MM-DD."),
            OpenApiParameter("start_time", type=str, description="Godzina początkowa w formacie HH:MM."),
            OpenApiParameter("end_time", type=str, description="Godzina końcowa w formacie HH:MM."),
        ],
        responses={200: "Lista dostępnych asystentów"}
    )
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
                assistant=assistant,
                date=date,
                start_time__lt=end_time,
                end_time__gt=start_time
            )

            if conflicting_events.exists():
                continue  

            available_assistants.append(assistant)

        serializer = ProfileCentralUserSerializer(available_assistants, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class AvailabilityCheckView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]


    @extend_schema(
        description="Sprawdza dostępność zasobów w zadanym przedziale czasowym.",
        parameters=[
            OpenApiParameter("start_date", type=str, description="Data początkowa w formacie YYYY-MM-DD."),
            OpenApiParameter("end_date", type=str, description="Data końcowa w formacie YYYY-MM-DD."),
            OpenApiParameter("interval_days", type=int, description="Interwał dni pomiędzy sprawdzeniami dostępności."),
            OpenApiParameter("start_time", type=str, description="Godzina początkowa w formacie HH:MM."),
            OpenApiParameter("end_time", type=str, description="Godzina końcowa w formacie HH:MM."),
            OpenApiParameter("doctor_id", type=int, description="ID lekarza", required=False),
            OpenApiParameter("assistant_id", type=int, description="ID asystenta", required=False),
            OpenApiParameter("office_id", type=int, description="ID gabinetu", required=False),
        ],
        responses={200: "Lista dostępności zasobów"}
    )
    def post(self, request):
        data = request.data
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        interval_days = data.get('interval_days')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        doctor_id = data.get('doctor_id')
        assistant_id = data.get('assistant_id')
        office_id = data.get('office_id')

        if not all([start_date_str, end_date_str, interval_days, start_time_str, end_time_str]):
            return Response({'error': 'Brak wymaganych parametrów.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if start_date > end_date:
                return Response({'error': 'Data początkowa musi być wcześniejsza niż data końcowa.'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'Nieprawidłowy format daty. Użyj YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            interval_days = int(interval_days)
            if interval_days <= 0:
                raise ValueError
        except ValueError:
            return Response({'error': 'Nieprawidłowa wartość interwału. Musi być liczbą całkowitą większą od zera.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            if start_time >= end_time:
                return Response({'error': 'Godzina rozpoczęcia musi być wcześniejsza niż godzina zakończenia.'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'Nieprawidłowy format godziny. Użyj HH:MM.'}, status=status.HTTP_400_BAD_REQUEST)

        doctor = None
        if doctor_id:
            try:
                doctor = ProfileCentralUser.objects.get(id=doctor_id, role='doctor')
            except ProfileCentralUser.DoesNotExist:
                return Response({'error': 'Nie znaleziono lekarza o podanym ID.'}, status=status.HTTP_404_NOT_FOUND)

        assistant = None
        if assistant_id:
            try:
                assistant = ProfileCentralUser.objects.get(id=assistant_id, role='assistant')
            except ProfileCentralUser.DoesNotExist:
                return Response({'error': 'Nie znaleziono asystenta o podanym ID.'}, status=status.HTTP_404_NOT_FOUND)

        office = None
        if office_id:
            try:
                office = Office.objects.get(id=office_id)
            except Office.DoesNotExist:
                return Response({'error': 'Nie znaleziono gabinetu o podanym ID.'}, status=status.HTTP_404_NOT_FOUND)

        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=interval_days)

        availability_list = []
        for date in dates:
            conflicts = []

            if doctor and not is_doctor_available(doctor, date, start_time, end_time):
                conflicts.append('Lekarz niedostępny')

            if assistant and not is_assistant_available(assistant, date, start_time, end_time):
                conflicts.append('Asystent niedostępny')

            if office and not is_office_available(office, date, start_time, end_time):
                conflicts.append('Gabinet zajęty')

            availability_list.append({
                'date': date,
                'start_time': start_time,
                'end_time': end_time,
                'available': not conflicts,
                'conflicts': conflicts
            })

        return Response(availability_list, status=status.HTTP_200_OK)