import re
from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from django_tenants.utils import tenant_context

from institution.models import Institution, Domain, UserInstitution, CentralUser
from user_profile.models import ProfileCentralUser
from branch.models import Branch
from institution.serializers import InstitutionSerializer
from rest_framework.test import APIClient, APITestCase


class InstitutionTestCase(TestCase):

    def test_create_institution_ok(self):
        payload = {
            "name": "Nowa Instytucja 123",
            "owner_email": "test@example.com",
            "owner_password": "test1234",
            "owner_name": "Jan",
            "owner_surname": "Kowalski",
            "owner_phone_number": "+48123456789",
            "address": "Adres testowy",
            "vat": "PL1234567890"
        }

        serializer = InstitutionSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        institution = serializer.save()

        # Sprawdź Instytucję
        self.assertIsNotNone(institution.pk)
        self.assertEqual(institution.name, payload["name"])
        
        # Sprawdź wygenerowany schema_name
        expected_schema_name = re.sub(r'[^a-z0-9_]', '', payload["name"].lower().replace(' ', '_'))
        if not re.match(r'^[a-z_]', expected_schema_name):
            expected_schema_name = 'a_' + expected_schema_name
        self.assertEqual(institution.schema_name, expected_schema_name)

        # Domain (z sygnału post_save)
        domain_qs = Domain.objects.filter(tenant=institution)
        self.assertEqual(domain_qs.count(), 1)
        domain = domain_qs.first()
        sanitized_schema_name = expected_schema_name.replace('_', '-')
        self.assertEqual(domain.domain, f"{sanitized_schema_name}.localhost")

        # UserInstitution
        ui_qs = UserInstitution.objects.filter(user__email=payload["owner_email"], institution=institution)
        self.assertEqual(ui_qs.count(), 1)

        # CentralUser
        central_user = CentralUser.objects.get(email=payload["owner_email"])
        self.assertTrue(central_user.check_password(payload["owner_password"]))

        # ProfileCentralUser + Branch w schemacie tenantowym
        with tenant_context(institution):
            profile_qs = ProfileCentralUser.objects.filter(user__email=payload["owner_email"])
            self.assertEqual(profile_qs.count(), 1)
            profile = profile_qs.first()
            self.assertEqual(profile.name, payload["owner_name"])
            self.assertEqual(profile.surname, payload["owner_surname"])
            self.assertEqual(profile.phone_number, payload["owner_phone_number"])
            self.assertEqual(profile.role, 'admin')
            self.assertTrue(profile.is_admin)

            branch_qs = Branch.objects.filter(name=institution.name)
            self.assertEqual(branch_qs.count(), 1)
            branch = branch_qs.first()
            self.assertTrue(branch.is_mother)
            self.assertEqual(branch.owner, profile)
            self.assertEqual(profile.branch, branch)

    def test_create_institution_existing_user(self):
        """
        Scenariusz, gdy user już istnieje w bazie (CentralUser),
        ale tworzymy nową instytucję z tym samym mailem.
        """
        existing_user = CentralUser.objects.create_user(
            email="existing@example.com",
            password="existing_pass",
        )

        payload = {
            "name": "Instytucja Dla Istniejącego Użytkownika",
            "owner_email": existing_user.email,
            # brak owner_password, bo user już istnieje
            "owner_name": "Ewa",
            "owner_surname": "Kowal",
            "owner_phone_number": "+48123456789",
            "address": "Adres istniejący",
            "vat": "PL5555555555"
        }

        serializer = InstitutionSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        institution = serializer.save()

        # Upewniamy się, że hasło pozostało niezmienione
        updated_user = CentralUser.objects.get(email="existing@example.com")
        self.assertTrue(updated_user.check_password("existing_pass"))

        # Sprawdź relację UserInstitution
        ui_qs = UserInstitution.objects.filter(user=existing_user, institution=institution)
        self.assertEqual(ui_qs.count(), 1)

        # Druga próba z tym samym mailem (tworzy inną instytucję, ale nie duplikuje relacji)
        serializer2 = InstitutionSerializer(data=payload)
        self.assertTrue(serializer2.is_valid(), serializer2.errors)
        institution2 = serializer2.save()
        self.assertNotEqual(institution.pk, institution2.pk)

        ui_qs2 = UserInstitution.objects.filter(user=existing_user, institution=institution2)
        self.assertEqual(ui_qs2.count(), 1)

    def test_institution_schema_name_validation(self):
        """
        Test sprawdza, czy clean() w modelu Institution wywołuje ValidationError 
        przy nieprawidłowej nazwie schema_name.
        """
        invalid_schema = "123#_start!"
        institution = Institution(name="Zła nazwa", schema_name=invalid_schema)
        with self.assertRaises(ValidationError):
            institution.clean()

    def test_institution_duplicate_userinstitution_raises(self):
        """
        Sprawdza unikalność (unique_together) w UserInstitution.
        """
        user = CentralUser.objects.create_user(email="duplicate@example.com", password="somepass")
        institution = Institution.objects.create(name="Duplikat test")

        UserInstitution.objects.create(user=user, institution=institution)
        with self.assertRaises(IntegrityError):
            UserInstitution.objects.create(user=user, institution=institution)
    
    def test_institution_name_starting_with_digit(self):
        payload = {
            "name": "123 firma",
            "owner_email": "digit@example.com",
            "owner_password": "test123",
            "owner_name": "Digit",
            "owner_surname": "User",
            "owner_phone_number": "+48123456789",
        }
        serializer = InstitutionSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        institution = serializer.save()
        
        self.assertEqual(institution.schema_name, "a_123_firma")


class InstitutionAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_institution_endpoint(self):
        payload = {
            "name": "Endpoint Instytucja",
            "owner_email": "endpoint@example.com",
            "owner_password": "test1234",
            "owner_name": "Adam",
            "owner_surname": "Testowy",
            "owner_phone_number": "+48123123123",
            "address": "Test Address",
            "vat": "PL1234567890"
        }
        response = self.client.post('/institution/institution/', data=payload, format='json')
        self.assertEqual(response.status_code, 201)
        
        self.assertTrue(Institution.objects.filter(name="Endpoint Instytucja").exists())
        self.assertTrue(CentralUser.objects.filter(email="endpoint@example.com").exists())

