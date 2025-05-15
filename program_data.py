import json
import os

def default_schedule_from_program(path='./data/program_data.json'):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('schedule', {})
