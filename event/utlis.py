from .models import Event
from user_profile.models import EmployeeSchedule
from collections import defaultdict
from datetime import timedelta

def get_time_slots_for_date_range(doctor, start_date, end_date, interval_minutes, office):
    if doctor.role != 'doctor':
        return []

    slots = []
    delta = timedelta(days=1)
    interval_delta = timedelta(minutes=interval_minutes)
    date_range = (start_date, end_date)

    # Fetch doctor's appointments
    doctor_appointments = Event.objects.filter(
        doctor=doctor,
        date__range=date_range
    ).values('date', 'start_time', 'end_time')

    # Fetch other appointments in the office if office is provided
    if office:
        other_appointments = Event.objects.filter(
            date__range=date_range,
            office=office
        ).exclude(doctor=doctor).values('date', 'start_time', 'end_time')
    else:
        other_appointments = []

    # Group appointments by date
    busy_intervals_by_date = defaultdict(list)
    for appt in doctor_appointments:
        busy_intervals_by_date[appt['date']].append((appt['start_time'], appt['end_time']))

    for appt in other_appointments:
        busy_intervals_by_date[appt['date']].append((appt['start_time'], appt['end_time']))

    # Merge overlapping intervals for each day
    for date in busy_intervals_by_date:
        intervals = sorted(busy_intervals_by_date[date])
        merged_intervals = [intervals[0]]
        for current in intervals[1:]:
            last_start, last_end = merged_intervals[-1]
            current_start, current_end = current
            if current_start <= last_end:
                merged_intervals[-1] = (last_start, max(last_end, current_end))
            else:
                merged_intervals.append(current)
        busy_intervals_by_date[date] = merged_intervals

    # Fetch plan changes and schedules
    plan_changes = PlanChange.objects.filter(
        doctor=doctor,
        date__range=date_range
    ).values('date', 'start_time', 'end_time')
    plan_changes_by_date = {pc['date']: pc for pc in plan_changes}

    schedules = EmployeeSchedule.objects.filter(
        employee=doctor
    ).values('day_num', 'start_time', 'end_time')
    schedules_by_day = {s['day_num']: s for s in schedules}

    current_date = start_date
    while current_date <= end_date:
        if current_date in plan_changes_by_date:
            working_hours = [(plan_changes_by_date[current_date]['start_time'], plan_changes_by_date[current_date]['end_time'])]
        else:
            day_num = current_date.weekday()
            schedule = schedules_by_day.get(day_num)
            if schedule:
                working_hours = [(schedule['start_time'], schedule['end_time'])]
            else:
                current_date += delta
                continue

        # Get busy intervals for the current date
        busy_intervals = busy_intervals_by_date.get(current_date, [])

        # Subtract busy intervals from working hours to get free intervals
        free_intervals = subtract_intervals(working_hours, busy_intervals)

        # Generate slots from free intervals
        for start_time, end_time in free_intervals:
            start_datetime = datetime.combine(current_date, start_time)
            end_datetime = datetime.combine(current_date, end_time)
            while start_datetime + interval_delta <= end_datetime:
                slots.append({
                    'start': start_datetime,
                    'end': start_datetime + interval_delta,
                    'status': 'wolny',
                    'occupied_by': None,
                })
                start_datetime += interval_delta

        current_date += delta

    return slots

def subtract_intervals(working_hours, busy_intervals):
    free_intervals = []
    for work_start, work_end in working_hours:
        temp_intervals = [(work_start, work_end)]
        for busy_start, busy_end in busy_intervals:
            new_intervals = []
            for interval_start, interval_end in temp_intervals:
                # No overlap
                if busy_end <= interval_start or busy_start >= interval_end:
                    new_intervals.append((interval_start, interval_end))
                else:
                    # Overlap exists
                    if interval_start < busy_start:
                        new_intervals.append((interval_start, busy_start))
                    if busy_end < interval_end:
                        new_intervals.append((busy_end, interval_end))
            temp_intervals = new_intervals
        free_intervals.extend(temp_intervals)
    return free_intervals