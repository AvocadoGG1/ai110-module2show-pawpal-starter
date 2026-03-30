from __future__ import annotations

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def build_scheduler() -> tuple[Owner, Pet, Scheduler]:
    """Creates a reusable owner, pet, and scheduler for tests."""

    owner = Owner(name="Jordan", daily_available_minutes=120, preferred_categories=["exercise"])
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    return owner, pet, Scheduler(owner)


def test_mark_complete_changes_status() -> None:
    _, pet, scheduler = build_scheduler()
    task = Task(title="Breakfast", time="08:00", duration_minutes=10)
    pet.add_task(task)

    scheduler.mark_task_complete("Mochi", task.task_id)

    assert task.completed is True


def test_adding_task_increases_pet_task_count() -> None:
    _, pet, _ = build_scheduler()

    pet.add_task(Task(title="Walk", time="07:30", duration_minutes=20))

    assert pet.task_count() == 1


def test_sorting_returns_tasks_in_chronological_order() -> None:
    _, pet, scheduler = build_scheduler()
    pet.add_task(Task(title="Dinner", time="18:00", duration_minutes=15))
    pet.add_task(Task(title="Walk", time="07:30", duration_minutes=20, priority="high"))
    pet.add_task(Task(title="Lunch", time="12:00", duration_minutes=10))

    ordered = scheduler.filter_tasks(target_date=date.today())

    assert [task.title for _, task in ordered] == ["Walk", "Lunch", "Dinner"]


def test_daily_recurrence_creates_next_day_task() -> None:
    _, pet, scheduler = build_scheduler()
    today = date.today()
    task = Task(
        title="Medication",
        time="09:00",
        duration_minutes=5,
        frequency="daily",
        due_date=today,
    )
    pet.add_task(task)

    next_task = scheduler.mark_task_complete("Mochi", task.task_id)

    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert pet.task_count() == 2


def test_conflict_detection_flags_duplicate_times() -> None:
    owner = Owner(name="Jordan")
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    today = date.today()
    mochi.add_task(Task(title="Walk", time="08:00", duration_minutes=20, due_date=today))
    luna.add_task(Task(title="Medication", time="08:00", duration_minutes=5, due_date=today))
    scheduler = Scheduler(owner)

    warnings = scheduler.detect_conflicts(today)

    assert len(warnings) == 1
    assert "Conflict at 08:00" in warnings[0]
