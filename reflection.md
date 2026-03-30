# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML design used four main classes: `Owner`, `Pet`, `Task`, and `Scheduler`. I wanted each class to represent one clear responsibility instead of mixing UI behavior with backend logic.

`Owner` stores the human-facing planning preferences, including daily time available and preferred task categories. `Pet` stores profile information and the list of tasks assigned to that animal. `Task` represents one unit of care with details like time, duration, priority, recurrence, and completion status. `Scheduler` acts as the coordinating layer that retrieves tasks from the owner's pets, sorts them, filters them, checks for conflicts, and generates a daily plan.

**b. Design changes**

Yes. During implementation I added a dedicated `ScheduleResult` wrapper and a `PlanItem` structure. My original design returned plain lists, but once I started connecting the backend to the Streamlit UI I realized I needed a cleaner way to carry selected tasks, skipped tasks, warnings, and minute totals together.

I also moved recurrence creation into the scheduler flow instead of keeping all of it inside the task itself. The `Task` still knows how to create its next occurrence, but the `Scheduler` decides when that should happen after a task is marked complete. That kept the design cleaner because the scheduler already owns task-management workflows.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

My scheduler considers the owner's available minutes for the day, each task's priority, task category preferences, recurrence frequency, completion state, and scheduled time. It also checks for exact-time conflicts so the user gets a warning when two tasks compete for the same slot.

I treated priority and time availability as the most important constraints because they directly affect what a busy pet owner can realistically complete. Preferences matter too, but I used them as a smaller score boost rather than letting them override essential care tasks.

**b. Tradeoffs**

One tradeoff is that conflict detection only flags exact matching times instead of calculating partial overlap based on duration. For example, a 7:30 AM task lasting 30 minutes and a 7:45 AM task would not currently be flagged as overlapping.

I think that tradeoff is reasonable for this project because it keeps the algorithm easy to understand, test, and explain while still catching the most obvious scheduling mistakes. If I had more time, overlap-aware conflict detection would be the next improvement.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI for design brainstorming, class-relationship planning, implementation support, test generation, and documentation drafting. The most helpful prompts were the ones that were specific about the design goal, such as asking how a scheduler should retrieve tasks from an owner's pets or how to structure recurring task logic without mixing too many responsibilities into one class.

AI was especially useful when I wanted a fast first draft for repetitive tasks like docstrings, tests, and UI wiring ideas. It helped me move faster, but I still had to decide which suggestions actually fit the architecture I wanted.

**b. Judgment and verification**

One moment where I did not accept an AI-style idea as-is was around making the scheduler score extremely complex, with multiple hidden heuristics. That would have made the app feel "smarter," but it also would have made the results harder to explain and debug.

I kept a simpler scoring model instead and verified it by running the CLI demo and automated tests. If the schedule output and tests matched the intended behavior, I treated that as evidence that the simpler design was the better choice for this assignment.

---

## 4. Testing and Verification

**a. What you tested**

I tested five core behaviors: marking a task complete, adding a task to a pet, sorting tasks in chronological order, generating the next occurrence for a daily task, and detecting conflicts when two tasks share the same time.

These tests were important because they cover the core promises of the system. If completion tracking fails, recurring tasks fail. If sorting fails, the schedule becomes confusing. If conflict detection fails, the user can miss collisions in their day. Together, these tests gave me confidence that the main planning flow works.

**b. Confidence**

I am moderately high in confidence, around 4 out of 5. The implemented behaviors work in the CLI demo, the tests are passing, and the Streamlit UI is successfully connected to the same backend logic.

If I had more time, I would test empty schedules, invalid time formats submitted through the UI, duplicate pet names entered repeatedly, tasks with durations longer than the entire daily time budget, and time overlaps based on duration rather than exact matching clock times.

---

## 5. Reflection

**a. What went well**

I am most satisfied with separating the backend logic from the UI. That made it much easier to test the scheduler in isolation first and then plug the same logic into Streamlit without rewriting core behavior.

**b. What you would improve**

In another iteration, I would improve task editing and deletion in the UI, add duration-aware conflict detection, and introduce a smarter rescheduling strategy for tasks that get skipped because of time limits.

**c. Key takeaway**

One important takeaway is that AI is most helpful when I use it like a fast collaborator, not an autopilot. The quality of the result depended on setting the structure, checking assumptions, and verifying behavior with tests instead of accepting every suggestion at face value.
