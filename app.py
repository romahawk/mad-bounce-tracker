import streamlit as st
import json
import os
import datetime
import plotly.graph_objects as go
import streamlit as st
import firebase_admin
from firebase_admin import credentials, initialize_app, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    initialize_app(cred)
db = firestore.client()

# Load program data
with open("program_data.json", "r", encoding="utf-8") as f:
    program_data = json.load(f)

# Load progress data (or initialize)
if os.path.exists("progress.json"):
    with open("progress.json", "r") as f:
        progress = json.load(f)
else:
    progress = {}

# Load or initialize schedule config
if os.path.exists("schedule.json"):
    with open("schedule.json", "r") as f:
        workout_schedule = json.load(f)
else:
    workout_schedule = program_data.get("schedule", {})
    with open("schedule.json", "w") as f:
        json.dump(workout_schedule, f, indent=2)

# --- Streamlit UI ---
st.set_page_config(layout="wide")
st.markdown("<h1 style='font-size: 36px; color: #1e3799;'>🚀 Mad Bounce Vertical Jump Program</h1>", unsafe_allow_html=True)

# Calculate progress
completed = len(progress)
total_workouts = 34
progress_percent = round((completed / total_workouts) * 100)

# Progress bar with text
st.markdown(f"""
<div class='sticky-container'>
<div style='background-color: #f0f4f8; border-radius: 12px; padding: 16px 12px; margin-top: 10px;'>
  <div style='font-size: 22px; font-weight: 600; color: #2d3436; margin-bottom: 12px;'>🔥 Your Progress</div>
  <div style='background-color: #dfe6e9; height: 36px; width: 100%; border-radius: 10px; overflow: hidden; box-shadow: inset 0 0 5px rgba(0,0,0,0.15);'>
    <div style='width: {progress_percent}%; height: 100%; background-color: #00b894; text-align: center;
                color: white; line-height: 36px; font-weight: bold; font-size: 14px; transition: width 0.5s ease-in-out;'>
      {completed} of {total_workouts} ({progress_percent}%)
    </div>
  </div>
  <p style='font-style: italic; color: #636e72; margin-top: 12px;'>“Small progress is still progress.”</p>
</div>
</div>""", unsafe_allow_html=True)

# Session state init
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "selected_workout" not in st.session_state:
    st.session_state.selected_workout = None
if "selected_date_key" not in st.session_state:
    st.session_state.selected_date_key = None
if "start_date" not in st.session_state:
    st.session_state.start_date = None

# --- Editable Calendar ---
st.markdown("""
<div class='calendar-wrapper'>
<h2 style='font-size: 22px;'>📅 Weekly Training Grid Editor</h2>

# Week selection with pagination
week_keys = [w for w in program_data["workouts"].keys() if w.startswith("week_") and len(w.split('_')) == 2 and w.split('_')[1].isdigit()]
week_keys_sorted = sorted(week_keys, key=lambda w: int(w.split('_')[1]))
pages = [week_keys_sorted[i:i + 4] for i in range(0, len(week_keys_sorted), 4)]

if not pages:
    st.error("No valid workout weeks found in program_data.json.")
    st.stop()

def go_prev():
    st.session_state.current_page = max(1, st.session_state.current_page - 1)

def go_next():
    st.session_state.current_page = min(len(pages), st.session_state.current_page + 1)


""", unsafe_allow_html=True)

nav1, nav2, nav3 = st.columns([1, 1, 1])
with nav1:
    st.button("⬅️", on_click=go_prev, disabled=st.session_state.current_page == 1)
with nav2:
    st.button("🔄 Reset", on_click=lambda: st.session_state.update(reset=True))
with nav3:
    st.button("➡️", on_click=go_next, disabled=st.session_state.current_page == len(pages))

st.markdown("</div>", unsafe_allow_html=True)  # close sticky-container

current_page = st.session_state.current_page
page_weeks = pages[current_page - 1]

# Reset button


weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
editable_weeks = page_weeks

# Compute base date from first completed workout
if progress:
    if not st.session_state.start_date:
        first_completed_key = sorted(progress.keys())[0]
        week_idx = int(first_completed_key.split("_")[1]) - 1
        st.session_state.start_date = datetime.date.today() - datetime.timedelta(weeks=week_idx)
else:
    st.session_state.start_date = None

base_date = st.session_state.start_date

if not base_date:
    st.info("📅 Dates will appear once you complete your first workout.")


# --- Inject global CSS ---
st.markdown("""
<style>
div[data-testid="stButton"] button {
    width: 110px;
    height: 80px;
    white-space: pre-wrap;
    text-align: center;
    border-radius: 8px;
    font-size: 12px;
    padding: 6px;
    overflow: hidden;
}

/* Responsive scrollable calendar container */
.scroll-container {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 12px;
}

@media (max-width: 768px) {
    div[data-testid="stButton"] button {
        width: 100px;
        height: 70px;
        font-size: 11px;
    }
}
.calendar-wrapper {
    max-height: 80vh;
    overflow-y: auto;
    position: relative;
    padding-bottom: 20px;
}

.calendar-wrapper .sticky-nav {
    position: sticky;
    top: 0;
    background-color: #fff9db;
    padding: 10px 0;
    z-index: 10;
    border-bottom: 1px solid #e0e0e0;
}


.sticky-container {
    position: sticky;
    top: 0;
    background-color: #ffffff;
    z-index: 999;
    padding-top: 5px;
    padding-bottom: 5px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    border-bottom: 1px solid #e0e0e0;
}

</style>
""", unsafe_allow_html=True)

