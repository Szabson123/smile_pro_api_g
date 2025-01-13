from django.db import models
from patients.models import Patient


class Obligation(models.Model):
    ammount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    when_paid = models.DateField(default=None)
    how_paid = models.CharField(null=True, blank=True)
    
    
class Deposits(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    ammonut = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)


class PiggyBank(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    sum = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)