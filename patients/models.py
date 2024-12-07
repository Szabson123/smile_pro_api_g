from django.db import models
from branch.models import Branch


class Patient(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='patient', default=None)
    name = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    age = models.IntegerField()

    