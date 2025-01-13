from django.db import models
from user_profile.models import ProfileCentralUser
from patients.models import Patient
from branch.models import Branch
from payment.models import Obligation
import string

TypeFree = [
    ('zwolnienie', 'Zwolnienie'),
    ('urlop', 'Urlop'),
    ('inne', 'Inne'),
]

Statuses_of_Event = [
    ('planned', 'Planned'),
    ('started', 'Started'),
    ('in_progres', 'In_Progres'),
    ('ended', 'Ended'),
    ('canceled', 'Canceled'),
]


class EventStatus(models.Model):
    number = models.CharField(max_length=5, null=True)
    status = models.CharField(choices=Statuses_of_Event, default='planned')


class Office(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='office', default=None)
    name = models.CharField(max_length=255)


class VisitType(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='visittype', default=None)
    name = models.CharField(max_length=255, unique=True)
    cost = models.DecimalField(decimal_places=2, max_digits=10)


class Tags(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='tags', default=None)
    name = models.CharField(max_length=255)
    icon = models.CharField(max_length=255, blank=True, null=True)
    color = models.CharField(max_length=255)

    class Meta:
        unique_together = ('branch', 'name')


class Event(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='events', default=None)
    doctor = models.ForeignKey(ProfileCentralUser, on_delete=models.CASCADE)
    date = models.DateField(default=None)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, blank=True, null=True)
    start_time = models.TimeField(default=None)
    end_time = models.TimeField(default=None)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, blank=True, null=True)
    visit_type = models.ForeignKey(VisitType, on_delete=models.CASCADE, null=True, blank=True, default=None)
    cost = models.OneToOneField(Obligation, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    tags = models.ManyToManyField(Tags, blank=True)
    assistant = models.ForeignKey(ProfileCentralUser, on_delete=models.CASCADE, blank=True, null=True, related_name='assistant')
    is_rep = models.BooleanField(default=False)
    rep_id = models.IntegerField(default=0)
    event_status = models.OneToOneField(EventStatus, null=True, blank=True, related_name='event', on_delete=models.CASCADE)
    
    class Meta:
        indexes = [
            models.Index(fields=['doctor', 'date']),
            models.Index(fields=['office', 'date']),
        ]


class Absence(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='absences', default=None)
    profile = models.ForeignKey(ProfileCentralUser, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    type = models.CharField(max_length=30, choices=TypeFree, default='inne')
    reason = models.TextField(null=True, blank=True)


class PlanChange(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='planchange', default=None)
    doctor = models.ForeignKey(ProfileCentralUser, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
