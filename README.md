# The Registry: Student Information and Grading System

Final project for CSPC 103 (Object Oriented Programming), Notre Dame of Marbel University.
Made by Stefan Zuri F. Modelo, BSCS 2.

A desktop app made with Python, Tkinter, and PostgreSQL. It manages students, teachers, subjects, class enrollment, scores, and grades, and it can export reports as PDF.

## Requirements

- Python 3.10 or higher
- PostgreSQL running on port 5432
- A database named `Modelo_CSPC103`

## How to Run

1. Install the packages:
```
   pip install -r requirements.txt
```
2. Set your PostgreSQL password (the other connection settings use the defaults in `db.py`):
```
   set PGPASSWORD=your_password
```
3. Create the tables:
```
   python db.py
```
4. Start the app:
```
   python main.py
```

`seed_data.py` adds sample data. Skip it when running the CRUD test cases. The Reset Database button at the bottom right empties all tables, so you can start the test cases clean.

## Features

- **Management:** add, edit, search, and delete students, teachers, and subjects
- **Classes and Enrollment:** create classes, set grading weights, and enroll students
- **Scores and Grades:** enter scores, then compute midterm, finals, and final grades
- **Reports:** class list, grade sheet, and student grade report, exported as PDF

## Folders

- `models/` - classes for students, teachers, classes, and grades
- `repositories/` - database queries
- `services/` - grade computation, validation, and report logic
- `ui/` - the Tkinter tabs and theme

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