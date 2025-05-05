import streamlit as st
import json
import os
import datetime
import plotly.graph_objects as go
from firebase_config import db

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
st.title(":star: Mad Bounce Training rogram Progress")

# Calculate progress
completed = len(progress)
total_workouts = 34
progress_percent = round((completed / total_workouts) * 100)

# Progress bar with text
st.plotly_chart(go.Figure(go.Bar(
    x=[completed],
    orientation='h',
    marker=dict(color='green'),
    text=f"{completed} of {total_workouts} ({progress_percent}%)",
    textposition='outside'
)).update_layout(
    xaxis=dict(range=[0, total_workouts], visible=False),
    yaxis=dict(visible=False),
    height=60,
    margin=dict(l=0, r=0, t=0, b=0),
    showlegend=False
), use_container_width=True)

# Session state init
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "selected_workout" not in st.session_state:
    st.session_state.selected_workout = None
if "selected_date_key" not in st.session_state:
    st.session_state.selected_date_key = None
if "start_date" not in st.session_state:
    st.session_state.start_date = datetime.date.today()

# --- Editable Calendar ---
st.subheader(":calendar: Weekly Training Grid Editor")

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

col1, col2 = st.columns([1, 1])
with col1:
    st.button("⬅️ Prev", on_click=go_prev, disabled=st.session_state.current_page == 1)
with col2:
    st.button("Next ➡️", on_click=go_next, disabled=st.session_state.current_page == len(pages))

current_page = st.session_state.current_page
page_weeks = pages[current_page - 1]

# Reset button
if st.button("🔄 Reset schedule to default"):
    workout_schedule = program_data.get("schedule", {})
    with open("schedule.json", "w") as f:
        json.dump(workout_schedule, f, indent=2)
    valid_keys = {
        f"{w}_{d}" for w in workout_schedule for d in workout_schedule[w] if workout_schedule[w][d].startswith("Training")
    }
    progress = {k: v for k, v in progress.items() if k in valid_keys}
    with open("progress.json", "w") as f:
        json.dump(progress, f, indent=2)
    st.rerun()

weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
editable_weeks = page_weeks

# Uniform button style
button_style = """
display: inline-block;
padding: 10px;
font-size: 14px;
text-align: center;
width: 100%;
height: 50px;
border-radius: 6px;
border: 1px solid #ccc;
background-color: #f8f9fa;
box-shadow: 1px 1px 3px rgba(0,0,0,0.05);
margin: 4px auto;
display: flex;
justify-content: center;
align-items: center;
"""

# Compute base date
base_date = None
for k in sorted(progress):
    if k in workout_schedule:
        continue
    week, day = k.split("_")[0] + "_" + k.split("_")[1], k.split("_")[2]
    if week in workout_schedule and workout_schedule[week].get(day, "").startswith("Training"):
        base_date = datetime.date.today()
        break
if not base_date:
    base_date = datetime.date.today()

# Draw calendar
for week_index, w in enumerate(editable_weeks):
    with st.container():
        st.markdown(f"<div style='padding: 8px 0; font-size: 20px; font-weight: bold; color: #2c3e50;'>{w}</div>", unsafe_allow_html=True)
        cols = st.columns(len(weekdays))
        workouts_in_week = 0
        for i, d in enumerate(weekdays):
            with cols[i]:
                default_val = workout_schedule.get(w, {}).get(d, "Rest")
                day_offset = (week_keys_sorted.index(w) * 7) + i
                current_date = base_date + datetime.timedelta(days=day_offset)
                date_str = current_date.strftime("%b %d")
                today = datetime.datetime.now().strftime("%A")
                highlight = (w == f"week_{datetime.datetime.now().isocalendar()[1]}" and d == today)
                highlight_completed = f"{w}_{d}" in progress and default_val.startswith("Training")
                style = "background-color: #90ee90;" if highlight_completed else ("background-color: #ffffcc;" if highlight else "")
                btn_label = f"{d[:3]} {default_val}"
                button_html = f"""
                <div style='{button_style}{style}'>{btn_label}</div>
                """
                if st.button(btn_label, key=f"btn-{w}-{d}", help=f"Click to view or mark {default_val}"):
                    if default_val.startswith("Training"):
                        st.session_state.selected_workout = default_val
                        st.session_state.selected_date_key = f"{w}_{d}"
                st.markdown(button_html, unsafe_allow_html=True)
                if w not in workout_schedule:
                    workout_schedule[w] = {}
                workout_schedule[w][d] = default_val
                if default_val.startswith("Training"):
                    workouts_in_week += 1
        st.caption(f"\U0001f4dc Workouts this week: {workouts_in_week}")

# --- Sidebar Workout Viewer ---
if st.session_state.selected_workout and st.session_state.selected_date_key:
    workout_name = st.session_state.selected_workout
    date_key = st.session_state.selected_date_key
    week = date_key.split("_")[0] + "_" + date_key.split("_")[1]
    workout_data = program_data["workouts"].get(week, {}).get(workout_name)

    if workout_data:
        with st.sidebar:
            st.markdown(f"<h3 style='margin-bottom: 5px;'>🏋️‍♂️ <span style='font-size:20px;'>Workout {workout_name} ({workout_data['location']})</span></h3>", unsafe_allow_html=True)

            for section, exercises in workout_data["exercises"].items():
                st.markdown(f"<h4 style='color:#2980b9;'>{section}</h4>", unsafe_allow_html=True)
                for ex in exercises:
                    st.markdown(f"<span style='font-weight:bold;'>{ex['name']}</span> - {ex['sets']} sets x {ex['reps']}", unsafe_allow_html=True)

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
            if st.button("💾 Save Notes"):
                notes[note_key] = note_text
                with open("notes.json", "w") as f:
                    json.dump(notes, f, indent=2)
                st.success("Notes saved!")

            if st.button("❌ Close Workout"):
                st.session_state.selected_workout = None
                st.session_state.selected_date_key = None

# Save updated schedule
with open("schedule.json", "w") as f:
    json.dump(workout_schedule, f, indent=2)

st.success("Schedule updated and saved.")
