from rest_framework import serializers

from .models import Event, Absence, Office, VisitType, Tags
from .utlis import is_doctor_available, is_assistant_available, is_office_available, is_patient_available
from user_profile.models import EmployeeSchedule, ProfileCentralUser
from patients.models import Patient


class EventSerializer(serializers.ModelSerializer):
    doctor_id = serializers.PrimaryKeyRelatedField(
        source='doctor',
        queryset=ProfileCentralUser.objects.filter(role='doctor'),
        write_only=True
    )
    office_id = serializers.PrimaryKeyRelatedField(
        source='office',
        queryset=Office.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )
    assistant_id = serializers.PrimaryKeyRelatedField(
        source='assistant',
        queryset=ProfileCentralUser.objects.filter(role='assistant'),
        required=False,
        allow_null=True,
        write_only=True
    )
    patient_id = serializers.PrimaryKeyRelatedField(
        source='patient',
        queryset=Patient.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )
    visit_type = serializers.SlugRelatedField(
        queryset=VisitType.objects.all(),
        slug_field='name',
        required=False,
        allow_null=True
    )
    tags = serializers.SlugRelatedField(
        many=True,
        queryset=Tags.objects.all(),
        slug_field='name',
        required=False
    )
    
    doctor = serializers.IntegerField(source='doctor.id', read_only=True)
    office = serializers.IntegerField(source='office.id', read_only=True)
    assistant = serializers.IntegerField(source='assistant.id', read_only=True)
    patient = serializers.IntegerField(source='patient.id', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'doctor_id', 'office_id', 'assistant_id', 'patient_id',
            'doctor', 'office', 'assistant', 'patient', 'date', 'start_time',
            'end_time', 'cost', 'visit_type', 'tags', 'description'
        ]
        read_only_fields = ['id'] 

    def validate(self, data):
        doctor = data.get('doctor')
        office = data.get('office')
        assistant = data.get('assistant')
        patient = data.get('patient')
        date = data.get('date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if not all([doctor, date, start_time, end_time]):
            raise serializers.ValidationError(
                "Wymagane jest podanie lekarza, daty, godziny rozpoczęcia i zakończenia."
            )

        if doctor.role != 'doctor':
            raise serializers.ValidationError("Wybrany profil nie ma roli 'doctor'.")

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

        return data

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


