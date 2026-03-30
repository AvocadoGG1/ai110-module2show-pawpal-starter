from __future__ import annotations

from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")


def ensure_owner() -> Owner:
    """Creates the shared Owner object for the current session."""

    if "owner" not in st.session_state:
        st.session_state.owner = Owner(
            name="Jordan",
            daily_available_minutes=90,
            preferred_categories=["exercise", "medication"],
        )
    return st.session_state.owner


def build_scheduler() -> Scheduler:
    """Returns the scheduler for the current session."""

    return Scheduler(ensure_owner())


def seed_demo_data(owner: Owner) -> None:
    """Adds starter pets and tasks so the UI is useful on first load."""

    if owner.pets:
        return

    today = date.today()
    mochi = Pet(name="Mochi", species="dog", age=4, notes="Loves long walks.")
    luna = Pet(name="Luna", species="cat", age=7, notes="Needs evening medication.")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(
        Task(
            title="Morning walk",
            time="07:30",
            duration_minutes=25,
            priority="high",
            frequency="daily",
            due_date=today,
            category="exercise",
        )
    )
    mochi.add_task(
        Task(
            title="Breakfast",
            time="08:00",
            duration_minutes=10,
            priority="high",
            frequency="daily",
            due_date=today,
            category="feeding",
        )
    )
    luna.add_task(
        Task(
            title="Medication",
            time="08:00",
            duration_minutes=5,
            priority="high",
            frequency="daily",
            due_date=today,
            category="medication",
        )
    )


def owner_snapshot(owner: Owner) -> list[dict[str, str | int]]:
    """Builds a compact summary of the current pets."""

    return [
        {
            "Pet": pet.name,
            "Species": pet.species.title(),
            "Age": pet.age or "Unknown",
            "Tasks": pet.task_count(),
            "Notes": pet.notes or "-",
        }
        for pet in owner.pets
    ]


def all_task_rows(owner: Owner) -> list[dict[str, str | int | bool]]:
    """Returns all tasks in a display-friendly format."""

    rows: list[dict[str, str | int | bool]] = []
    for pet, task in Scheduler(owner).filter_tasks(completed=None):
        rows.append(task.to_row(pet.name))
    return rows


owner = ensure_owner()
seed_demo_data(owner)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;700&family=Manrope:wght@400;500;700&display=swap');
    html, body, [class*="css"] {
        font-family: "Manrope", sans-serif;
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(255, 214, 168, 0.45), transparent 28%),
            radial-gradient(circle at top right, rgba(95, 162, 141, 0.35), transparent 24%),
            linear-gradient(180deg, #fffaf2 0%, #f4efe6 100%);
        color: #243127;
    }
    h1, h2, h3 {
        font-family: "Fraunces", serif !important;
        letter-spacing: -0.02em;
        color: #223228;
    }
    .hero-card, .glass-panel {
        background: rgba(255, 251, 245, 0.82);
        border: 1px solid rgba(68, 86, 69, 0.12);
        border-radius: 22px;
        box-shadow: 0 18px 42px rgba(34, 50, 40, 0.08);
        padding: 1.2rem 1.3rem;
        backdrop-filter: blur(8px);
    }
    .metric-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.8rem;
        margin-top: 1rem;
    }
    .metric-chip {
        background: #f7efe1;
        border-radius: 18px;
        padding: 0.9rem 1rem;
        border: 1px solid rgba(68, 86, 69, 0.1);
    }
    .metric-chip strong {
        display: block;
        font-size: 1.4rem;
        color: #9b4d1d;
    }
    .caption-text {
        color: #5a695e;
        margin-top: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-card">
        <h1>🐾 PawPal+</h1>
        <p class="caption-text">
            A pet care planner that organizes routines by time, priority, owner preferences,
            recurring needs, and schedule conflicts.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

left_col, right_col = st.columns([1.2, 1], gap="large")

with left_col:
    st.markdown("### Owner Settings")
    with st.form("owner_form", clear_on_submit=False):
        owner_name = st.text_input("Owner name", value=owner.name)
        available_minutes = st.slider(
            "Daily time available (minutes)",
            min_value=15,
            max_value=240,
            value=owner.daily_available_minutes,
            step=15,
        )
        preferred_categories = st.multiselect(
            "Preferred task categories",
            ["exercise", "feeding", "medication", "grooming", "enrichment", "appointment"],
            default=owner.preferred_categories,
        )
        owner_saved = st.form_submit_button("Save owner settings")

    if owner_saved:
        owner.name = owner_name.strip() or "Jordan"
        owner.daily_available_minutes = available_minutes
        owner.preferred_categories = preferred_categories
        st.success("Owner settings updated.")

    st.markdown("### Add a Pet")
    with st.form("pet_form", clear_on_submit=True):
        pet_name = st.text_input("Pet name")
        species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
        age = st.number_input("Age", min_value=0, max_value=30, value=1)
        pet_notes = st.text_input("Notes")
        pet_saved = st.form_submit_button("Add pet")

    if pet_saved:
        try:
            owner.add_pet(
                Pet(
                    name=pet_name.strip(),
                    species=species,
                    age=int(age),
                    notes=pet_notes,
                )
            )
            st.success(f"Added {pet_name.strip()} to PawPal+.")
        except ValueError as exc:
            st.error(str(exc))

    st.markdown("### Add a Task")
    pet_names = [pet.name for pet in owner.pets]
    with st.form("task_form", clear_on_submit=True):
        selected_pet = st.selectbox("Pet", pet_names)
        task_title = st.text_input("Task title", value="Evening enrichment")
        task_date = st.date_input("Task date", value=date.today())
        task_time = st.text_input("Time (HH:MM)", value="18:30")
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)
        frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        category = st.selectbox(
            "Category",
            ["exercise", "feeding", "medication", "grooming", "enrichment", "appointment", "general"],
            index=4,
        )
        notes = st.text_input("Task notes")
        task_saved = st.form_submit_button("Add task")

    if task_saved:
        try:
            owner.add_task_to_pet(
                selected_pet,
                Task(
                    title=task_title,
                    time=task_time,
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                    due_date=task_date,
                    category=category,
                    notes=notes,
                ),
            )
            st.success(f"Added {task_title} for {selected_pet}.")
        except ValueError as exc:
            st.error(str(exc))

