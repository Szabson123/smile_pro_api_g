from django.db import models
from patients.models import Patient
from branch.models import Branch

class Obligation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True, related_name='obligation')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    to_count = models.BooleanField(default=False, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    when_paid = models.DateField(null=True, blank=True)
    how_paid = models.CharField(null=True, blank=True, max_length=255)
    
    
class Deposits(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='deposit')
    amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    date = models.DateField(auto_now_add=True, null=True, blank=True)


class PiggyBank(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    sum = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)