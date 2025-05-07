from datetime import datetime, timedelta

def recalculate_schedule(base_key, base_date, schedule, weekdays):
    ordered = []
    for week in sorted(schedule.keys(), key=lambda w: int(w.split('_')[1])):
        for i, day in enumerate(weekdays):
            if schedule[week].get(day, '').startswith('Training'):
                ordered.append(f"{week}_{day}")
    if base_key not in ordered:
        return {}
    base_index = ordered.index(base_key)
    updated_dates = {}
    for i in range(base_index, len(ordered)):
        delta_days = i - base_index
        new_date = base_date + timedelta(days=delta_days * 2)  # assuming every 2 days
        updated_dates[ordered[i]] = new_date.strftime('%Y-%m-%d')
    return updated_dates
