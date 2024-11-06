from rest_framework import serializers
from user_profile.models import ProfileCentralUser
from custom_user.models import CentralUser, make_random_password
from institution.models import UserInstitution
from django.db import transaction


class ProfileCentralUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = ProfileCentralUser
        fields = ['name', 'surname', 'email', 'phone_number']


class EmployeeProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)

    class Meta:
        model = ProfileCentralUser
        fields = [
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

        with transaction.atomic():
            central_user, created = CentralUser.objects.get_or_create(email=email)
            if created:
                temp_password = make_random_password()
                central_user.set_password(temp_password)
                central_user.save()
            UserInstitution.objects.get_or_create(user=central_user, institution=institution)

            profile = ProfileCentralUser.objects.create(user=central_user, **validated_data)

        return profile
