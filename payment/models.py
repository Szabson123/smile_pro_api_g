from django.db import models
from patients.models import Patient


class Payment(models.Model):
    ammount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)


class PiggyBank(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)