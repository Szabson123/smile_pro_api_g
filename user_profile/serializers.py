from rest_framework import serializers
from user_profile.models import ProfileCentralUser
from custom_user.models import CentralUser, make_random_password
from institution.models import UserInstitution
from django.db import transaction
from django_tenants.utils import tenant_context


class ProfileCentral(serializers.ModelSerializer):

    class Meta:
        model = ProfileCentralUser
        fields = ['id', 'name', 'surname', 'role']


class MeProfileSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = CentralUser
        fields = ['email', 'profile']

    def get_profile(self, obj):
        request = self.context.get('request')
        tenant = getattr(request, 'tenant', None)
        branch_uuid = self.context.get('branch_uuid')

        if tenant and branch_uuid:
            with tenant_context(tenant):
                try:
                    profile = obj.profile.get(branch__identyficator=branch_uuid)
                    return ProfileCentral(profile, context=self.context).data
                except ProfileCentralUser.DoesNotExist:
                    return None
        else:
            return None


class ProfileCentralUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = ProfileCentralUser
        fields = ['id', 'name', 'surname', 'email', 'phone_number', 'role']


class EmployeeProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)

    class Meta:
        model = ProfileCentralUser
        fields = [
            'id',
            'role',
            'email',
            'name',
            'surname',
            'pesel',
            'date_of_birth',
            'sex',
            'street',
            'house_number',
            'local_number',
            'zip_code',
            'city',
            'phone_number',
            'nip',
        ]

    def create(self, validated_data):
        email = validated_data.pop('email')
        institution = self.context['request'].tenant 
        branch = self.context['request'].branch

        with transaction.atomic():
            central_user, created = CentralUser.objects.get_or_create(email=email)
            if created:
                temp_password = make_random_password()
                central_user.set_password(temp_password)
                central_user.save()

            UserInstitution.objects.get_or_create(user=central_user, institution=institution)

            if not ProfileCentralUser.objects.filter(user=central_user, branch=branch).exists():
                profile = ProfileCentralUser.objects.create(user=central_user, **validated_data)
            else:
                raise serializers.ValidationError("Profile for this user already exists in the branch.")

        return profile
