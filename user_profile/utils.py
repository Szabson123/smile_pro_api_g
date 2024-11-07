from datetime import datetime, timedelta
from user_profile.models import DoctorSchedule
from event.models import Event

def generate_daily_time_slots(doctor, date, interval_minutes):
    day_of_week = date.weekday()

    try:
        schedule = DoctorSchedule.objects.get(doctor=doctor, day_of_week=day_of_week)
    except DoctorSchedule.DoesNotExist:
        return []
    
    start_datetime = datetime.combine(date, schedule.start_time)
    end_datetime = datetime.combine(date, schedule.end_time)

    slots = []
    current_time = start_datetime
    while current_time + timedelta(minutes=interval_minutes) <= end_datetime:
        slot = {
            'start': current_time,
            'end': current_time + timedelta(minutes=interval_minutes),
            'status': 'wolny'
        }
        slots.append(slot)
        current_time += timedelta(minutes=interval_minutes)

    return slots

def mark_occupied_slots(slots, appointments):
    for slot in slots:
        slot_start = slot['start']
        slot_end = slot['end']
        for appointment in appointments:
            appointment_start = datetime.combine(appointment.date, appointment.start_time)
            appointment_end = datetime.combine(appointment.date, appointment.end_time)
            if appointment_start < slot_end and appointment_end > slot_start:
                slot['status'] = 'zajęty'
                break  
    return slots
