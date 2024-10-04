from rest_framework import serializers
from .models import Institution
from custom_user.models import CentralUser

class InstitutionSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(write_only=True)
    owner_password = serializers.CharField(write_only=True)

    class Meta:
        model = Institution
        fields = ['name', 'owner_email', 'owner_password']

    def create(self, validated_data):
        owner_email = validated_data.pop('owner_email')
        owner_password = validated_data.pop('owner_password')

        # Utwórz CentralUser
        central_user = CentralUser.objects.create_user(email=owner_email, password=owner_password)

        # Utwórz Instytucję i przypisz owner_user
        institution = Institution.objects.create(**validated_data)
        institution.owner_user = central_user
        institution.save()

        return institution
