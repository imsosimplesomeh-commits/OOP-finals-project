# Test Run Guide

Rehearsal sheet for the live demonstration. Run the cases top to bottom in this order: some cases say "after X" and are run at that point, because later cases need records made earlier.

## Before you start

1. Empty the database: click **Reset Database** (bottom right) and answer Yes, or run `psql -U postgres -d Modelo_CSPC103 -f reset_for_demo.sql`. Do not run `load_demo_data.py`.
2. Start the app: `python main.py`.
3. Open pgAdmin on `Modelo_CSPC103` (Schemas > public > Tables) so the tester can watch each table.
4. Tabs: **I Records** (Students / Teachers / Subjects), **II Classes**, **III Grades**, **IV Reports**, **V Audit Log**. To edit or delete, click the row first.

## Part A. Master records and enrollment

| Test | Where | Type or do | Expect |
| --- | --- | --- | --- |
| ST-01 | Records > Students > Add | 2026-0001 Juan Dela Cruz BSCS 2; 2026-0002 Pedro Reyes BSCS 2; 2026-0003 Ana Garcia BSIT 2 (Clear between) | "Student saved." each time; 3 rows in list |
| ST-02 | Students > Add | 2026-0001 again | "That student number already exists." |
| ST-03 | Students > Add | Blank name, then blank number | "First name is required." / "Student number is required." |
| ST-04 | Students > Search | Reyes, Search, click Pedro | Pedro's details in the form |
| ST-05 | Students > Update | Click Ana, Program BSCS, Update; View All, click Ana | Program BSCS, other fields unchanged |
| ST-06 | Students > Add, Delete | 2026-0099 Lea Ramos BSIT 1; click row, Delete, Yes | Confirmation, then row gone |
| TE-01 | Records > Teachers > Add | T-1001 Maria Santos, Computer Studies Department | "Teacher saved." |
| TE-02 | Teachers > Add | T-1001 again; then a blank name | "That teacher ID already exists." / "First name is required." |
| TE-03 | Teachers > View | Click T-1001 | Details shown |
| TE-04 | Teachers > Update | Department: Information Technology Department | Saved and shown |
| SU-01 | Records > Subjects > Add | CSPC 103, Object Oriented Programming, 3 | "Subject saved." |
| SU-02 | Subjects > Add | CSPC 103 again; then units 0, then -2 | "That subject code already exists." / "Units must be a positive whole number." |
| SU-03 | Subjects > View | Show the list | CSPC 103 with details |
| SU-04 | Subjects > Update | Description: Object-oriented analysis, design and programming in Java | Saved and shown |
| SU-05 (part 1) | Subjects > Add, Delete | TMP 101 Temporary 1; Delete, Yes | Deleted |
| CL-01 | Classes > Add Class | Code CSPC103-A, CSPC 103, Santos, Section A, MWF 9:00-10:00, CS-201, 2026-2027, 1st | "Class saved." |
| TE-05 | Teachers > Delete | Click T-1001, Delete, Yes | "Cannot delete this teacher because class CSPC103-A depends on it." |
| SU-05 (part 2) | Subjects > Delete | Click CSPC 103, Delete, Yes | Blocked, names CSPC103-A |
| CL-02 | Classes > Add Class | Clear; no teacher; then no subject; then no school year | "... is required." each time |
| CL-03 | Classes > Filter by Teacher | Pick Santos, Maria | Only CSPC103-A with subject, section, schedule, room, term; then pick All teachers |
| CL-04 | Classes > Update Class | Click class; Room CS-202, Schedule TTh 1:00-2:30 | Saved, shown after reopen |
| EN-01 | Classes > Enroll Student | Click class; pick Juan, Pedro, Ana one by one | "Successfully enrolled ..." x3 |
| ST-07 | Students > Delete | Click Juan, Delete, Yes | "Cannot delete this student because enrollments depend on it." |
| CL-05 | Classes > Delete Class | Click class, Delete, Yes | "Cannot delete this class because enrollments depend on it." |
| EN-02 | Classes > Enroll Student | Juan again | "... is already enrolled in CSPC103-A." |
| EN-03 | Classes > Enroll Student | Type 2026-9999 | "Student with ID '2026-9999' does not exist." |
| EN-04 | Classes | Click class | Juan, Pedro, Ana with status |
| EN-05 | Classes > Drop Selected, Restore | Click Pedro, Drop; then Restore | "Enrollment status set to Dropped." / "...Enrolled." |
| EN-06 (part 1) | Students > Add, then Classes > Remove | 2026-0098 Carlo Mendoza BSIT 1; enroll; Remove, Yes | "Enrollment removed." |

## Part B. Grading, reports, persistence

