
from rest_framework.exceptions import ValidationError

from user_profile.models import ProfileCentralUser
from .models import Office, Event
from patients.models import Patient
from user_profile.models import EmployeeSchedule

# Metody avaible 
def is_doctor_available(doctor, date, start_time, end_time, exclude_event_id=None):
    day_num = date.weekday()
    try:
        schedule = EmployeeSchedule.objects.get(employee=doctor, day_num=day_num)
    except EmployeeSchedule.DoesNotExist:
        return False  

    if start_time < schedule.start_time or end_time > schedule.end_time:
        return False

    conflicting_events = Event.objects.filter(
        doctor=doctor,
        date=date,
        start_time__lt=end_time,
        end_time__gt=start_time
    )

    if exclude_event_id:
        conflicting_events = conflicting_events.exclude(id=exclude_event_id)

    return not conflicting_events.exists()

def is_assistant_available(assistant, date, start_time, end_time, exclude_event_id=None):
    day_num = date.weekday()
    try:
        schedule = EmployeeSchedule.objects.get(employee=assistant, day_num=day_num)
    except EmployeeSchedule.DoesNotExist:
        return False  

    if start_time < schedule.start_time or end_time > schedule.end_time:
        return False

    conflicting_events = Event.objects.filter(
        assistant=assistant,
        date=date,
        start_time__lt=end_time,
        end_time__gt=start_time
    )

    if exclude_event_id:
        conflicting_events = conflicting_events.exclude(id=exclude_event_id)

    return not conflicting_events.exists()

def is_office_available(office, date, start_time, end_time, exclude_event_id=None):
    conflicting_events = Event.objects.filter(
        office=office,
        date=date,
        start_time__lt=end_time,
        end_time__gt=start_time
    )

    if exclude_event_id:
        conflicting_events = conflicting_events.exclude(id=exclude_event_id)

    return not conflicting_events.exists()

def is_patient_available(patient, date, start_time, end_time, exclude_event_id=None):
    conflicting_events = Event.objects.filter(
        patient=patient,
        date=date,
        start_time__lt=end_time,
        end_time__gt=start_time
    )

    if exclude_event_id:
        conflicting_events = conflicting_events.exclude(id=exclude_event_id)

    return not conflicting_events.exists()

# --------------------------------------------------------------------------------------------------------------------------------
# Metody walidujące istnienie
def validate_doctor_id(value):
    try:
        doctor = ProfileCentralUser.objects.get(id=value)
    except ProfileCentralUser.DoesNotExist:
        raise ValidationError("Nie znaleziono lekarza o podanym identyfikatorze.")
    
    if doctor.role != 'doctor':
        raise ValidationError("Sloty czasowe mogą być generowane tylko dla lekarzy.")
    
    return value


def validate_office_id(office_id):
    if office_id:
        try:
            office = Office.objects.get(id=office_id)
        except Office.DoesNotExist:
            raise ValidationError("Nie znaleziono gabinetu o podanym identyfikatorze.")
    return office_id


def validate_assistant_id(assistant_id):
    if assistant_id is not None:
        try:
            assistant = ProfileCentralUser.objects.get(id=assistant_id, role='assistant')
        except ProfileCentralUser.DoesNotExist:
            raise ValidationError({"assistant_id": "Wybrany asystent nie istnieje lub nie ma roli 'assistant'."})
        return assistant
    return None


def validate_patient_id(patient_id):
    if patient_id is not None:
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            raise ValidationError({"patient_id": "Wybrany pacjent nie istnieje."})
        return patient
    else:
        return("Nie można stowrzyć bez pdoania pacjenta")


def validate_dates(start_date, end_date):
    if start_date is None or end_date is None:
        raise ValidationError("Wymagane jest podanie daty początkowej i końcowej.")
        
    if start_date > end_date:
        raise ValidationError("Data początkowa musi być wcześniejsza lub równa dacie końcowej.")


def validate_times(start_time, end_time):
    if start_time is None or end_time is None:
        raise ValidationError("Wymagane jest podanie godziny rozpoczęcia i zakończenia.")
        
    if start_time >= end_time:
        raise ValidationError({"end_time": "Godzina zakończenia musi być po godzinie rozpoczęcia."})