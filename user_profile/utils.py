from datetime import datetime, timedelta
from user_profile.models import EmployeeSchedule
from event.models import Event, PlanChange


def generate_daily_time_slots(doctor, date, interval_minutes):
    if doctor.role != 'doctor':
        return []

    try:
        plan_change = PlanChange.objects.get(doctor=doctor, date=date)
        start_time = plan_change.start_time
        end_time = plan_change.end_time
    except PlanChange.DoesNotExist:
        day_num = date.weekday()
        try:
            schedule = EmployeeSchedule.objects.get(employee=doctor, day_num=day_num)
            start_time = schedule.start_time
            end_time = schedule.end_time
        except EmployeeSchedule.DoesNotExist:
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
        slot_start_time = slot['start'].time()
        slot_end_time = slot['end'].time()
        slot_occupied = False

        # Sprawdź, czy slot jest zajęty przez wizytę lekarza
        for appointment in appointments:
            if appointment.start_time < slot_end_time and appointment.end_time > slot_start_time:
                slot['status'] = 'zajęty'
                slot['occupied_by'] = 'Ty'
                slot_occupied = True
                break

        if slot_occupied:
            continue

        # Sprawdź, czy slot jest zajęty przez inne wizyty w gabinecie
        if office:
            for appointment in other_appointments:
                if appointment.start_time < slot_end_time and appointment.end_time > slot_start_time:
                    occupied_by_doctor = appointment.doctor
                    slot['status'] = 'zajęty'
                    slot['occupied_by'] = f"{occupied_by_doctor.name} {occupied_by_doctor.surname}"
                    slot_occupied = True
                    break
        else:
            pass

    return slots

