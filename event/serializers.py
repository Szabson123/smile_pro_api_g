from rest_framework import serializers

from .models import Event, Absence, Office
from user_profile.models import DoctorSchedule

class EventSerializer(serializers.ModelSerializer):
    doctor_id = serializers.CharField(source='profile')
    office_id = serializers.CharField(source='office')
    class Meta:
        model = Event
        fields = ['id', 'name', 'doctor_id', 'date', 'start_time', 'end_time', 'office_id']
        

class AbsenceSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = Absence
        fields = ['id', 'profile', 'start_date', 'end_date', 'type', 'reason']

    def get_profile(self, obj):
        return obj.profile.id 


class DoctorScheduleSerializer(serializers.ModelSerializer):
    doctor_id = serializers.CharField(source='doctor')
    class Meta:
        model = DoctorSchedule
        fields = ['doctor_id', 'date', 'start_time', 'end_time', 'office']