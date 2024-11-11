from .models import Event
from user_profile.models import EmployeeSchedule

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