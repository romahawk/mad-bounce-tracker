import json
import os

# Toggle for local dev vs production
IS_DEV = True
DATA_PATH = "./" if IS_DEV else "/app/data/"

def get_file_path(filename):
    return os.path.join(DATA_PATH, filename)

def load_json(filename):
    path = get_file_path(filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    path = get_file_path(filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def reset_progress():
    save_json("./data/progress.json", {})

def reset_schedule():
    from program_data import default_schedule_from_program
    schedule = default_schedule_from_program()
    save_json("./data/schedule.json", schedule)

def reset_notes():
    save_json("./data/notes.json", {})
