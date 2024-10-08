from rest_framework import serializers

from .models import Event

class EventSerializer(serializers.ModelSerializer):
    profile = serializers.ReadOnlyField(source='profile.name')
    class Meta:
        model = Event
        fields = ['id', 'name', 'profile']
        read_only_fields = ['profile']