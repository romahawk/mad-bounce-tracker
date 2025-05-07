import streamlit as st
import datetime
from persistence import load_json, save_json, reset_progress, reset_schedule, reset_notes
from reschedule_utils import recalculate_schedule

IS_DEV = True

if not IS_DEV:
    import firebase_admin
    from firebase_admin import credentials, initialize_app, firestore
    if not firebase_admin._apps:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        initialize_app(cred)
    db = firestore.client()

st.set_page_config(layout="wide")
program_data = load_json("./data/program_data.json")
progress = load_json("./data/progress.json") or {}
workout_schedule = load_json("./data/schedule.json") or program_data.get("schedule", {})
notes = load_json("./data/notes.json") or {}
save_json("./data/schedule.json", workout_schedule)

st.markdown("<h1 style='font-size: 36px; color: #1e3799;'>🚀 Mad Bounce Vertical Jump Program</h1>", unsafe_allow_html=True)
if "start_date" not in st.session_state:
    st.session_state.start_date = datetime.date.today()
st.session_state.start_date = st.date_input("📅 Select Start Date (First Completed Workout)", value=st.session_state.start_date)
base_date = st.session_state.start_date
completed = len([v for v in progress.values() if v == True or isinstance(v, dict) and v.get('completed')])
total_workouts = 34
progress_percent = round((completed / total_workouts) * 100)
st.markdown(f"""
<div style='background-color: #f0f4f8; border-radius: 12px; padding: 16px 12px;'>
  <div style='font-size: 22px; font-weight: 600;'>🔥 Your Progress</div>
  <div style='background-color: #dfe6e9; height: 36px; border-radius: 10px;'>
    <div style='width: {progress_percent}%; height: 100%; background-color: #00b894; text-align: center;
                color: white; line-height: 36px; font-weight: bold;'>
      {completed} of {total_workouts} ({progress_percent}%)
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "selected_workout" not in st.session_state:
    st.session_state.selected_workout = None
if "selected_date_key" not in st.session_state:
    st.session_state.selected_date_key = None
weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
week_keys = sorted([w for w in program_data['workouts']], key=lambda x: int(x.split('_')[1]))
pages = [week_keys[i:i+2] for i in range(0, len(week_keys), 2)]
current_page = st.session_state.current_page
page_weeks = pages[current_page - 1]
col1, col2, col3 = st.columns(3)
with col1:
    st.button("⬅️ Prev", on_click=lambda: st.session_state.update(current_page=max(1, current_page - 1)))
with col2:
    st.button("🔄 Reset All", on_click=lambda: (reset_progress(), reset_schedule(), reset_notes()))
with col3:
    st.button("➡️ Next", on_click=lambda: st.session_state.update(current_page=min(len(pages), current_page + 1)))
for w in page_weeks:
    st.subheader(f"📅 {w.replace('_', ' ').title()}")
    cols = st.columns(7)
    for i, day in enumerate(weekdays):
        default_val = workout_schedule.get(w, {}).get(day, "Rest")
        date_key = f"{w}_{day}"
        is_workout = default_val.startswith("Training")
        is_completed = progress.get(date_key) == True or (isinstance(progress.get(date_key), dict) and progress[date_key].get('completed'))
        is_today = base_date + datetime.timedelta(days=(week_keys.index(w)*7 + i)) == datetime.date.today()
        color = "#28a745" if is_completed else "#ffc107" if is_today and is_workout else "#007bff" if is_workout else "#e0e0e0"
        workout_date = base_date + datetime.timedelta(days=(week_keys.index(w)*7 + i))
        label = f"{day[:3]} {workout_date.strftime('%b %d')}\n{'🟢 ' + default_val if is_workout else '💤 Rest'}"
        with cols[i]:
            st.markdown(f"<div style='background-color:{color}; padding:4px; border-radius:6px;'>", unsafe_allow_html=True)
            if st.button(label, key=f"btn_{w}_{day}"):
                st.session_state.selected_workout = default_val
                st.session_state.selected_date_key = date_key
            st.markdown("</div>", unsafe_allow_html=True)
if st.session_state.selected_workout and st.session_state.selected_date_key:
    wk_name = st.session_state.selected_workout
    date_key = st.session_state.selected_date_key
    week = date_key.split('_')[0] + '_' + date_key.split('_')[1]
    workout_data = program_data['workouts'].get(week, {}).get(wk_name)
    if workout_data:
        with st.sidebar:
            st.subheader(f"🏋️ {wk_name} ({workout_data['location']})")
            for section, exs in workout_data['exercises'].items():
                st.markdown(f"### {section}")
                for ex in exs:
                    st.markdown(f"- **{ex['name']}**: {ex['sets']} x {ex['reps']}")
            # Completion toggle
            completed_val = progress.get(date_key) == True or (isinstance(progress.get(date_key), dict) and progress[date_key].get('completed'))
            if st.checkbox("✅ Mark as completed", value=completed_val):
                progress[date_key] = True
            else:
                progress.pop(date_key, None)
            save_json("./data/progress.json", progress)
            # Reschedule section
            if wk_name.startswith("Training"):
                edit_date = st.date_input("📅 New Start Date for Rescheduling", value=base_date)
                if st.button("🔁 Reschedule from this workout"):
                    future_dates = recalculate_schedule(date_key, edit_date, workout_schedule, weekdays)
                    for k, v in future_dates.items():
                        if k != date_key:
                            progress[k] = {'planned': v}
                    save_json("./data/progress.json", progress)
                    st.success("Future workouts rescheduled.")
            note_key = f"note_{date_key}"
            note = st.text_area("📝 Notes", value=notes.get(note_key, ""))
            if st.button("💾 Save Notes"):
                notes[note_key] = note
                save_json("./data/notes.json", notes)
                st.success("Notes saved!")
            if st.button("❌ Close Workout"):
                st.session_state.selected_workout = None
                st.session_state.selected_date_key = None