| Test | Where | Type or do | Expect |
| --- | --- | --- | --- |
| GP-01 | Classes > Add Period | Midterm 1; Finals 2 | "Grading period added." |
| GC-01 | Classes > Add Component | Midterm Quiz 50, Midterm Laboratory/Project 100, Midterm Examination 100, Final Quiz 50, Final Laboratory/Project 100, Final Examination 100 (pick period and category) | 6 rows; Weight column shows "-" |
| GW-01 | Classes > Save Weights | Click class; Period Midterm 20 / 30 / 50, Save; Period Finals 20 / 30 / 50, Save | "Period weights saved."; Weight column 20/30/50, "Midterm total 100.00%" |
| GW-02 | Classes > Save Weights | Midterm 20 / 30 / 40 | "Weights total 90%, they must total 100%."; boxes reload 20 / 30 / 50 |
| GW-03 | Classes > Save Weights | -20 in one box; then one box blank | "Weight cannot be negative." / "Enter a number for weight." |
| GC-02 | Classes | Click class | Period, Component, Max Score, Weight (%) and a total per period |
| SC-01 | Grades > Save Score | Pick student and component ("Midterm Quiz (/50 - 20%)"), type score. Juan 40 90 **57** 45 85 80; Pedro 20 60 55 30 70 65; Ana 50 100 100 48 95 92 | "Score saved." x18 |
| GC-03 | Classes > Delete Component | Click Midterm Quiz, Delete, Yes | "Cannot delete Midterm Quiz because 3 score(s) depend on it." |
| EN-06 (part 2) | Classes > Remove | Click Juan, Remove, Yes | "Cannot remove this enrollment because scores depend on it." |
| SC-02 | Grades > Save Score | Pedro, Midterm Quiz, 55 | "Score 55 is above the maximum of 50." |
| SC-03 | Grades > Save Score | Any component, -5 | "Score cannot be negative." |
| SC-04 | Grades > Save Score | Type 2026-0098 in Student, Midterm Quiz, 10 | "'2026-0098' is not enrolled in this class, so no score can be saved." |
| SC-05 | Grades | Switch tab and back, pick each student | All scores reload |
| SC-06 | Grades > Save Score | Juan, click Midterm Examination row, 75, Save | Same row updated |
| GR-01 | Grades > Compute All | | Midterm % 80.50 / 53.50 / 100.00, Midterm GP 2.50 / 5.00 / 1.00 |
| GR-02 | Grades (same table) | | Finals % 83.50 / 65.50 / 93.70, Finals GP 2.25 / 5.00 / 1.50; Overall % 82.30 / 60.70 / 96.22, Overall GP 2.25 / 5.00 / 1.25; Passed / Failed / Passed; Status Complete |
| SC-07 | Grades > Delete, Save Score | Ana, click Final Quiz row, Delete, Yes; then 48 again | Finals "Incomplete", Status "Midterm only"; after 48: 93.70, Complete |
| GR-03 | Classes > Save Weights, Grades > Compute All | Midterm 30 / 30 / 40; recompute | Juan 81.00 / 82.50, Pedro 52.00 / 60.10, Ana 100.00 / 96.22 |
| GR-04 | V Audit Log > Refresh | | Newest first: GRADE and GRADE_PERCENTAGE updates, score 57 to 75, who and when |
| RP-01 | Reports > View Report | Class List, CSPC103-A | Header with IT Department, TTh 1:00-2:30, CS-202; Dela Cruz, Garcia, Reyes |
| RP-02 | Reports > View Report | Grade Sheet, CSPC103-A | 2.50 / 2.25, 1.00 / 1.25, 5.00 / 5.00 |
| Setup | Records, Classes, Grades | T-1002 Jose Ramos, Physical Education Department; PATHFIT 3, Physical Activity Towards Health and Fitness 3, 2; class PATHFIT3-A, Ramos, A, TTh 3:00-5:00, Gym; enroll Juan; weights 20/30/50 both periods; Juan 45 90 90 45 90 90; Compute All | 90.00, 1.75, Passed |
| RP-03 | Reports > View Report | Student Grade Report, Juan | CSPC 103 ... 3 2.25; PATHFIT 3 ... 2 1.75 |
| RP-04 | Reports | Read the summary | Total Units 5, No. of Subjects 2, GWA 2.05 |
| PS-02 | Students > Add, Search | 2026-0004 Kevin O'Brien BSIT 1; search `' OR '1'='1` | Saved; empty list, no error |
| PS-01 | Close the app, `python main.py` | Reports > Grade Sheet | Same grades |

## After the run

`psql -U postgres -d Modelo_CSPC103 -f verify_appendix.sql` checks row counts, expected rows, audit entries and the rows that must not exist. Every line should say PASS.

## If the teacher asks about a missing Finals

A class with Midterm weights and scores but no Finals shows Finals "Incomplete" (or "N/A" when the period has no components), Overall equal to the Midterm percent, and Status "Midterm only". Reports mark that grade with `*` and the note "* Midterm only". Set `SHOW_MIDTERM_ONLY_OVERALL = False` in `services/grade_calculator.py` to leave Overall blank instead.
