from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Iterable
from uuid import uuid4


PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1}
VALID_FREQUENCIES = {"once", "daily", "weekly"}


def _normalize_priority(priority: str) -> str:
    normalized = priority.strip().lower()
    if normalized not in PRIORITY_ORDER:
        raise ValueError(f"Unsupported priority: {priority}")
    return normalized


def _normalize_frequency(frequency: str) -> str:
    normalized = frequency.strip().lower()
    if normalized not in VALID_FREQUENCIES:
        raise ValueError(f"Unsupported frequency: {frequency}")
    return normalized


def _time_key(time_value: str) -> datetime:
    return datetime.strptime(time_value, "%H:%M")


@dataclass(slots=True)
class Task:
    """Represents one care task for a pet."""

    title: str
    time: str
    duration_minutes: int
    priority: str = "medium"
    frequency: str = "once"
    due_date: date = field(default_factory=date.today)
    category: str = "general"
    notes: str = ""
    completed: bool = False
    task_id: str = field(default_factory=lambda: uuid4().hex[:8])

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        self.time = self.time.strip()
        self.priority = _normalize_priority(self.priority)
        self.frequency = _normalize_frequency(self.frequency)
        self.category = self.category.strip().lower() or "general"
        self.notes = self.notes.strip()
        _time_key(self.time)
        if self.duration_minutes <= 0:
            raise ValueError("Task duration must be greater than zero.")

    def mark_complete(self) -> None:
        """Marks the task as completed."""

        self.completed = True

    def occurs_on(self, target_date: date) -> bool:
        """Returns True when the task is scheduled for the provided day."""

        return self.due_date == target_date

    def next_occurrence(self) -> Task | None:
        """Creates the next scheduled copy for recurring tasks."""

        if self.frequency == "once":
            return None

        delta = timedelta(days=1 if self.frequency == "daily" else 7)
        return Task(
            title=self.title,
            time=self.time,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            due_date=self.due_date + delta,
            category=self.category,
            notes=self.notes,
        )

    def to_row(self, pet_name: str) -> dict[str, str | int | bool]:
        """Returns a UI-friendly view of this task."""

        return {
            "Pet": pet_name,
            "Task": self.title,
            "Date": self.due_date.isoformat(),
            "Time": self.time,
            "Duration": self.duration_minutes,
            "Priority": self.priority.title(),
            "Frequency": self.frequency.title(),
            "Category": self.category.title(),
            "Completed": self.completed,
        }


