from rest_framework import serializers

from .models import Event, Absence
from user_profile.models import DoctorSchedule

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'profile', 'date', 'start_time', 'end_time']
        

class Absence(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField
    class Meta:
        model = Absence
        fields = ['id', 'profile', 'start_date', 'end_date', 'type', 'reason']
        
    # def get_profile(self, obj):


class DoctorScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSchedule
        fields = ['doctor', 'date', 'start_time', 'end_time']