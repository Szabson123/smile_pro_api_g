from rest_framework import serializers

from .models import Event, Absence, Office, VisitType, Tags
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
    patient = serializers.IntegerField(source='patient.id', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'doctor_id', 'office_id', 'patient_id',
            'doctor', 'office', 'patient', 'date', 'start_time',
            'end_time', 'cost', 'visit_type', 'tags', 'description'
        ]
        read_only_fields = ['id'] 

    def validate(self, data):
        doctor = data.get('doctor')
        office = data.get('office')
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

        if not self.is_doctor_available(doctor, date, start_time, end_time):
            raise serializers.ValidationError("Lekarz nie jest dostępny w podanym czasie.")

        if office:
            if not self.is_office_available(office, date, start_time, end_time):
                raise serializers.ValidationError("Gabinet nie jest dostępny w podanym czasie.")

        if patient:
            if not self.is_patient_available(patient, date, start_time, end_time):
                raise serializers.ValidationError("Pacjent nie jest dostępny w podanym czasie.")

        return data

    def is_doctor_available(self, doctor, date, start_time, end_time):
        day_num = date.weekday()
        try:
            schedule = EmployeeSchedule.objects.get(employee=doctor, day_num=day_num)
        except EmployeeSchedule.DoesNotExist:
            return False  # Lekarz nie pracuje w tym dniu

        if start_time < schedule.start_time or end_time > schedule.end_time:
            return False

        conflicting_events = Event.objects.filter(
            doctor=doctor,
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time
        )

        if self.instance:
            conflicting_events = conflicting_events.exclude(id=self.instance.id)

        if conflicting_events.exists():
            return False

        return True

    def is_office_available(self, office, date, start_time, end_time):
        conflicting_events = Event.objects.filter(
            office=office,
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time
            
        )

        if self.instance:
            conflicting_events = conflicting_events.exclude(id=self.instance.id)

        if conflicting_events.exists():
            return False

        return True

    def is_patient_available(self, patient, date, start_time, end_time):
        conflicting_events = Event.objects.filter(
            patient=patient,
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time
        )

        if self.instance:
            conflicting_events = conflicting_events.exclude(id=self.instance.id)

        if conflicting_events.exists():
            return False

        return True
        

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