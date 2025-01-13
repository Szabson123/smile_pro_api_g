from rest_framework import serializers

from .models import Event, Absence, Office, VisitType, Tags, EventStatus
from .validators import validate_doctor_id, validate_office_id, validate_assistant_id, validate_patient_id, validate_dates, validate_times, is_doctor_available, is_office_available, is_assistant_available, is_patient_available, validate_doctor_id_with_id

from user_profile.models import EmployeeSchedule, ProfileCentralUser
from patients.models import Patient
from django.db.models import Max
from datetime import timedelta
from branch.models import Branch
from payment.models import Obligation
from decimal import Decimal
import decimal


class ObligationSerializer(serializers.ModelSerializer):
    ammount = serializers.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        model = Obligation
        fields = ['ammount']


class EventSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(write_only=True, required=True)
    office_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    assistant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    patient_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    doctor = serializers.IntegerField(source='doctor.id', read_only=True)
    office = serializers.IntegerField(source='office.id', read_only=True)
    assistant = serializers.IntegerField(source='assistant.id', read_only=True)
    patient = serializers.IntegerField(source='patient.id', read_only=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tags.objects.all(), many=True, required=False)
    event_status = serializers.CharField(source='event_status.status', read_only=True)
    cost = ObligationSerializer(read_only=True)
    cost_input = serializers.DecimalField(max_digits=8, decimal_places=2, write_only=True, required=True)

    class Meta:
        model = Event
        fields = [
            'id', 'doctor_id', 'office_id', 'assistant_id', 'patient_id',
            'doctor', 'office', 'assistant', 'patient', 'date', 'start_time',
            'end_time', 'cost', 'cost_input', 'visit_type', 'tags', 'description', 'event_status'
        ]
        read_only_fields = ['id', 'rep_id', 'is_rep']
    
    def validate_cost(self, value):
        if not isinstance(value, (float, int, decimal.Decimal)):
            raise serializers.ValidationError("Cost must be a valid decimal number.")
        return value

    def validate(self, data):
        doctor_id = data.get('doctor_id')
        office_id = data.get('office_id')
        assistant_id = data.get('assistant_id')
        patient_id = data.get('patient_id')
        date = data.get('date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        exclude_event_id = self.instance.id if self.instance else None

        doctor = validate_doctor_id(doctor_id)
        office = validate_office_id(office_id)
        assistant = validate_assistant_id(assistant_id)
        patient = validate_patient_id(patient_id)

        validate_times(start_time, end_time)

        if not is_doctor_available(doctor, date, start_time, end_time, exclude_event_id=exclude_event_id):
            raise serializers.ValidationError("Lekarz nie jest dostępny w podanym czasie.")

        if not is_office_available(office, date, start_time, end_time, exclude_event_id=exclude_event_id):
            raise serializers.ValidationError("Gabinet nie jest dostępny w podanym czasie.")

        if not is_assistant_available(assistant, date, start_time, end_time, exclude_event_id=exclude_event_id):
            raise serializers.ValidationError("Asystent nie jest dostępny w podanym czasie.")

        if not is_patient_available(patient, date, start_time, end_time, exclude_event_id=exclude_event_id):
            raise serializers.ValidationError("Pacjent nie jest dostępny w podanym czasie.")

        data['doctor'] = doctor
        data['office'] = office
        data['assistant'] = assistant
        data['patient'] = patient

        return data

    def create(self, validated_data):
        request = self.context['request']
        branch_uuid = self.context['view'].kwargs.get('branch_uuid')
        branch = Branch.objects.get(identyficator=branch_uuid)

        try:
            profile = validated_data['doctor'].user.profile.get(branch=branch)
        except:
            raise serializers.ValidationError("Nie masz profilu lub lekarz nie jest przypisany do tego branchu.")

        validated_data['branch'] = branch

        doctor = validated_data['doctor']
        office = validated_data.get('office')
        assistant = validated_data.get('assistant')
        patient = validated_data.get('patient')

        if doctor.branch != branch:
            raise serializers.ValidationError("Wybrany lekarz nie należy do tego branchu.")
        if office and office.branch != branch:
            raise serializers.ValidationError("Wybrany gabinet nie należy do tego branchu.")
        if assistant and assistant.branch != branch:
            raise serializers.ValidationError("Wybrany asystent nie należy do tego branchu.")
        if patient and patient.branch != branch:
            raise serializers.ValidationError("Wybrany pacjent nie należy do tego branchu.")

        tags = validated_data.pop('tags', [])

        is_rep = bool(self.parent)
        if is_rep:

            if not hasattr(self.parent, '_rep_id'):
                last_rep = Event.objects.aggregate(max_rep=Max('rep_id'))['max_rep'] or 0
                new_rep_id = last_rep + 1
                self.parent._rep_id = new_rep_id
                
            rep_id = self.parent._rep_id
            validated_data['is_rep'] = True
            validated_data['rep_id'] = rep_id
        else:
            validated_data['is_rep'] = False
            validated_data['rep_id'] = 0

        # -----------------------------------
        # Generowanie numeru w EventStatus
        # -----------------------------------

        event_date = validated_data['date']
        max_number_str = (
            EventStatus.objects
            .filter(event__date=event_date)
            .aggregate(m=Max('number'))['m']
        )

        if max_number_str:
            current_max = int(max_number_str)
            new_number_int = current_max + 1 
        else:
            new_number_int = 1

        new_number_str = f"{new_number_int:05d}"

        new_event_status = EventStatus.objects.create(
            number=new_number_str,
            status='planned' 
        )

        validated_data['event_status'] = new_event_status

        cost_value = validated_data.pop('cost_input')
        new_payment = Obligation.objects.create(ammount=cost_value, branch=branch, patient=patient)
        validated_data['cost'] = new_payment

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
    

class EventListSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    event_status = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    patient_surname = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ['id', 'doctor_name', 'patient_name', 'date', 'event_status', 'patient_surname']

    def get_doctor_name(self, obj):
        if obj.doctor:
            name = obj.doctor.name or ""
            surname = obj.doctor.surname or ""
            full_name = f"{name} {surname}".strip()
            return full_name if full_name else "Nieznany lekarz"
        return "Nieznany lekarz"

    def get_event_status(self, obj):
        return obj.event_status.status if obj.event_status else "Unknown status"

    def get_patient_name(self, obj):
        return obj.patient.name if obj.patient else "Unknown patient"

    def get_patient_surname(self, obj):
        return obj.patient.surname if obj.patient else "Unknown surname"
    

class TimeSlotRequestSerializer(serializers.Serializer):
    doctor_id = serializers.IntegerField()
    office_id = serializers.IntegerField(required=False, allow_null=True)
    interval = serializers.IntegerField(min_value=1)
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate_doctor_id_with_id(self, value):
        return validate_doctor_id_with_id(value)

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