import streamlit as st
import datetime
from persistence import load_json, save_json, reset_progress, reset_schedule, reset_notes, load_start_date, save_start_date, reset_start_date
from reschedule_utils import recalculate_schedule, get_training_day_sequence

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

# Initialize planned dates for all training days if not set
base_date = datetime.date(2025, 5, 9)  # Default base date
if not progress:
    # Get the first training day key as base_key
    sequence = get_training_day_sequence(workout_schedule, ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    base_key = sequence[0][0] if sequence else next(iter(workout_schedule.keys())) + "_Monday"  # Fallback if sequence is empty
    initial_dates = recalculate_schedule(base_key, base_date, workout_schedule, ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    for key, date in initial_dates.items():
        progress[key] = {'completed': False, 'planned': date}
    save_json("./data/progress.json", progress)

# Load start date from persistent storage
if "start_date" not in st.session_state or st.session_state.start_date is None:
    saved_start_date = load_start_date()
    if saved_start_date:
        st.session_state.start_date = datetime.datetime.strptime(saved_start_date, "%Y-%m-%d").date()
    else:
        st.session_state.start_date = base_date

# Display and save start date
with st.sidebar:
    st.markdown("### 📅 Start Date (First Completed Workout)")
    saved_start_date = load_start_date()
    disabled = saved_start_date is not None
    current_start_date = st.date_input("", value=st.session_state.start_date, disabled=disabled, key="start_date_input")
    if not disabled:
        if st.button("💾 Save Start Date"):
            save_start_date(current_start_date.strftime("%Y-%m-%d"))
            st.session_state.start_date = current_start_date
            # Update all planned dates based on new start date
            sequence = get_training_day_sequence(workout_schedule, ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
            base_key = sequence[0][0] if sequence else next(iter(workout_schedule.keys())) + "_Monday"
            updated_dates = recalculate_schedule(base_key, current_start_date, workout_schedule, ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], progress)
            for key, date in updated_dates.items():
                current_status = progress.get(key, {}).get('completed', False)
                progress[key] = {'planned': date, 'completed': current_status}
            save_json("./data/progress.json", progress)
            st.success("Start date saved and calendar updated!")
    else:
        st.markdown("Start date is set and defines your training calendar. Use 🔄 Reset All to change it.")

st.session_state.start_date = st.session_state.start_date  # Lock start date after saving

st.markdown("<h1 style='font-size: 36px; color: #1e3799;'>🚀 Mad Bounce Vertical Jump Program</h1>", unsafe_allow_html=True)
completed = len([v for v in progress.values() if isinstance(v, dict) and v.get('completed')])
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
  <div style='text-align: center; font-size: 16px; font-weight: 500; color: #2ecc71; margin-top: 8px;'>
    Keep pushing—your jump is getting higher every day! 🚀
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
pages = [week_keys[i:i+3] for i in range(0, len(week_keys), 3)]
current_page = st.session_state.current_page
page_weeks = pages[current_page - 1]

# Pagination
# Custom CSS for hover effect, button styling, and full-width alignment
st.markdown("""
<style>
.button-container {
    border-radius: 12px;
    padding: 4px 0; /* Reduced vertical padding */
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100vw; /* Full viewport width */
    position: relative;
    left: 0;
    margin-left: calc(-50vw + 50%); /* Center within viewport */
}
.button-wrapper button {
    padding: 4px 10px; /* Reduced vertical padding */
    border-radius: 6px;
    border: 1px solid #ccc;
    background-color: transparent;
    cursor: pointer;
    transition: all 0.3s ease;
    width: 100%; /* Ensure buttons take full width of their column */
}
.button-wrapper button:hover:not(:disabled) {
    background-color: #e0e0e0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.button-wrapper button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
}
</style>
""", unsafe_allow_html=True)

# Button layout using a container div
st.markdown('<div class="button-container">', unsafe_allow_html=True)

# Use st.columns to create a horizontal layout
col1, col2, col3 = st.columns([1, 1, 1])  # Equal widths for each button

with col1:
    st.markdown('<div class="button-wrapper">', unsafe_allow_html=True)
    st.button("⬅️ Prev", on_click=lambda: st.session_state.update(current_page=max(1, current_page - 1)), disabled=current_page == 1)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="button-wrapper">', unsafe_allow_html=True)
    st.button("🔄 Reset All", on_click=lambda: (reset_progress(), reset_schedule(), reset_notes(), reset_start_date(), st.session_state.update(current_page=1)))
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="button-wrapper">', unsafe_allow_html=True)
    st.button("➡️ Next", on_click=lambda: st.session_state.update(current_page=min(len(pages), current_page + 1)), disabled=current_page == len(pages))
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Base date for workout scheduling
base_date = st.session_state.start_date
for w in page_weeks:
    st.subheader(f"📅 {w.replace('_', ' ').title()}")
    cols = st.columns(7)
    for i, day in enumerate(weekdays):
        default_val = workout_schedule.get(w, {}).get(day, "Rest")
        date_key = f"{w}_{day}"
        is_workout = default_val.startswith("Training")
        val = progress.get(date_key, {})
        is_completed = isinstance(val, dict) and val.get('completed', False)
        if isinstance(val, dict) and "planned" in val:
            workout_date = datetime.datetime.strptime(val["planned"], "%Y-%m-%d").date()
        else:
            workout_date = base_date + datetime.timedelta(days=(week_keys.index(w)*7 + i))
        is_today = workout_date == datetime.date.today()
        color = "#28a745" if is_completed else "#ffc107" if is_today and is_workout else "#007bff" if is_workout else "#e0e0e0"
        label = f"{workout_date.strftime('%a %b %d')}\n{'🟢 ' + default_val if is_workout else '💤 Rest'}"
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
            completed_val = progress.get(date_key, {}).get('completed', False)
            if st.checkbox("✅ Mark as completed", value=completed_val, key="completion_checkbox"):
                # Store as a dictionary with 'completed' and 'planned' keys
                planned_date = progress.get(date_key, {}).get('planned', base_date.strftime('%Y-%m-%d'))
                progress[date_key] = {'completed': True, 'planned': planned_date}
                # Auto-reschedule future workouts
                future_dates = recalculate_schedule(date_key, datetime.datetime.strptime(planned_date, "%Y-%m-%d").date(), workout_schedule, weekdays, progress)
                for k, v in future_dates.items():
                    if k != date_key:  # Skip the current workout
                        current_status = progress.get(k, {}).get('completed', False)
                        progress[k] = {'planned': v, 'completed': current_status}
                save_json("./data/progress.json", progress)
                st.success("Workout marked as completed and future dates rescheduled.")
            else:
                # If unchecked, preserve the planned date if it exists
                planned_date = progress.get(date_key, {}).get('planned', base_date.strftime('%Y-%m-%d'))
                progress[date_key] = {'completed': False, 'planned': planned_date}
                save_json("./data/progress.json", progress)
            if wk_name.startswith("Training"):
                # Enable date input for rescheduling
                current_date = base_date if not progress.get(date_key, {}).get("planned") else datetime.datetime.strptime(progress[date_key]["planned"], "%Y-%m-%d").date()
                edit_date = st.date_input("📅 New Training Date", value=current_date, key=f"date_{date_key}")
                if st.button("🔁 Reschedule from this workout", key=f"reschedule_{date_key}"):
                    future_dates = recalculate_schedule(date_key, edit_date, workout_schedule, weekdays, progress)
                    for k, v in future_dates.items():
                        if k == date_key:
                            progress[k] = {'planned': edit_date.strftime('%Y-%m-%d'), 'completed': progress.get(date_key, {}).get('completed', False)}
                        else:
                            current_status = progress.get(k, {}).get('completed', False)
                            progress[k] = {'planned': v, 'completed': current_status}
                    save_json("./data/progress.json", progress)
                    st.success("Future workouts rescheduled.")
            note_key = f"note_{date_key}"
            note = st.text_area("📝 Notes", value=notes.get(note_key, ""))
            if st.button("💾 Save Training"):
                notes[note_key] = note
                save_json("./data/notes.json", notes)
                st.success("Notes saved!")
            if st.button("❌ Close Workout"):
                st.session_state.selected_workout = None
                st.session_state.selected_date_key = None