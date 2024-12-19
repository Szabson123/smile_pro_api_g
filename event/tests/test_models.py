import uuid
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from institution.models import CentralUser
from branch.models import Branch
from institution.models import Institution, Domain
from event.models import Tags
from django_tenants.utils import tenant_context
from user_profile.models import ProfileCentralUser
from institution.serializers import InstitutionSerializer
from django.test import TestCase


class TagAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
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
        self.sc_user = CentralUser.objects.create(email="test2@g.com", password='lolek')
        # Tworzymy instytucję (tenant) wraz z Owner Userem, ProfileCentralUser, Branch mother i Domain
        serializer = InstitutionSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.institution = serializer.save()

        # Pobieramy domenę wygenerowaną przez sygnał post_save
        self.domain_obj = Domain.objects.get(tenant=self.institution)

        # Pobieramy użytkownika-owner
        self.owner_user = CentralUser.objects.get(email=payload["owner_email"])
        self.client.force_authenticate(user=self.owner_user)

        # W tenant_context pobieramy branch mother
        with tenant_context(self.institution):
            self.branch = Branch.objects.filter(is_mother=True).first()

        self.branch_uuid = str(self.branch.identyficator)
        self.url = f"/{self.branch_uuid}/events/tags/"

    def test_create_tag_ok(self):
        """
        Użytkownik zalogowany, ma profil w branchu -> 201 CREATED
        """
        payload = {"name": "Test Tag", "icon": "test_icon.png", "color": "#FFFFFF"}
        response = self.client.post(
            self.url,
            data=payload,
            format='json',
            HTTP_HOST=self.domain_obj.domain
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['name'], payload["name"])

        with tenant_context(self.institution):
            created_tag = Tags.objects.get(pk=response.data['id'])
            self.assertEqual(created_tag.name, payload['name'])
            self.assertEqual(created_tag.icon, payload['icon'])
            self.assertEqual(created_tag.color, payload['color'])
            self.assertEqual(created_tag.branch, self.branch)

    # def test_create_tag_unauthenticated(self):
    #     """
    #     Użytkownik niezalogowany -> 401 UNAUTHORIZED
    #     """
    #     self.client.force_authenticate(user=None)

    #     payload = {"name": "Test Tag Unauth", "icon": "icon.png", "color": "#000000"}
    #     response = self.client.post(
    #         self.url,
    #         data=payload,
    #         format='json',
    #         HTTP_HOST=self.domain_obj.domain
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, response.data)
    #     self.assertNotIn('id', response.data)

    def test_create_tag_user_no_profile(self):
        """
        Użytkownik zalogowany, ale nie ma profilu w danym Branch -> 403 FORBIDDEN
        """
        self.client.force_authenticate(user=self.sc_user)

        payload = {"name": "Tag Bez Profilu", "icon": "no_prof_icon.png", "color": "#123456"}
        response = self.client.post(
            self.url,
            data=payload,
            format='json',
            HTTP_HOST=self.domain_obj.domain
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)
        self.assertNotIn('id', response.data)