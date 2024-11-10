from datetime import datetime, timedelta
from user_profile.models import DoctorSchedule
from event.models import Event, PlanChange

def generate_daily_time_slots(doctor, date, interval_minutes):
    try:
        plan_change = PlanChange.objects.get(doctor=doctor, date=date)
        start_time = plan_change.start_time
        end_time = plan_change.end_time
    except PlanChange.DoesNotExist:
        day_num = date.weekday()
        try:
            schedule = DoctorSchedule.objects.get(doctor=doctor, day_num=day_num)
            start_time = schedule.start_time
            end_time = schedule.end_time
        except DoctorSchedule.DoesNotExist:
            return []  

    start_datetime = datetime.combine(date, start_time)
    end_datetime = datetime.combine(date, end_time)

    slots = []
    current_time = start_datetime
    while current_time + timedelta(minutes=interval_minutes) <= end_datetime:
        slot = {
            'start': current_time,
            'end': current_time + timedelta(minutes=interval_minutes),
            'status': 'wolny',
            'occupied_by': None,
        }
        slots.append(slot)
        current_time += timedelta(minutes=interval_minutes)

    return slots

def mark_occupied_slots(slots, appointments, other_appointments, office):
    for slot in slots:
        slot_start = slot['start']
        slot_end = slot['end']
        slot_occupied = False

        for appointment in appointments:
            appointment_start = datetime.combine(appointment.date, appointment.start_time)
            appointment_end = datetime.combine(appointment.date, appointment.end_time)
            if appointment_start < slot_end and appointment_end > slot_start:
                slot['status'] = 'zajęty'
                slot['occupied_by'] = 'Ty'  
                slot_occupied = True
                break

        if slot_occupied:
            continue  

        if office:
            for other_appointment in other_appointments:
                if other_appointment.office_id == office.id:
                    appointment_start = datetime.combine(other_appointment.date, other_appointment.start_time)
                    appointment_end = datetime.combine(other_appointment.date, other_appointment.end_time)
                    if appointment_start < slot_end and appointment_end > slot_start:
                        occupied_by_profile = other_appointment.profile
                        slot['status'] = 'zajęty'
                        slot['occupied_by'] = f"{occupied_by_profile.name} {occupied_by_profile.surname}"
                        slot_occupied = True
                        break
        else:
            pass  

    return slots
