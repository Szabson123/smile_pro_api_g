from rest_framework import serializers

from .models import Event, Absence, Office, VisitType, Tags
from .validators import validate_doctor_id, validate_office_id, validate_assistant_id, validate_patient_id, validate_dates, validate_times, is_doctor_available, is_office_available, is_assistant_available, is_patient_available

from user_profile.models import EmployeeSchedule, ProfileCentralUser
from patients.models import Patient
from django.db.models import Max
from datetime import timedelta
from branch.models import Branch

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

    tags = serializers.PrimaryKeyRelatedField(queryset=Tags.objects.all(), many=True, required=False)

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

        doctor = validate_doctor_id(doctor_id)
        office = validate_office_id(office_id)
        assistant = validate_assistant_id(assistant_id)
        patient = validate_patient_id(patient_id)

        validate_dates(date, data.get('end_date'))
        validate_times(start_time, end_time)

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

            date = validated_data.get('date')
            end_date = validated_data.pop('end_date', None)
            interval_days = validated_data.pop('interval_days', None)

            if not all([date, end_date, interval_days]):
                raise serializers.ValidationError(
                    "For recurring events, 'date', 'end_date', and 'interval_days' are required."
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
    profile_id = serializers.PrimaryKeyRelatedField(read_only=True, source='profile')

    class Meta:
        model = Absence
        fields = ['id', 'profile_id', 'start_date', 'end_date', 'type', 'reason']

    def create(self, validated_data):
        request = self.context['request']
        branch_uuid = self.context['view'].kwargs.get('branch_uuid')
        branch = Branch.objects.get(identyficator=branch_uuid)

        try:
            profile = ProfileCentralUser.objects.get(user=request.user, branch=branch)
        except ProfileCentralUser.DoesNotExist:
            raise serializers.ValidationError("Nie masz profilu w tym branchu.")

        validated_data['branch'] = branch
        validated_data['profile'] = profile

        return super().create(validated_data)
    


class DoctorScheduleSerializer(serializers.ModelSerializer):
    doctor_id = serializers.PrimaryKeyRelatedField(read_only=True, source='employee')

    class Meta:
        model = EmployeeSchedule
        fields = ['id', 'doctor_id', 'day_num', 'start_time', 'end_time']

    def create(self, validated_data):
        request = self.context['request']
        branch_uuid = self.context['view'].kwargs.get('branch_uuid')
        branch = Branch.objects.get(identyficator=branch_uuid)

        try:
            profile = ProfileCentralUser.objects.get(user=request.user, branch=branch)
        except ProfileCentralUser.DoesNotExist:
            raise serializers.ValidationError("Nie masz profilu w tym branchu.")

        validated_data['branch'] = branch
        validated_data['employee'] = profile

        return super().create(validated_data)


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

    def validate_doctor_id(self, value):
        return validate_doctor_id(value)

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        validate_dates(start_date, end_date)
        
        return attrs


class TimeSlotSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    status = serializers.CharField()
    occupied_by = serializers.CharField(allow_null=True, required=False)