with right_col:
    st.markdown("### Care Overview")
    st.markdown(
        f"""
        <div class="glass-panel">
            <div class="metric-strip">
                <div class="metric-chip"><strong>{len(owner.pets)}</strong>Pets</div>
                <div class="metric-chip"><strong>{sum(pet.task_count() for pet in owner.pets)}</strong>Total tasks</div>
                <div class="metric-chip"><strong>{owner.daily_available_minutes}</strong>Minutes available</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if owner.pets:
        st.table(owner_snapshot(owner))

    st.markdown("### Current Tasks")
    rows = all_task_rows(owner)
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("Add a pet and a task to begin building the daily schedule.")

st.divider()

st.markdown("### Generate Daily Schedule")
schedule_date = st.date_input("Choose the day to plan", value=date.today(), key="schedule_date")
result = build_scheduler().generate_daily_plan(schedule_date)

summary_left, summary_right = st.columns([1.4, 1], gap="large")

with summary_left:
    if result.plan_items:
        st.success(
            f"Planned {len(result.plan_items)} task(s) using {result.minutes_used} minutes for {schedule_date.isoformat()}."
        )
        st.dataframe(result.as_rows(), use_container_width=True, hide_index=True)
    else:
        st.info("No tasks are due for the selected day.")

with summary_right:
    st.markdown("### Scheduler Notes")
    st.write(f"Minutes remaining: **{result.minutes_remaining}**")
    if result.warnings:
        for warning in result.warnings:
            st.warning(warning)
    else:
        st.caption("No timing conflicts detected.")

    if result.skipped:
        for skipped in result.skipped:
            st.info(skipped)
    else:
        st.caption("Nothing was skipped by the time-budget filter.")

st.markdown("### Complete a Task")
pending_tasks = [
    (pet.name, task)
    for pet, task in build_scheduler().filter_tasks(target_date=schedule_date, completed=False)
]
if pending_tasks:
    labels = {
        f"{pet_name} | {task.time} | {task.title}": (pet_name, task.task_id)
        for pet_name, task in pending_tasks
    }
    selected_label = st.selectbox("Pending tasks", list(labels.keys()))
    if st.button("Mark selected task complete"):
        pet_name, task_id = labels[selected_label]
        next_task = build_scheduler().mark_task_complete(pet_name, task_id)
        if next_task is None:
            st.success("Task marked complete.")
        else:
            st.success(
                f"Task marked complete. A new {next_task.frequency} occurrence was created for {next_task.due_date.isoformat()}."
            )
        st.rerun()
else:
    st.caption("No incomplete tasks remain for the selected day.")
