from django.db import models
from branch.models import Branch


class Patient(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='patient', default=None)
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    age = models.IntegerField()


class Treatment(models.Model):
    branch = models.ForeignKey('branch.Branch', on_delete=models.CASCADE, related_name='treatment', null=True, blank=True)
    event = models.ForeignKey('event.Event', on_delete=models.CASCADE, related_name='treatment', null=True, blank=True)
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='treatment', null=True, blank=True)
    doctor = models.ForeignKey('user_profile.ProfileCentralUser', on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    tooth = models.CharField(max_length=255, default='Brak', null=True, blank=True)
    anesthesia = models.CharField(max_length=1024, null=True, blank=True)
    details = models.TextField(null=True, blank=True)


# class TreatmentFiles(models.Model):
#     branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='treatmentfiles')
#     treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='treatmentfiles')
#     file = models.FileField()
#     name = models.CharField(max_length=255)