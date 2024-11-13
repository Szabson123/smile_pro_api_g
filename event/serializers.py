from rest_framework import serializers

from .models import Event, Absence, Office, VisitType, Tags
from .utlis import is_doctor_available, is_assistant_available, is_office_available, is_patient_available
from user_profile.models import EmployeeSchedule, ProfileCentralUser
from patients.models import Patient
from django.db.models import Max
from datetime import timedelta


class EventSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(write_only=True, required=True)
    office_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    assistant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    patient_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    doctor = serializers.IntegerField(source='doctor.id', read_only=True)
    office = serializers.IntegerField(source='office.id', read_only=True)
    assistant = serializers.IntegerField(source='assistant.id', read_only=True)
    patient = serializers.IntegerField(source='patient.id', read_only=True)

    is_rep = serializers.BooleanField(write_only=True, default=False)
    rep_id = serializers.IntegerField(read_only=True)
    end_date = serializers.DateField(write_only=True, required=False)
    interval_days = serializers.IntegerField(write_only=True, required=False)

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Event
        fields = [
            'id', 'doctor_id', 'office_id', 'assistant_id', 'patient_id',
            'doctor', 'office', 'assistant', 'patient', 'date', 'start_time',
            'end_time', 'cost', 'visit_type', 'tags', 'description',
            'is_rep', 'rep_id', 'end_date', 'interval_days'
        ]
        read_only_fields = ['id', 'rep_id']

    def validate(self, data):
        doctor_id = data.get('doctor_id')
        office_id = data.get('office_id')
        assistant_id = data.get('assistant_id')
        patient_id = data.get('patient_id')
        date = data.get('date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        is_rep = data.get('is_rep', False)

        try:
            doctor = ProfileCentralUser.objects.get(id=doctor_id, role='doctor')
        except ProfileCentralUser.DoesNotExist:
            raise serializers.ValidationError({"doctor_id": "Wybrany lekarz nie istnieje lub nie ma roli 'doctor'."})

        office = None
        if office_id is not None:
            try:
                office = Office.objects.get(id=office_id)
            except Office.DoesNotExist:
                raise serializers.ValidationError({"office_id": "Wybrany gabinet nie istnieje."})

        # Pobranie instancji asystenta
        assistant = None
        if assistant_id is not None:
            try:
                assistant = ProfileCentralUser.objects.get(id=assistant_id, role='assistant')
            except ProfileCentralUser.DoesNotExist:
                raise serializers.ValidationError({"assistant_id": "Wybrany asystent nie istnieje lub nie ma roli 'assistant'."})

        # Pobranie instancji pacjenta
        patient = None
        if patient_id is not None:
            try:
                patient = Patient.objects.get(id=patient_id)
            except Patient.DoesNotExist:
                raise serializers.ValidationError({"patient_id": "Wybrany pacjent nie istnieje."})

        if not all([date, start_time, end_time]):
            raise serializers.ValidationError(
                "Wymagane jest podanie daty, godziny rozpoczęcia i zakończenia."
            )

        if start_time >= end_time:
            raise serializers.ValidationError(
                {"end_time": "Godzina zakończenia musi być po godzinie rozpoczęcia."}
            )

        exclude_event_id = self.instance.id if self.instance else None

        if not is_doctor_available(doctor, date, start_time, end_time, exclude_event_id=exclude_event_id):
            raise serializers.ValidationError("Lekarz nie jest dostępny w podanym czasie.")

        if office and not is_office_available(office, date, start_time, end_time, exclude_event_id=exclude_event_id):
            raise serializers.ValidationError("Gabinet nie jest dostępny w podanym czasie.")

        if assistant and not is_assistant_available(assistant, date, start_time, end_time, exclude_event_id=exclude_event_id):
            raise serializers.ValidationError("Asystent nie jest dostępny w podanym czasie.")

        if patient and not is_patient_available(patient, date, start_time, end_time, exclude_event_id=exclude_event_id):
            raise serializers.ValidationError("Pacjent nie jest dostępny w podanym czasie.")

        # Dodanie instancji do danych
        data['doctor'] = doctor
        data['office'] = office
        data['assistant'] = assistant
        data['patient'] = patient

        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        is_rep = validated_data.pop('is_rep', False)
        rep_id = None

        if is_rep:
            last_rep = Event.objects.aggregate(max_rep=Max('rep_id'))['max_rep'] or 0
            rep_id = last_rep + 1

            date = validated_data.get('date', None)
            end_date = validated_data.pop('end_date', None)
            interval_days = validated_data.pop('interval_days', None)

            if not all([date, end_date, interval_days]):
                raise serializers.ValidationError(
                    "Dla powtarzających się wydarzeń wymagane są pola: date (data początkowa), end_date, interval_days."
                )

            event_dates = []
            current_date = date
            while current_date <= end_date:
                event_dates.append(current_date)
                current_date += timedelta(days=interval_days)

            created_events = []
            for event_date in event_dates:
                event_data = validated_data.copy()
                event_data['date'] = event_date
                event_data['rep_id'] = rep_id
                event_data['is_rep'] = True

                event = Event.objects.create(**event_data)
                created_events.append(event)
                if tags:
                    event.tags.set(tags)
                created_events.append(event)

            return created_events
        else:
            event = Event.objects.create(**validated_data)
            if tags:
                event.tags.set(tags)
            return event

class AbsenceSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = Absence
        fields = ['id', 'profile', 'start_date', 'end_date', 'type', 'reason']

    def get_profile(self, obj):
        return obj.profile.id 


class EmployeeScheduleSerializer(serializers.ModelSerializer):
    doctor_id = serializers.CharField(source='doctor')
    class Meta:
        model = EmployeeSchedule
        fields = ['doctor_id', 'day_num', 'start_time', 'end_time']


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ['id', 'name']


class VisitTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitType
        fields = ['id', 'name', 'cost']


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ['id', 'name', 'icon', 'color']


# addition optimalization

class EventCalendarSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    office_name = serializers.CharField(source='office.name', allow_null=True)
    visit_type_name = serializers.CharField(source='visit_type.name', allow_null=True)

    class Meta:
        model = Event
        fields = ['id', 'doctor_name', 'office_name', 'start_time', 'end_time', 'date', 'visit_type_name']

    def get_doctor_name(self, obj):
        if obj.doctor:
            name = obj.doctor.name or ""
            surname = obj.doctor.surname or ""
            full_name = f"{name} {surname}".strip()
            return full_name if full_name else "Nieznany lekarz"
        return "Nieznany lekarz"
    

class TimeSlotRequestSerializer(serializers.Serializer):
    doctor_id = serializers.IntegerField()
    office_id = serializers.IntegerField(required=False, allow_null=True)
    interval = serializers.IntegerField(min_value=1)
    start_date = serializers.DateField()
    end_date = serializers.DateField()


class TimeSlotSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    status = serializers.CharField()
    occupied_by = serializers.CharField(allow_null=True, required=False)