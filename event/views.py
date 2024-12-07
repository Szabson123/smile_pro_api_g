from drf_spectacular.utils import extend_schema, OpenApiParameter
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, status, mixins, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ValidationError

from .models import Event, Office, Absence, VisitType, Tags, PlanChange
from .serializers import EventSerializer, DoctorScheduleSerializer, AbsenceSerializer, OfficeSerializer, VisitTypeSerializer, TagsSerializer, EventCalendarSerializer, TimeSlotRequestSerializer, TimeSlotSerializer
from .filters import EventFilter
from .utlis import *
from .renderers import ORJSONRenderer
from .validators import validate_assistant_id, is_assistant_available, validate_doctor_id, is_doctor_available, is_office_available, validate_office_id, is_patient_available, validate_dates, validate_times

from user_profile.models import ProfileCentralUser, EmployeeSchedule
from user_profile.permissions import IsOwnerOfInstitution, HasProfilePermission
from user_profile.serializers import ProfileCentralUserSerializer
from user_profile.utils import generate_daily_time_slots, mark_occupied_slots
from branch.models import Branch

from datetime import timedelta, datetime

class EventViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Event.objects.select_related('doctor', 'office', 'assistant', 'patient').all()
    serializer_class = EventSerializer
    permission_classes = [HasProfilePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EventFilter

    def create(self, request, *args, **kwargs):
        is_many = isinstance(request.data, list)

        serializer = self.get_serializer(data=request.data, many=is_many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class EventCalendarViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet do wyświetlania listy eventów w kalendarzu.
    """
    queryset = Event.objects.select_related('doctor', 'office').all()
    serializer_class = EventCalendarSerializer
    permission_classes = [HasProfilePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EventFilter


class AbsenceViewSet(viewsets.ModelViewSet):
    serializer_class = AbsenceSerializer
    permission_classes = [HasProfilePermission]
    filterset_fields = ['profile']

    def get_queryset(self):
        branch_uuid = self.kwargs.get('branch_uuid')
        return Absence.objects.filter(branch__identyficator=branch_uuid)
        

class DoctorScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = DoctorScheduleSerializer
    permission_classes = [IsAuthenticated, HasProfilePermission]

    def get_queryset(self):
        branch_uuid = self.kwargs.get('branch_uuid')
        return EmployeeSchedule.objects.filter(branch__identyficator=branch_uuid)


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

    def get_queryset(self):
        branch_uuid = self.kwargs.get('branch_uuid')
        return VisitType.objects.filter(branch__identyficator=branch_uuid)

    def perform_create(self, serializer):
        branch_uuid = self.kwargs.get('branch_uuid')
        branch = Branch.objects.get(identyficator=branch_uuid)
        serializer.save(branch=branch)


class TimeSlotView(APIView):
    permission_classes = [IsAuthenticated, HasProfilePermission]
    parser_classes = [JSONParser]
    renderer_classes = [ORJSONRenderer]

    @extend_schema(
        description="Generuje dostępne sloty czasowe dla lekarza w zadanym przedziale czasowym.",
        request=TimeSlotRequestSerializer,
        responses={200: TimeSlotSerializer(many=True)}
    )
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

        office = None
        if office_id:
            try:
                office = Office.objects.get(id=office_id)
            except Office.DoesNotExist:
                return Response({'error': 'Nie znaleziono gabinetu.'}, status=status.HTTP_404_NOT_FOUND)

        slots = get_time_slots_for_date_range(doctor_id, start_date, end_date, interval_minutes, office)
        serialized_slots = TimeSlotSerializer(slots, many=True)
        return Response(serialized_slots.data, status=status.HTTP_200_OK)
    

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
            validate_dates(date_str, date_str) 
            validate_times(start_time_str, end_time_str)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        assistants = ProfileCentralUser.objects.filter(role='assistant')

        available_assistants = []

        for assistant in assistants:
            day_num = date_str.weekday()
            
            try:
                schedule = EmployeeSchedule.objects.get(employee=assistant, day_num=day_num)
            except EmployeeSchedule.DoesNotExist:
                continue

            if start_time_str < schedule.start_time or end_time_str > schedule.end_time:
                continue

            conflicting_events = Event.objects.filter(
                assistant=assistant,
                date=date_str,
                start_time__lt=end_time_str,
                end_time__gt=start_time_str
            )
            if conflicting_events.exists():
                continue
            
            available_assistants.append(assistant)
            
        serializer = ProfileCentralUserSerializer(available_assistants, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CheckRepetitionEvents(APIView):
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
            validate_dates(start_date, end_date)
        except ValueError:
            return Response({'error': 'Nieprawidłowy format daty. Użyj YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            interval_days = int(interval_days)
            if interval_days <= 0:
                raise ValueError
        except ValueError:
            return Response({'error': 'Nieprawidłowa wartość interwału. Musi być liczbą całkowitą większą od zera.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            validate_times(start_time, end_time)
        except ValueError:
            return Response({'error': 'Nieprawidłowy format godziny. Użyj HH:MM.'}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        doctor = None
        if doctor_id:
            try:
                doctor = validate_doctor_id(doctor_id)
            except ValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        assistant = None
        if assistant_id:
            try:
                assistant = validate_assistant_id(assistant_id)
            except ValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        office = None
        if office_id:
            try:
                office = validate_office_id(office_id)
            except ValidationError as e:
                return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

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