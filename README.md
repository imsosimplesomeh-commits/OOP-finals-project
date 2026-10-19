# Student Information and Grading System

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
| 1.00 | 98 - 100 |
| 1.25 | 95 - 97.9 |
| 1.50 | 92 - 94.9 |
| 1.75 | 89 - 91.9 |
| 2.00 | 86 - 88.9 |
| 2.25 | 83 - 85.9 |
| 2.50 | 80 - 82.9 |
| 2.75 | 77 - 79.9 |
| 3.00 | 75 - 76.9 |
| 5.00 | below 75 (Failed) |