@dataclass(slots=True)
class Pet:
    """Stores one pet and the tasks assigned to it."""

    name: str
    species: str
    age: int | None = None
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Adds a task to the pet."""

        self.tasks.append(task)

    def get_task(self, task_id: str) -> Task | None:
        """Finds a task by its unique identifier."""

        return next((task for task in self.tasks if task.task_id == task_id), None)

    def task_count(self) -> int:
        """Returns the number of tasks assigned to this pet."""

        return len(self.tasks)

    def tasks_for_day(self, target_date: date, include_completed: bool = False) -> list[Task]:
        """Returns tasks scheduled for a given day."""

        return [
            task
            for task in self.tasks
            if task.occurs_on(target_date) and (include_completed or not task.completed)
        ]


@dataclass(slots=True)
class Owner:
    """Represents the pet owner and their planning preferences."""

    name: str
    daily_available_minutes: int = 120
    preferred_categories: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.preferred_categories = [
            category.strip().lower()
            for category in self.preferred_categories
            if category.strip()
        ]
        if self.daily_available_minutes <= 0:
            raise ValueError("Daily available minutes must be greater than zero.")

    def add_pet(self, pet: Pet) -> None:
        """Adds a pet if it is not already tracked."""

        if self.get_pet(pet.name) is not None:
            raise ValueError(f"A pet named {pet.name} already exists.")
        self.pets.append(pet)

    def get_pet(self, pet_name: str) -> Pet | None:
        """Looks up a pet by name."""

        lowered_name = pet_name.strip().lower()
        return next((pet for pet in self.pets if pet.name.lower() == lowered_name), None)

    def add_task_to_pet(self, pet_name: str, task: Task) -> None:
        """Adds a task to the requested pet."""

        pet = self.get_pet(pet_name)
        if pet is None:
            raise ValueError(f"No pet named {pet_name} exists.")
        pet.add_task(task)

    def iter_tasks(
        self,
        target_date: date | None = None,
        include_completed: bool = True,
    ) -> Iterable[tuple[Pet, Task]]:
        """Yields every task, optionally scoped to a specific date."""

        for pet in self.pets:
            for task in pet.tasks:
                if target_date is not None and task.due_date != target_date:
                    continue
                if not include_completed and task.completed:
                    continue
                yield pet, task


@dataclass(slots=True)
class PlanItem:
    """One scheduled entry returned by the scheduler."""

    pet_name: str
    title: str
    date_label: str
    time: str
    duration_minutes: int
    priority: str
    frequency: str
    category: str
    reason: str

    def to_row(self) -> dict[str, str | int]:
        """Returns a table-friendly representation of the plan item."""

        return {
            "Pet": self.pet_name,
            "Task": self.title,
            "Date": self.date_label,
            "Time": self.time,
            "Duration": self.duration_minutes,
            "Priority": self.priority.title(),
            "Frequency": self.frequency.title(),
            "Category": self.category.title(),
            "Why it was chosen": self.reason,
        }


@dataclass(slots=True)
class ScheduleResult:
    """Wraps the selected plan, skipped tasks, and warnings."""

    plan_items: list[PlanItem]
    skipped: list[str]
    warnings: list[str]
    minutes_used: int
    minutes_remaining: int

    def as_rows(self) -> list[dict[str, str | int]]:
        """Converts the schedule to a list of dictionaries for display."""

        return [item.to_row() for item in self.plan_items]


class Scheduler:
    """Organizes, filters, and evaluates tasks across an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def sort_by_time(self, tasks: Iterable[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Sorts tasks chronologically, then by priority and title."""

        return sorted(
            tasks,
            key=lambda item: (
                _time_key(item[1].time),
                -PRIORITY_ORDER[item[1].priority],
                item[0].name.lower(),
                item[1].title.lower(),
            ),
        )

    def filter_tasks(
        self,
        *,
        pet_name: str | None = None,
        completed: bool | None = None,
        target_date: date | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Filters tasks by pet, completion state, and optionally date."""

        matches: list[tuple[Pet, Task]] = []
        normalized_pet = pet_name.strip().lower() if pet_name else None

        for pet, task in self.owner.iter_tasks(target_date=target_date, include_completed=True):
            if normalized_pet and pet.name.lower() != normalized_pet:
                continue
            if completed is not None and task.completed != completed:
                continue
            matches.append((pet, task))

        return self.sort_by_time(matches)

    def detect_conflicts(self, target_date: date) -> list[str]:
        """Returns warnings when multiple incomplete tasks share the same time."""

        schedule_by_time: dict[str, list[str]] = {}
        for pet, task in self.filter_tasks(target_date=target_date, completed=False):
            schedule_by_time.setdefault(task.time, []).append(f"{pet.name}: {task.title}")

        warnings: list[str] = []
        for time_label, entries in sorted(schedule_by_time.items(), key=lambda item: _time_key(item[0])):
            if len(entries) > 1:
                warnings.append(
                    f"Conflict at {time_label}: {', '.join(entries)} are all scheduled at the same time."
                )
        return warnings

    def mark_task_complete(self, pet_name: str, task_id: str) -> Task | None:
        """Marks a task complete and creates the next recurring instance if needed."""

        pet = self.owner.get_pet(pet_name)
        if pet is None:
            raise ValueError(f"No pet named {pet_name} exists.")

        task = pet.get_task(task_id)
        if task is None:
            raise ValueError(f"No task with id {task_id} exists for {pet_name}.")

        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            pet.add_task(next_task)
        return next_task

    def generate_daily_plan(self, target_date: date) -> ScheduleResult:
        """Builds a realistic plan that respects time, priority, and preferences."""

        candidates = self.filter_tasks(target_date=target_date, completed=False)
        warnings = self.detect_conflicts(target_date)

        scored_candidates = sorted(
            candidates,
            key=lambda item: (
                -self._task_score(item[1]),
                _time_key(item[1].time),
                item[0].name.lower(),
                item[1].title.lower(),
            ),
        )

        plan_items: list[PlanItem] = []
        skipped: list[str] = []
        minutes_remaining = self.owner.daily_available_minutes

        for pet, task in scored_candidates:
            if task.duration_minutes > minutes_remaining:
                skipped.append(
                    f"Skipped {task.title} for {pet.name} because only {minutes_remaining} minutes remained."
                )
                continue

            reason_parts = [
                f"{task.priority.title()} priority task",
                f"scheduled for {task.time}",
            ]
            if task.category in self.owner.preferred_categories:
                reason_parts.append("matches an owner preference")
            if task.frequency != "once":
                reason_parts.append(f"keeps the {task.frequency} routine on track")

            plan_items.append(
                PlanItem(
                    pet_name=pet.name,
                    title=task.title,
                    date_label=task.due_date.isoformat(),
                    time=task.time,
                    duration_minutes=task.duration_minutes,
                    priority=task.priority,
                    frequency=task.frequency,
                    category=task.category,
                    reason=", ".join(reason_parts),
                )
            )
            minutes_remaining -= task.duration_minutes

        plan_items.sort(key=lambda item: _time_key(item.time))

        return ScheduleResult(
            plan_items=plan_items,
            skipped=skipped,
            warnings=warnings,
            minutes_used=self.owner.daily_available_minutes - minutes_remaining,
            minutes_remaining=minutes_remaining,
        )

    def _task_score(self, task: Task) -> int:
        """Produces a simple score so the scheduler can choose tasks under time pressure."""

        score = PRIORITY_ORDER[task.priority] * 100
        if task.category in self.owner.preferred_categories:
            score += 25
        if task.frequency == "daily":
            score += 15
        elif task.frequency == "weekly":
            score += 10
        return score
