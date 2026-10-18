# AGENTS.md - read this before touching the project

Project: CSPC 103 Finals - Student Grade Management System (Python, Tkinter, PostgreSQL).
Checked by: a live demo using the 52-case CRUD checklist (100 pts). The tester compares the
database tables with the checklist, so the schema and the numbers must match exactly.

## Code style (important)
- Write like a first-year BSCS student, not like a framework. Simple names, short functions.
- Short lowercase comments that explain WHY, no long docstrings, no emojis, no marketing words.
- No clever tricks (no metaclasses, decorators, or generic base-class magic). Plain classes, plain SQL.
- One job per file: ui/ draws forms, services/ validates + decides, repositories/ runs SQL,
  grade_calculator.py does the math. UI never writes SQL. Repositories never compute grades.
- All SQL uses %s parameters. Never put user input inside an f-string SQL.
- Show friendly messages (messagebox) for every rejected action. Never show a raw psycopg2 error.
- Do not add libraries other than psycopg2-binary and reportlab (for PDF).

## Hard rules from the checklist
- Keys are text: student_id like "2026-0001", teacher_id like "T-1001". Duplicates rejected.
- email is optional (the test data has none). year_level is required for students.
- Grade scale lives ONLY in services/grade_calculator_v2.py (GRADE_SCALE). Use the UNROUNDED percentage.
- Weights are per component per class (GRADE_PERCENTAGE: class_id, component_id, percentage).
  Each grading period's weights must total 100 or the save is rejected. Never hard-code 20/30/50.
- Overall = Midterm x 40% + Finals x 60%. Raw scores are never changed by recalculation.
- A missing score = "Incomplete", never 0.
- Do not delete a parent that has children: student with enrollment, teacher with class, subject with
  class, class with enrollments, component with scores, enrollment with scores. Show a message that
  names the dependency. Use ON DELETE RESTRICT, no CASCADE on these.
- Duplicate enrollment (same student + class) rejected. Score only allowed for an enrolled student.
- Grade rows: one per enrollment, updated on recompute (UPSERT), never duplicated.
- Every change to scores, weights, and grades writes an AUDIT_LOG row (table_name, record_id, action,
  old_value, new_value, changed_by, changed_at).
- Reports come from saved data only, students sorted by last name then first name, layouts exactly as
  in the checklist ("Expected report layouts"). Every report needs an "Export PDF" button.
- Student Grade report: GWA = sum(F Grade x units) / total units, two decimals (2.05 for the sample).

## Definition of done
- `python -m unittest discover` passes (tests/test_grade_numbers.py must stay green).
- `python db.py` creates 11 tables on an EMPTY database. `seed_data.py` is optional and must never run automatically.
- No password in source. Read PGPASSWORD / a .env file that is in .gitignore.
