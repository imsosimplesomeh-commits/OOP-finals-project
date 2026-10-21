# The Registry: Student Information and Grading System

Final project for CSPC 103 (Object Oriented Programming), Notre Dame of Marbel University.
Made by Stefan Zuri F. Modelo, BSCS 2.

A desktop app made with Python, Tkinter, and PostgreSQL. It manages students, teachers, subjects, class enrollment, scores, and grades, and it can export reports as PDF.

## Requirements

- Python 3.10 or higher
- PostgreSQL running on port 5432
- A database named `Modelo_CSPC103`

## How to Run

1. Create the database once (pgAdmin, or `psql -U postgres -c "CREATE DATABASE \"Modelo_CSPC103\";"`).
2. Install the packages:
```
   pip install -r requirements.txt
```
3. Set your PostgreSQL password. All connection settings live in `DB_CONFIG` in `db.py` and can be changed with the `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` and `PGPASSWORD` environment variables:
```
   set PGPASSWORD=your_password
```
4. Create the tables (runs `schema.sql`; safe to run again, existing rows are kept):
```
   python db.py
```
5. Start the app:
```
   python main.py
```

`seed_data.py` adds sample data. Skip it when running the CRUD test cases. The Reset Database button at the bottom right empties all tables, so you can start the test cases clean.

## Testing

- Unit tests for the grade math (SPEC numbers, both weight sets, PATHFIT example, scale boundaries, Midterm-only cases):
```
   python -m unittest discover tests
```
- `TEST_RUN_GUIDE.md` lists all 52 test cases in demo order with the data to type.
- `verify_appendix.sql` checks the database against the SPEC appendix after the full run (every line should say PASS):
```
   psql -U postgres -d Modelo_CSPC103 -f verify_appendix.sql
```
- `reset_for_demo.sql` empties every table and restarts ids, the same as the Reset Database button.
- `AUDIT.md` records the result of every test case with evidence.

## Support Files

- `SPEC.md` - the teacher's checklist (52 test cases, expected values, report layouts, expected tables)
- `schema.sql` - builds the empty database; `db.py` runs it
- `reset_for_demo.sql`, `verify_appendix.sql` - see Testing

## Features

- **Management:** add, edit, search, and delete students, teachers, and subjects
- **Classes and Enrollment:** create classes, set grading weights, and enroll students
- **Scores and Grades:** enter scores and see Midterm, Finals and Overall (percent and grade point), automatic Passed/Failed remarks and a Status; Overall = Midterm 40% + Finals 60%
- **Grading configuration:** each component shows its max score and its weight for the selected class, with a total per period
- **Audit Log:** every score, weight and grade change with who, old value, new value and when
- **Reports:** class list, grade sheet, and student grade report, exported as PDF

## Folders

- `models/` - classes for students, teachers, classes, and grades
- `repositories/` - database queries
- `services/` - grade computation, validation, and report logic
- `ui/` - the Tkinter tabs and theme

## Grade Rules

- Component percent = score / max score x 100; period grade = sum of component percent x weight / 100.
- The grade point is looked up from the unrounded percentage (96.99 is 1.25, 74.99 is 5.00). The scale lives only in `services/grade_calculator.py`.
- A period with a missing score or weights that do not total 100% is "Incomplete" (never counted as 0). A period with no components is "N/A".
- When Midterm is complete but Finals is not, Overall shows the Midterm percent with Status "Midterm only", and reports mark it with `*`. Set `SHOW_MIDTERM_ONLY_OVERALL = False` in `services/grade_calculator.py` to leave Overall blank instead.
- Remarks: 5.00 is Failed, anything else is Passed. They are computed, never typed.

## Grading Scale

| Grade | Range |
| --- | --- |
| 1.00 | 97 - 100 |
| 1.25 | 94 - 96.99 |
| 1.50 | 91 - 93.99 |
| 1.75 | 88 - 90.99 |
| 2.00 | 85 - 87.99 |
| 2.25 | 82 - 84.99 |
| 2.50 | 79 - 81.99 |
| 2.75 | 76 - 78.99 |
| 3.00 | 75 - 75.99 |
| 5.00 | below 75 (Failed) |