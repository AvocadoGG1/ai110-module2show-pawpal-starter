from __future__ import annotations

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule() -> None:
    """Runs a small CLI demo for the scheduler."""

    owner = Owner(
        name="Jordan",
        daily_available_minutes=75,
        preferred_categories=["exercise", "medication"],
    )

    mochi = Pet(name="Mochi", species="dog", age=4)
    luna = Pet(name="Luna", species="cat", age=7)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    today = date.today()
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
    luna.add_task(
        Task(
            title="Brush coat",
            time="19:00",
            duration_minutes=15,
            priority="medium",
            frequency="weekly",
            due_date=today,
            category="grooming",
        )
    )

    scheduler = Scheduler(owner)
    schedule = scheduler.generate_daily_plan(today)

    print(f"Today's Schedule for {owner.name}")
    print("-" * 72)
    for item in schedule.plan_items:
        print(
            f"{item.time} | {item.pet_name:<6} | {item.title:<15} | "
            f"{item.duration_minutes:>2} min | {item.reason}"
        )

    if schedule.warnings:
        print("\nWarnings")
        print("-" * 72)
        for warning in schedule.warnings:
            print(f"* {warning}")

    if schedule.skipped:
        print("\nSkipped")
        print("-" * 72)
        for skipped in schedule.skipped:
            print(f"* {skipped}")

    print("\nSummary")
    print("-" * 72)
    print(f"Minutes used: {schedule.minutes_used}")
    print(f"Minutes remaining: {schedule.minutes_remaining}")


if __name__ == "__main__":
    print_schedule()
