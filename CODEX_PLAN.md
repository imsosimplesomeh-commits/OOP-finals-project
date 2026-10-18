# Codex plan - do these in order, one prompt per step, commit after each

Open the repo in Codex (or ChatGPT with the zip), make sure AGENTS.md is in the repo root.
Paste ONE step at a time. After each step run the tests, then `git commit`.
If Codex changes more than the step asks, say: "undo everything outside this step".

## Step 1 - remove the secret and dead files
"Read AGENTS.md. In db.py remove the hard-coded database password and read it from the PGPASSWORD
environment variable (or a .env file ignored by git). Delete the unused old files student_app.py,
crud_tab.py, config.py and the student_grades.db file. Do not change anything else."

## Step 2 - schema that matches the checklist (biggest point gain)
"Rewrite init_db() in db.py so the 11 tables match the Appendix of the CRUD test case document:
students(student_id TEXT PK, first_name, last_name, email NULL, program, year_level, status),
teachers(teacher_id TEXT PK, ... department ...), subjects, class_offerings, enrollments,
grading_periods(+period_order), grade_components(period_id FK, name, type, max_score, description),
grade_percentages(class_id FK, component_id FK, percentage, UNIQUE(class_id, component_id)),
grade_component_scores, grades(midterm_grade, finals_grade, overall_grade, midterm_equiv,
final_equiv, remarks, date_encoded, one row per enrollment), audit_log. Use ON DELETE RESTRICT on
every parent link. Update models/ and the repositories to match. Keep SQL parameterized."

## Step 3 - swap in the verified calculator
"Rename services/grade_calculator_v2.py to services/grade_calculator.py. Update grading_service.py
to: load the six component weights of the class from grade_percentages, build (score, max, weight)
lists per period, call GradeCalculator, and UPSERT one grades row per enrollment with the percentages
AND the grade-point equivalents. Missing score -> store NULL and show 'Incomplete'.
tests/test_grade_numbers.py must pass unchanged."

## Step 4 - validation + safe deletes in services
"Add the validations from the 'Hard rules' list in AGENTS.md to the services (duplicate ids, blank
required fields, positive units, weights total 100 per period, negative or blank weight, score range,
duplicate enrollment, unknown student, score only for enrolled student, delete blocked when children
exist with a message that names the dependency). The forms only call services and show the message."

## Step 5 - audit log
"Write an AuditRepository and call it from the score, weight, and grade save/delete methods inside the
same transaction. Log old and new values."

## Step 6 - reports + PDF
"Rewrite ReportService queries to return exactly the three layouts in the checklist (Class List,
Grade Sheet with MG and FG, Student Grade with Units, F Grade, Total Units, No. of Subjects, GWA).
Sort by last name, first name. No SQL inside the service: add report methods to the repositories.
Add an Export PDF button to the Reports tab using reportlab."

## Step 7 - rehearsal
"Create tests/test_checklist_flow.py that runs ST-01 to PS-02 in order against a TEST database
(env var PGDATABASE_TEST) using the services (no GUI), and checks the row counts in the Appendix
('Row counts' table). Then give me a list of any test case that fails."

## Before the demo (you, not Codex)
1. Create a fresh empty database, run `python db.py`, do NOT run seed_data.py.
2. Open pgAdmin on the same database. Run the checklist in order, type the data exactly as written.
3. Print the checklist and the three reports as PDF.
