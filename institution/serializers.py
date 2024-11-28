from rest_framework import serializers
from .models import Institution, UserInstitution
from custom_user.models import CentralUser
from django_tenants.utils import tenant_context
from user_profile.models import ProfileCentralUser
from branch.models import Branch
from django.db import transaction

class InstitutionSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(write_only=True)
    owner_password = serializers.CharField(write_only=True)
    owner_name = serializers.CharField(write_only=True)
    owner_surname = serializers.CharField(write_only=True)
    owner_phone_number = serializers.CharField(write_only=True)

    class Meta:
        model = Institution
        fields = ['name', 'owner_email', 'owner_password', 'owner_name', 'owner_surname', 'owner_phone_number', 'address', 'vat']
        
    @transaction.atomic
    def create(self, validated_data):
        owner_email = validated_data.pop('owner_email')
        owner_password = validated_data.pop('owner_password')
        owner_name = validated_data.pop('owner_name')
        owner_surname = validated_data.pop('owner_surname')
        owner_phone_number = validated_data.pop('owner_phone_number')

        central_user = CentralUser.objects.create_user(email=owner_email, password=owner_password)
        institution = Institution.objects.create(owner_user=central_user, **validated_data)

        # Create ProfileCentralUser within the tenant schema
        
        with tenant_context(institution):
            ProfileCentralUser.objects.create(
                user=central_user,
                owner=True,
                name=owner_name,
                surname=owner_surname,
                phone_number=owner_phone_number
            )
            Branch.objects.create(
                name=institution.name,
                is_mother=True                
            )

        return institution