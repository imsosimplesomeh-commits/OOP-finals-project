# Student Information and Grading System

Final project for **CSPC 103 — Object Oriented Programming**  
Notre Dame of Marbel University — CEAC  
**Instructor:** Mrs. Brenda M. Balala, MIT  

---

## Overview

A desktop grading system built with Python, Tkinter, and PostgreSQL (`psycopg2`). It handles student records, class offerings, raw score entry, and automatic grade computation using the standard collegiate rating scale (1.00 to 5.00).

The project separates responsibilities cleanly:

* `models/`: Data definitions for students, teachers, classes, and grades.
* `repositories/`: Database queries and CRUD operations using parameterized PostgreSQL SQL.
* `services/`: Grade calculations, period weighting, and report generation.
* `ui/`: Tkinter interface divided into four functional tabs.

---

## Prerequisites

* Python 3.10 or higher
* PostgreSQL 14+ installed and running locally on port 5432
* pgAdmin 4 (recommended for database management)

---

## Database Setup (pgAdmin / PostgreSQL)

1. Open **pgAdmin 4** and connect to your local PostgreSQL server (default port `5432`, user `postgres`).
2. In the Object Explorer on the left, right-click **Databases** > **Create** > **Database...**.
3. Name the database **`Modelo_CSPC103`** and click **Save**.
4. *(Optional)* If your PostgreSQL password differs from the default in `db.py`, set environment variables:
   * `PGHOST`: `localhost`
   * `PGPORT`: `5432`
   * `PGDATABASE`: `Modelo_CSPC103`
   * `PGUSER`: `postgres`
   * `PGPASSWORD`: `<your_password>`

---

## Installation & Quick Start

1. **Install required dependencies:**
```bash
pip install -r requirements.txt
```

2. **Initialize database tables:**
```bash
python db.py
```
*Creates all tables with `SERIAL PRIMARY KEY` and foreign key relationships in `Modelo_CSPC103`.*

3. **Seed sample data (optional, skip this for the CRUD checklist):**
```bash
python seed_data.py
```
*Populates the database with subjects, teachers, class offerings, grading periods, enrollments, and realistic distinct scores for Midterm and Finals.*

4. **Launch the application:**
```bash
python main.py
```

5. **Run automated test cases:**
```bash
python test_system.py
```

---

## Features

* **Tab 1: Management** — Add, edit, search, and delete students, faculty, and academic subjects.
* **Tab 2: Class Offerings & Enrollment** — Set up classes, assign teachers, configure component percentage weights (quizzes, labs, exams), and enroll students.
* **Tab 3: Score Entry & Calculations** — Record component scores per student, compute weighted midterm and final grades, and calculate final ratings.
* **Tab 4: Reports** — Generate printable class rosters, official grade sheets, and individual student grade summaries with text and table export.

## PDF reports and a clean test database

In Reports, choose Class List, Grade Sheet, or Student Grade Report. Choose the class or student,
click Generate Report, then Export PDF. Choose where to save the file. Open the PDF to print it.

Use Reset Database at the bottom right before starting the CRUD checklist. Read the database name
in the confirmation, then choose Yes. This permanently clears all 11 project tables, including the
audit log, and restarts generated IDs. No is selected by default. The forms reload empty after a reset.
Normal Delete buttons still protect records that have dependents.

---

## Grading Scale (Philippine / NDMU Collegiate Standard)

* `98.0 – 100.0` : **1.00** (PASSED)
* `95.0 – 97.9` : **1.25** (PASSED)
* `92.0 – 94.9` : **1.50** (PASSED)
* `89.0 – 91.9` : **1.75** (PASSED)
* `86.0 – 88.9` : **2.00** (PASSED)
* `83.0 – 85.9` : **2.25** (PASSED)
* `80.0 – 82.9` : **2.50** (PASSED)
* `77.0 – 79.9` : **2.75** (PASSED)
* `75.0 – 76.9` : **3.00** (PASSED)
* `Below 75.0` : **5.00** (FAILED)

---

## File Structure

```
finals-project-student_gui/
├── db.py                 # PostgreSQL connection and table schemas
├── main.py               # Main application GUI entry point
├── requirements.txt      # Python dependencies (psycopg2-binary)
├── seed_data.py          # PostgreSQL sample data loader
├── test_system.py        # Automated unit and integration tests
├── models/               # Domain classes
├── repositories/         # PostgreSQL repositories (parameterized SQL)
├── services/             # Calculation and report logic
└── ui/                   # Tkinter GUI tabs
```
