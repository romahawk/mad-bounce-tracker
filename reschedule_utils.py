from datetime import datetime, timedelta

def get_training_day_sequence(schedule, weekdays):
    sequence = []
    for week in sorted(schedule.keys(), key=lambda w: int(w.split('_')[1])):
        for day in weekdays:
            if schedule[week].get(day, '').startswith('Training'):
                sequence.append((f"{week}_{day}", week, day))
    return sequence

def recalculate_schedule(base_key, new_base_date, schedule, weekdays, progress=None):
    sequence = get_training_day_sequence(schedule, weekdays)
    keys = [s[0] for s in sequence]
    if base_key not in keys:
        return {}
    base_index = keys.index(base_key)

    # Calculate absolute day offsets for each training session based on original schedule
    absolute_days = []
    for s in sequence:
        week_num = int(s[1].split('_')[1]) - 1
        day_offset = weekdays.index(s[2])
        absolute_days.append(week_num * 7 + day_offset)

    # Compute relative intervals between each training session
    intervals = [absolute_days[i] - absolute_days[i - 1] for i in range(1, len(absolute_days))]

    # Shift only future workouts based on the base workout's new date
    updated_dates = {base_key: new_base_date.strftime('%Y-%m-%d')}
    current_date = new_base_date
    for i in range(base_index + 1, len(keys)):
        delta = intervals[i - 1]  # interval from previous training day
        # Ensure the interval is at least 1 day to avoid same-day assignments
        current_date += timedelta(days=max(1, delta))
        updated_dates[keys[i]] = current_date.strftime('%Y-%m-%d')

    # If progress is provided, update only uncompleted future workouts
    if progress:
        for key in updated_dates:
            if key != base_key and progress.get(key, {}).get('completed', False):
                updated_dates[key] = progress[key]['planned']  # Preserve completed dates

    return updated_dates