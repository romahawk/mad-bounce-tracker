
from datetime import datetime, timedelta

def get_full_day_sequence(schedule, weekdays):
    sequence = []
    for week in sorted(schedule.keys(), key=lambda w: int(w.split('_')[1])):
        for day in weekdays:
            key = f"{week}_{day}"
            workout = schedule[week].get(day, 'Rest')
            sequence.append((key, week, day, workout))
    return sequence

def recalculate_schedule(base_key, new_base_date, schedule, weekdays, progress=None):
    sequence = get_full_day_sequence(schedule, weekdays)
    keys = [s[0] for s in sequence]
    if base_key not in keys:
        return {}

    base_index = keys.index(base_key)

    # Compute intervals between all days
    absolute_days = []
    for s in sequence:
        week_num = int(s[1].split('_')[1]) - 1
        day_offset = weekdays.index(s[2])
        absolute_days.append(week_num * 7 + day_offset)

    intervals = [absolute_days[i] - absolute_days[i - 1] for i in range(1, len(absolute_days))]

    # Shift all future dates starting from base_key
    updated_dates = {base_key: new_base_date.strftime('%Y-%m-%d')}
    current_date = new_base_date
    for i in range(base_index + 1, len(keys)):
        delta = intervals[i - 1]
        current_date += timedelta(days=max(1, delta))
        if progress and progress.get(keys[i], {}).get('completed', False):
            continue  # preserve completed
        updated_dates[keys[i]] = current_date.strftime('%Y-%m-%d')

    return updated_dates