# Draw calendar
st.markdown("<div class='scroll-container'>", unsafe_allow_html=True)
for week_index, w in enumerate(editable_weeks):
    with st.container():
        st.markdown(f"<div style='padding: 8px 0; font-size: 20px; font-weight: bold; color: #2c3e50;'>{w}</div>", unsafe_allow_html=True)
        cols = st.columns(len(weekdays))
        workouts_in_week = 0
        for i, d in enumerate(weekdays):
            with cols[i]:
                default_val = workout_schedule.get(w, {}).get(d, "Rest")
                if base_date:
                    day_offset = (week_keys_sorted.index(w) * 7) + i
                    current_date = base_date + datetime.timedelta(days=day_offset)
                    date_str = current_date.strftime("%b %d")
                else:
                    date_str = ""

                date_key = f"{w}_{d}"
                is_workout_day = default_val.startswith("Training")
                is_completed = date_key in progress
                is_today = base_date and (current_date == datetime.date.today())

                if is_completed:
                    color = "#28a745"  # green
                elif is_today and is_workout_day:
                    color = "#ffc107"  # yellow
                elif is_workout_day:
                    color = "#007bff"  # blue
                else:
                    color = "#f8f9fa"  # light gray

                button_text = f"{d[:3]}\n{default_val}\n{date_str}"

                # Wrap button in colored div
                st.markdown(f"<div style='background-color:{color}; padding:2px; border-radius:8px;'>", unsafe_allow_html=True)
                if st.button(button_text, key=f"btn_{w}_{d}"):
                    if is_workout_day:
                        st.session_state.selected_workout = default_val
                        st.session_state.selected_date_key = date_key
                st.markdown("</div>", unsafe_allow_html=True)

                if w not in workout_schedule:
                    workout_schedule[w] = {}
                workout_schedule[w][d] = default_val

                if is_workout_day:
                    workouts_in_week += 1

        st.caption(f"📜 Workouts this week: {workouts_in_week}")
st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # closes scroll-container
st.markdown("</div>", unsafe_allow_html=True)  # closes calendar-wrapper

# --- Sidebar Workout Viewer ---
if st.session_state.selected_workout and st.session_state.selected_date_key:
    workout_name = st.session_state.selected_workout
    date_key = st.session_state.selected_date_key
    week = date_key.split("_")[0] + "_" + date_key.split("_")[1]
    workout_data = program_data["workouts"].get(week, {}).get(workout_name)

    if workout_data:
        with st.sidebar:
            st.markdown(f"<h3 style='margin-bottom: 5px;'>⛹️‍♂️ <span style='font-size:20px;'>Workout {workout_name} ({workout_data['location']})</span></h3>", unsafe_allow_html=True)

            for section, exercises in workout_data["exercises"].items():
                st.markdown(f"<h4 style='color:#2980b9;'>{section}</h4>", unsafe_allow_html=True)
                for ex in exercises:
                    st.markdown(f"<span style='font-weight:bold;'>{ex['name']}</span> - {ex['sets']} sets x {ex['reps']}", unsafe_allow_html=True)
                # Auto-include stretching blocks
                if section.lower() == "warmup":
                    st.markdown(f"<h4 style='color:#2980b9;'>Light Stretching</h4>", unsafe_allow_html=True)
                    st.markdown(f"<span style='font-weight:bold;'>Stretch major muscle groups</span> - 1 set x 30 sec", unsafe_allow_html=True)
                if section.lower() == "main":
                    st.markdown(f"<h4 style='color:#2980b9;'>Heavy Stretching</h4>", unsafe_allow_html=True)
                    st.markdown(f"<span style='font-weight:bold;'>Deep hamstring/quads/hips stretch</span> - 2 sets x 45 sec", unsafe_allow_html=True)

            if st.checkbox("✅ Mark workout as completed", value=date_key in progress):
                progress[date_key] = True
            else:
                progress.pop(date_key, None)
            with open("progress.json", "w") as f:
                json.dump(progress, f, indent=2)

            note_key = f"note_{date_key}"
            if os.path.exists("notes.json"):
                with open("notes.json", "r") as f:
                    notes = json.load(f)
            else:
                notes = {}
            note_text = st.text_area("🗒 Notes", value=notes.get(note_key, ""))
            if st.button("💾 Save Workout"):
                notes[note_key] = note_text
                with open("notes.json", "w") as f:
                    json.dump(notes, f, indent=2)
                st.success("Workout saved!")

            if st.button("❌ Close Workout"):
                st.session_state.selected_workout = None
                st.session_state.selected_date_key = None

# Save updated schedule
with open("schedule.json", "w") as f:
    json.dump(workout_schedule, f, indent=2)

st.success("Schedule updated and saved.")
