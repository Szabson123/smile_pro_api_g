from rest_framework import serializers
from .models import Institution, UserInstitution
from custom_user.models import CentralUser
from django_tenants.utils import tenant_context
from django.db import transaction
from user_profile.models import ProfileCentralUser
from branch.models import Branch

class InstitutionSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(write_only=True)
    owner_password = serializers.CharField(write_only=True, required=False)
    owner_name = serializers.CharField(write_only=True)
    owner_surname = serializers.CharField(write_only=True)
    owner_phone_number = serializers.CharField(write_only=True)

    class Meta:
        model = Institution
        fields = [
            'name',
            'owner_email',
            'owner_password',
            'owner_name',
            'owner_surname',
            'owner_phone_number',
            'address',
            'vat'
        ]
                
    @transaction.atomic
    def create(self, validated_data):
        owner_email = validated_data.pop('owner_email')
        owner_password = validated_data.pop('owner_password', None)
        owner_name = validated_data.pop('owner_name')
        owner_surname = validated_data.pop('owner_surname')
        owner_phone_number = validated_data.pop('owner_phone_number')

        central_user, created = CentralUser.objects.get_or_create(email=owner_email)
        if created:
            central_user.set_password(owner_password)
            central_user.save()
        else:
            pass

        institution = Institution.objects.create(owner_user=central_user, **validated_data)

        UserInstitution.objects.get_or_create(user=central_user, institution=institution)

        with tenant_context(institution):
            profile, profile_created = ProfileCentralUser.objects.get_or_create(
                user=central_user,
                defaults={
                    'name': owner_name,
                    'surname': owner_surname,
                    'phone_number': owner_phone_number,
                    'role': 'admin',
                    'is_admin': True
                }
            )
            if not profile_created:
                profile.name = owner_name
                profile.surname = owner_surname
                profile.phone_number = owner_phone_number
                profile.is_admin = True
                profile.save()

            branch, branch_created = Branch.objects.get_or_create(
                owner=profile,
                is_mother=True,
                defaults={
                    'name': institution.name,
                }
            )

            profile.branch = branch
            profile.save()

        return institution
