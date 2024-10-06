from rest_framework import serializers
from user_profile.models import ProfileCentralUser

class ProfileCentralUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = ProfileCentralUser
        fields = ['name', 'surname', 'email']