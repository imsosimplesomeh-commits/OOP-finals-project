> SPEC.md: exact text copy of the teacher docx "CSPC 103 Finals Project - CRUD Test Case Scenarios (100 pts)". Source of truth. Do not edit.

CSPC 103 — Finals Project | Student Grade Management System | Advanced OOP Design, Refactoring & Persistence

	JMJ MARIST BROTHER                                                                Documentation on GUI Program

	Notre Dame of Marbel University	1st Semester SY 2026-2027

	City of Koronadal	  Mrs. Brenda M. Balala, MIT

**Object Oriented Programming**

**CSPC 103**

Student name:   _______________________________________________          Score: ___________________

**FINALS PROJECT**

**CRUD Test Case Scenarios (100 points)**

*Student Grade Management System · Live Demonstration Checklist*

**SDG 4 Quality ****Education  |****  CLO 3 ****&**** 4 — OOP System Design and Implementation**

## How to Use This Checklist

The 52 test cases total 100 points. Run them in order during the live demonstration, because later cases depend on records created earlier.

**Scoring rule for each test case**

- **Full points:** the system behaves exactly as stated in Expected Result, and the effect is visible in the UI and in the database.

- **Half points:** the operation works, but with a defect such as a missing confirmation, an unclear error message, or a result shown in the UI but not saved.

- **Zero:** the operation fails, crashes, or accepts data it should reject.

**Before testing**

- The student starts the application on a fresh copy of its database with the schema and no sample records, or deletes the sample records first.

- The tester keeps the database open in a client (e.g., MySQL Workbench, phpMyAdmin, DBeaver, or PostgreSQL) to confirm each change in the tables.

- Enter the test data exactly as written in the next section, so the computed grades can be checked against the expected values.

**Legend:** C = Create, R = Read, U = Update, D = Delete, V = Validation (a negative test the system must reject).

## Test Data

Use these records in every test so the computed grades can be checked against the expected values below.

**Master records**

| Record | Values to enter |
| --- | --- |
| Teacher | T-1001, Maria Santos, Computer Studies Department |
| Subject | CSPC 103, Object Oriented Programming, 3 units |
| Class | CSPC 103 – Section A, SY 2026-2027, 1st Semester, MWF 9:00–10:00, Room CS-201, teacher T-1001 |
| Student 1 | 2026-0001, Juan Dela Cruz, BSCS, 2nd year |
| Student 2 | 2026-0002, Pedro Reyes, BSCS, 2nd year |
| Student 3 | 2026-0003, Ana Garcia, BSIT, 2nd year |
| Student 4 | 2026-0004, Kevin O'Brien, BSIT, 1st year (added in PS-02) |
| Temporary students | 2026-0099, Lea Ramos, BSIT, 1st year (ST-06, deleted); 2026-0098, Carlo Mendoza, BSIT, 1st year (EN-06, kept but not enrolled) |

**Grading configuration for CSPC 103 – A**

| Period | Component | Max score | Weight |
| --- | --- | --- | --- |
| Midterm | Midterm Quiz | 50 | 20% |
| Midterm | Midterm Laboratory/Project | 100 | 30% |
| Midterm | Midterm Examination | 100 | 50% |
| Finals | Final Quiz | 50 | 20% |
| Finals | Final Laboratory/Project | 100 | 30% |
| Finals | Final Examination | 100 | 50% |

Overall grade = Midterm × 40% + Finals × 60%.

**Raw scores**

| Student | Mid Quiz (/50) | Mid Lab (/100) | Mid Exam (/100) | Final Quiz (/50) | Final Lab (/100) | Final Exam (/100) |
| --- | --- | --- | --- | --- | --- | --- |
| Juan Dela Cruz | 40 | 90 | 75 | 45 | 85 | 80 |
| Pedro Reyes | 20 | 60 | 55 | 30 | 70 | 65 |
| Ana Garcia | 50 | 100 | 100 | 48 | 95 | 92 |

**Expected computed grades** (component grade = score ÷ max × 100; then weighted)

| Student | Midterm | Finals | Overall | After recalculation (Midterm weights 30/30/40): Midterm | After recalculation: Overall |
| --- | --- | --- | --- | --- | --- |
| Juan Dela Cruz | 80.50 | 83.50 | 82.30 | 81.00 | 82.50 |
| Pedro Reyes | 53.50 | 65.50 | 60.70 | 52.00 | 60.10 |
| Ana Garcia | 100.00 | 93.70 | 96.22 | 100.00 | 96.22 |

Worked example for Juan's Midterm: (40/50 × 100) × 20% + 90 × 30% + 75 × 50% = 16 + 27 + 37.5 = 80.50. Accept differences of ±0.01 from rounding. Each percentage is then converted to a grade point with the scale below, and the remarks follow from the grade point.

**Grade-point equivalent scale**

Every computed percentage (Midterm, Finals and Overall) is converted to a grade point. Look up the unrounded percentage; for example 96.99 is 1.25 and 74.99 is 5.00. Keep the scale in one place (a lookup table or the GradeCalculator), not in the forms.

| Percentage | Grade point | Remarks |
| --- | --- | --- |
| 97.00 – 100.00 | 1.00 | Passed |
| 94.00 – 96.99 | 1.25 | Passed |
| 91.00 – 93.99 | 1.50 | Passed |
| 88.00 – 90.99 | 1.75 | Passed |
| 85.00 – 87.99 | 2.00 | Passed |
| 82.00 – 84.99 | 2.25 | Passed |
| 79.00 – 81.99 | 2.50 | Passed |
| 76.00 – 78.99 | 2.75 | Passed |
| 75.00 – 75.99 | 3.00 | Passed |
| Below 75.00 | 5.00 | Failed |

**Expected grade points** (the percentages above converted with the scale)

| Student | Midterm | Finals | Overall | Remarks | After recalc: Midterm | After recalc: Overall | Remarks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Juan Dela Cruz | 2.50 | 2.25 | 2.25 | Passed | 2.50 | 2.25 | Passed |
| Pedro Reyes | 5.00 | 5.00 | 5.00 | Failed | 5.00 | 5.00 | Failed |
| Ana Garcia | 1.00 | 1.50 | 1.25 | Passed | 1.00 | 1.25 | Passed |

**Report setup records** (entered just before Part B4, so the Student Grade report has two subjects with different units)

| Record | Values to enter |
| --- | --- |
| Teacher 2 | T-1002, Jose Ramos, Physical Education Department |
| Subject 2 | PATHFIT 3, Physical Activity Towards Health and Fitness 3, 2 units |
| Class 2 | PATHFIT 3 – Section A, SY 2026-2027, 1st Semester, TTh 3:00–5:00, Gym, teacher T-1002 |
| Enrollment | Juan Dela Cruz (2026-0001) only, status Enrolled |
| Weights | Same components as CSPC 103; 20/30/50 for both Midterm and Finals; Overall = Midterm × 40% + Finals × 60% |
| Juan's scores | Mid Quiz 45, Mid Lab 90, Mid Exam 90, Final Quiz 45, Final Lab 90, Final Exam 90 |
| Expected grades | Midterm 90.00 (1.75), Finals 90.00 (1.75), Overall 90.00 → Final Grade 1.75, Passed |

## Part A. Master Records and Enrollment (50 points)

### A1. Student (12 points)

| TC | Type | Scenario and steps | Expected result | Pts | Score |
| --- | --- | --- | --- | --- | --- |
| ST-01 | C | Add Juan, Pedro and Ana from the test data. | Each student is saved, shown in the list, and appears as a row in STUDENT. | 2 |  |
| ST-02 | V | Add another student with number 2026-0001. | Rejected with a clear duplicate message; no second row in STUDENT. | 2 |  |
| ST-03 | V | Save a student with the name or student number left blank. | Rejected with a required-field message; nothing saved. | 1 |  |
| ST-04 | R | Search for "Reyes", then open Pedro's record. | Pedro is found and his saved details are shown correctly. | 2 |  |
| ST-05 | U | Change Ana's program from BSIT to BSCS, save, close and reopen her record. | The new program is shown and saved in STUDENT; other fields unchanged. | 2 |  |
| ST-06 | D | Add the temporary student 2026-0099 (Lea Ramos), then delete it after confirming. | The system asks for confirmation; the record disappears from the list and from STUDENT. | 1 |  |
| ST-07 | V | Run after EN-01. Try to delete Juan, who has an enrollment. | Deletion is blocked (or requires an explicit, documented safe action); his enrollment and scores are not lost. | 2 |  |

### A2. Teacher (8 points)

| TC | Type | Scenario and steps | Expected result | Pts | Score |
| --- | --- | --- | --- | --- | --- |
| TE-01 | C | Add teacher T-1001, Maria Santos, Computer Studies Department. | Saved and listed; row appears in TEACHER. | 2 |  |
| TE-02 | V | Add another teacher with ID T-1001, or with a blank name. | Rejected with a clear message; nothing saved. | 1 |  |
| TE-03 | R | Open the teacher list and view T-1001. | Details are shown correctly. | 1 |  |
| TE-04 | U | Change Maria Santos's department to Information Technology Department, save and reopen. | The change is saved and shown; it also appears in the Class List header (RP-01). | 2 |  |
| TE-05 | V | Run after CL-01. Try to delete T-1001, who handles a class. | Deletion is blocked with a message naming the dependent class. | 2 |  |

### A3. Subject (8 points)

| TC | Type | Scenario and steps | Expected result | Pts | Score |
| --- | --- | --- | --- | --- | --- |
| SU-01 | C | Add CSPC 103, Object Oriented Programming, 3 units. | Saved and listed; row appears in SUBJECT. | 2 |  |
| SU-02 | V | Add a subject with code CSPC 103 again, then one with 0 or negative units. | Both are rejected with clear messages. | 2 |  |
| SU-03 | R | View the subject catalog. | CSPC 103 is listed with correct details. | 1 |  |
| SU-04 | U | Edit the description of CSPC 103 to “Object-oriented analysis, design and programming in Java” and save. | The new description is saved and shown. | 1 |  |
| SU-05 | D | Add and delete a temporary unused subject; then try to delete CSPC 103 after CL-01. | The unused subject is deleted; CSPC 103 cannot be deleted while a class uses it. | 2 |  |

### A4. Class Offering (10 points)

| TC | Type | Scenario and steps | Expected result | Pts | Score |
| --- | --- | --- | --- | --- | --- |
| CL-01 | C | Create CSPC 103 – Section A with the test-data term, schedule, room and teacher. | Saved and listed; CLASS row holds the correct subject_id and teacher_id. | 3 |  |
| CL-02 | V | Try to save a class with no teacher, no subject, or no school year/semester. | Rejected with a required-field message; nothing saved. | 2 |  |
| CL-03 | R | View classes handled by T-1001. | CSPC 103 – A is listed with subject, section, term, schedule and room. | 1 |  |
| CL-04 | U | Change the room to CS-202 and the schedule to TTh 1:00–2:30; save and reopen. | Changes are saved and shown in the class details and Class List. | 2 |  |
| CL-05 | V | Run after EN-01. Try to delete CSPC 103 – A. | Deletion is blocked because enrolled students depend on it. | 2 |  |

### A5. Enrollment (12 points)

| TC | Type | Scenario and steps | Expected result | Pts | Score |
| --- | --- | --- | --- | --- | --- |
| EN-01 | C | Enroll Juan, Pedro and Ana in CSPC 103 – A with today's date and status Enrolled. | Three ENROLLMENT rows with correct student_id, class_id, date and status. | 3 |  |
| EN-02 | V | Enroll Juan in CSPC 103 – A a second time. | Rejected as a duplicate enrollment; still one row for Juan in that class. | 2 |  |
| EN-03 | V | Try to enroll a student number that does not exist (e.g., 2026-9999). | Rejected with a clear message; no orphan ENROLLMENT row. | 1 |  |
| EN-04 | R | Open the list of students enrolled in CSPC 103 – A. | Juan, Pedro and Ana are listed with their enrollment status. | 2 |  |
| EN-05 | U | Change Pedro's status to Dropped, save, then change it back to Enrolled. | Each status change is saved and shown; Pedro's scores are not affected. | 2 |  |
| EN-06 | D | Add the temporary student 2026-0098 (Carlo Mendoza), enroll him and remove that enrollment; then try to remove Juan's enrollment after SC-01. | The empty enrollment is removed; Juan's enrollment with scores is protected or removed only after a clear warning. | 2 |  |

## Part B. Grading, Computation, Reports and Persistence (50 points)

### B1. Grading Configuration (13 points)

| TC | Type | Scenario and steps | Expected result | Pts | Score |
| --- | --- | --- | --- | --- | --- |
| GP-01 | C | Create grading periods Midterm (order 1) and Finals (order 2). | Both saved in GRADING_PERIOD in the correct order. | 2 |  |
| GC-01 | C | Create the six grade components with their periods and maximum scores. | Six GRADE_COMPONENT rows, each linked to the correct period_id with the correct max score. | 2 |  |
| GW-01 | C | Set the weights 20/30/50 for each period of CSPC 103 – A. | Six GRADE_PERCENTAGE rows with the correct class_id, component_id and weight; nothing is hard-coded. | 2 |  |
| GW-02 | V | Change the Midterm weights to 20/30/40 (total 90%) and save. | Rejected because the period total is not 100%; the saved weights stay 20/30/50. | 3 |  |
| GW-03 | V | Enter a negative or blank weight. | Rejected with a clear message. | 1 |  |
| GC-02 | R | View the grading configuration of CSPC 103 – A. | All periods, components, max scores and weights are shown as entered. | 1 |  |
| GC-03 | V | Run after SC-01. Try to delete the Midterm Quiz component. | Deletion is blocked because scores exist for it; no scores are lost. | 2 |  |

### B2. Component Scores (13 points)

| TC | Type | Scenario and steps | Expected result | Pts | Score |
| --- | --- | --- | --- | --- | --- |
| SC-01 | C | Enter all 18 raw scores from the test data, except enter Juan's Midterm Exam as 57 (corrected in SC-06). | 18 GRADE_COMPONENT_SCORE rows, each linked to the correct enrollment_id and component_id, with the encoding date. | 3 |  |
| SC-02 | V | Enter 55 for a Midterm Quiz (max 50). | Rejected: score is above the maximum; nothing saved. | 2 |  |
| SC-03 | V | Enter –5 for any component. | Rejected: score cannot be negative. | 1 |  |
| SC-04 | V | Try to enter a score for student 2026-0098, whose enrollment was removed in EN-06. | Rejected because the student is not enrolled; no score row is created. | 2 |  |
| SC-05 | R | Close and reopen the grade entry screen for CSPC 103 – A. | All saved scores reload correctly for each student and component. | 1 |  |
| SC-06 | U | Correct Juan's Midterm Exam from 57 to 75. | The score row is updated (not duplicated), and Juan's Midterm grade becomes 80.50 when computed. | 2 |  |
| SC-07 | D | Delete Ana's Final Quiz score, check her grade, then re-enter 48. | After deletion, her Finals grade is shown as incomplete or not computed rather than silently using 0; after re-entry it is 93.70 again. | 2 |  |

### B3. Grade Computation and Recalculation (10 points)

| TC | Type | Scenario and steps | Expected result | Pts | Score |
| --- | --- | --- | --- | --- | --- |
| GR-01 | R | Compute the Midterm grades of the class. | Juan 80.50 → 2.50, Pedro 53.50 → 5.00, Ana 100.00 → 1.00 (±0.01), saved in GRADE. | 3 |  |
| GR-02 | R | Compute the Finals and Overall grades. | Finals: Juan 83.50 → 2.25, Pedro 65.50 → 5.00, Ana 93.70 → 1.50. Overall: Juan 82.30 → 2.25 Passed, Pedro 60.70 → 5.00 Failed, Ana 96.22 → 1.25 Passed. | 3 |  |
| GR-03 | U | Change the Midterm weights to 30/30/40 and recompute. | Raw scores stay the same; Midterm: Juan 81.00 → 2.50, Pedro 52.00 → 5.00, Ana 100.00 → 1.00; Overall: Juan 82.50 → 2.25, Pedro 60.10 → 5.00, Ana 96.22 → 1.25. The GRADE rows are updated, not duplicated. | 3 |  |
| GR-04 | V | Check the audit trail after SC-06 or GR-03. | AUDIT_LOG (or an equivalent table) records who changed the grade data, what changed and when. | 1 |  |

### B4. Reports (10 points)

The three reports below follow the layouts given in class. All grades on the reports are grade points (1.00–3.00, 5.00 for failure). MG is the Midterm grade point; FG (F Grade) is the subject's final grade point, the equivalent of the Overall percentage (Midterm × 40% + Finals × 60%). Grade Weighted Average = Σ(F Grade × Units) ÷ Total Units, shown with two decimals. Every report must be generated from saved records, not typed in.

| TC | Type | Scenario and steps | Expected result | Pts | Score |
| --- | --- | --- | --- | --- | --- |
| RP-01 | R | Generate the Class List for CSPC 103 – A (Report 1). | Header shows subject code and title, section, teacher and department (from TE-04), school year, semester, schedule and room (CS-202, TTh 1:00–2:30 from CL-04). Columns: No., Student Name, Course. Students appear alphabetically by last name, not in the order entered: 1 Dela Cruz, Juan – BSCS; 2 Garcia, Ana – BSCS; 3 Reyes, Pedro – BSCS. Removed or temporary students do not appear. | 3 |  |
| RP-02 | R | Generate the Grade Sheet for CSPC 103 – A (Report 2). | Columns: No., Student, Course, MG, FG, in the same alphabetical order, as grade points read from GRADE after the GR-03 recomputation: Dela Cruz, Juan – BSCS – 2.50 – 2.25; Garcia, Ana – BSCS – 1.00 – 1.25; Reyes, Pedro – BSCS – 5.00 – 5.00. | 3 |  |
| RP-03 | R | Complete the report setup records, then generate the Student Grade report for Juan Dela Cruz (Report 3). | Header shows Student Name (Dela Cruz, Juan), Course (BSCS) and Year (2nd). One row per enrolled subject with Subject Code, Description (subject title), Teacher, Units and F Grade: CSPC 103 – Object Oriented Programming – Maria Santos – 3 – 2.25; PATHFIT 3 – Physical Activity Towards Health and Fitness 3 – Jose Ramos – 2 – 1.75. | 2 |  |
| RP-04 | R | Check the summary lines of Juan's Student Grade report. | Total Units: 5. No. of Subjects: 2. Grade Weighted Average: 2.05, computed as (2.25 × 3 + 1.75 × 2) ÷ 5 = 10.25 ÷ 5 from the database, not hard-coded. 2.00 is wrong and earns zero: it comes from a simple average of grade points, or from averaging percentages first (85.50 → 2.00). | 2 |  |

**Expected report layouts**

Use these as the answer key while checking RP-01 to RP-04. Column order and headings must match; fonts and styling are up to the group.

**Report 1. Class List**

**Subject: **CSPC 103 – Object Oriented Programming     **Section: **A

**Teacher: **Maria Santos, Information Technology Department

**Term: **1st Semester, SY 2026-2027     **Schedule / Room: **TTh 1:00–2:30, CS-202

*Arranged alphabetically by last name, then first name.*

| No. | Student Name | Course |
| --- | --- | --- |
| 1 | Dela Cruz, Juan | BSCS |
| 2 | Garcia, Ana | BSCS |
| 3 | Reyes, Pedro | BSCS |

**Report 2. Grade Sheet**

**Subject: **CSPC 103 – Object Oriented Programming     **Section: **A

**Teacher: **Maria Santos     **Term: **1st Semester, SY 2026-2027

*MG and FG are grade points. Percentages behind them after GR-03: Juan 81.00 / 82.50, Ana 100.00 / 96.22, Pedro 52.00 / 60.10.*

| No. | Student | Course | MG | FG |
| --- | --- | --- | --- | --- |
| 1 | Dela Cruz, Juan | BSCS | 2.50 | 2.25 |
| 2 | Garcia, Ana | BSCS | 1.00 | 1.25 |
| 3 | Reyes, Pedro | BSCS | 5.00 | 5.00 |

**Report 3. Student Grade**

**Student Name: **Dela Cruz, Juan     **Course: **BSCS     **Year: **2nd

**Term: **1st Semester, SY 2026-2027

| No. | Subject Code | Description | Teacher | Units | F Grade |
| --- | --- | --- | --- | --- | --- |
| 1 | CSPC 103 | Object Oriented Programming | Maria Santos | 3 | 2.25 |
| 2 | PATHFIT 3 | Physical Activity Towards Health and Fitness 3 | Jose Ramos | 2 | 1.75 |

**Total Units: **5          **No. of Subjects: **2

**Grade Weighted Average: **2.05   *[**(2.25 × 3) + (1.75 × 2)] ÷ 5 = 10.25 ÷ 5*

### B5. Persistence and Security (4 points)

| TC | Type | Scenario and steps | Expected result | Pts | Score |
| --- | --- | --- | --- | --- | --- |
| PS-01 | R | Close the application completely, restart it, and open the Grade Sheet. | All records, scores and computed grades are still present after the restart. | 2 |  |
| PS-02 | V | Add student 2026-0004, Kevin O'Brien, BSIT, 1st year, then search for ' OR '1'='1 in the student search. | O'Brien is saved correctly; the search returns no extra records and causes no SQL error, showing that parameter binding is used. | 2 |  |

## Score Summary Sheet

Student name: ______________________________________________   Date tested: ______________

| Module | Test cases | Max points | Points earned |
| --- | --- | --- | --- |
| A1. Student | ST-01 to ST-07 | 12 |  |
| A2. Teacher | TE-01 to TE-05 | 8 |  |
| A3. Subject | SU-01 to SU-05 | 8 |  |
| A4. Class Offering | CL-01 to CL-05 | 10 |  |
| A5. Enrollment | EN-01 to EN-06 | 12 |  |
| B1. Grading Configuration | GP-01 to GC-03 | 13 |  |
| B2. Component Scores | SC-01 to SC-07 | 13 |  |
| B3. Grade Computation and Recalculation | GR-01 to GR-04 | 10 |  |
| B4. Reports | RP-01 to RP-04 | 10 |  |
| B5. Persistence and Security | PS-01 to PS-02 | 4 |  |
| **Total** | **52 test cases** | **100** |  |

By CRUD operation, the points split as Create 21, Read 27, Update 14, Delete 7, and Validation 31. Validation cases carry heavy weight because the specification requires the system to reject invalid weights, out-of-range scores, unenrolled students and unsafe deletions.

Tested by: Brenda M. Balala, MIT   Signature: ______________________________

## Appendix. Expected Table Contents After Testing

After every test case has been run in order, including the report setup records and PS-02, the database should hold exactly the rows below. The tester compares these tables with the student's database client at the end of the demonstration.

**Reading the tables: **Column names follow the UML class design in snake_case, with the foreign keys from the ERD. Surrogate IDs assume auto-increment from 1 in test order, so gaps are expected where a test deleted a row (subject 2, enrollment 4, score 16). The exact ID numbers may differ; what matters is that every foreign key points to the right parent row. “—” means NULL or not supplied, and “test date” is the date the case was run. The class_code values are examples.

**Row counts**

| **Table** | **Rows** | **Comes from** |
| --- | --- | --- |
| STUDENT | 5 | ST-01, EN-06, PS-02 |
| TEACHER | 2 | TE-01, report setup |
| SUBJECT | 2 | SU-01, report setup |
| CLASS | 2 | CL-01, report setup |
| ENROLLMENT | 4 | EN-01, report setup |
| GRADING_PERIOD | 2 | GP-01 |
| GRADE_COMPONENT | 6 | GC-01 |
| GRADE_PERCENTAGE | 12 | GW-01, GR-03, report setup |
| GRADE_COMPONENT_SCORE | 24 | SC-01, SC-06, SC-07, report setup |
| GRADE | 4 | GR-01 to GR-03, report setup |
| AUDIT_LOG | 7 or more | SC-06, SC-07, GR-03 |

**STUDENT**

| **student_id** | **first_name** | **last_name** | **email** | **program** | **year_level** | **status** | **Set by** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-0001 | Juan | Dela Cruz | — | BSCS | 2 | Active | ST-01 |
| 2026-0002 | Pedro | Reyes | — | BSCS | 2 | Active | ST-01 |
| 2026-0003 | Ana | Garcia | — | BSCS | 2 | Active | ST-01; program BSIT → BSCS in ST-05 |
| 2026-0098 | Carlo | Mendoza | — | BSIT | 1 | Active | EN-06 (student kept, enrollment removed) |
| 2026-0004 | Kevin | O'Brien | — | BSIT | 1 | Active | PS-02 |

**TEACHER**

| **teacher_id** | **first_name** | **last_name** | **email** | **department** | **status** | **Set by** |
| --- | --- | --- | --- | --- | --- | --- |
| T-1001 | Maria | Santos | — | Information Technology Department | Active | TE-01; department changed in TE-04 |
| T-1002 | Jose | Ramos | — | Physical Education Department | Active | Report setup |

**SUBJECT**

| **subject_id** | **subject_code** | **subject_name** | **description** | **units** | **Set by** |
| --- | --- | --- | --- | --- | --- |
| 1 | CSPC 103 | Object Oriented Programming | Object-oriented analysis, design and programming in Java | 3 | SU-01; description in SU-04 |
| 3 | PATHFIT 3 | Physical Activity Towards Health and Fitness 3 | — | 2 | Report setup |

**CLASS (ClassOffering)**

| **class_id** | **class_code** | **subject_id** | **teacher_id** | **section** | **school_year** | **semester** | **schedule** | **room** | **Set by** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | CSPC103-A | 1 | T-1001 | A | 2026-2027 | 1st | TTh 1:00–2:30 | CS-202 | CL-01; room and schedule in CL-04 |
| 2 | PATHFIT3-A | 3 | T-1002 | A | 2026-2027 | 1st | TTh 3:00–5:00 | Gym | Report setup |

**ENROLLMENT**

| **enrollment_id** | **student_id** | **class_id** | **enroll_date** | **status** | **Set by** |
| --- | --- | --- | --- | --- | --- |
| 1 | 2026-0001 | 1 | test date | Enrolled | EN-01 |
| 2 | 2026-0002 | 1 | test date | Enrolled | EN-01; Dropped and back to Enrolled in EN-05 |
| 3 | 2026-0003 | 1 | test date | Enrolled | EN-01 |
| 5 | 2026-0001 | 2 | test date | Enrolled | Report setup |

**GRADING_PERIOD**

| **period_id** | **name** | **period_order** | **start_date** | **end_date** | **school_year** | **semester** | **Set by** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Midterm | 1 | as entered | as entered | 2026-2027 | 1st | GP-01 |
| 2 | Finals | 2 | as entered | as entered | 2026-2027 | 1st | GP-01 |

**GRADE_COMPONENT**

| **component_id** | **period_id** | **name** | **type** | **max_score** | **description** | **Set by** |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | Midterm Quiz | Quiz | 50 | — | GC-01; delete blocked in GC-03 |
| 2 | 1 | Midterm Laboratory/Project | Laboratory | 100 | — | GC-01 |
| 3 | 1 | Midterm Examination | Exam | 100 | — | GC-01 |
| 4 | 2 | Final Quiz | Quiz | 50 | — | GC-01 |
| 5 | 2 | Final Laboratory/Project | Laboratory | 100 | — | GC-01 |
| 6 | 2 | Final Examination | Exam | 100 | — | GC-01 |

**GRADE_PERCENTAGE**

| **percentage_id** | **class_id** | **component_id** | **percentage** | **Set by** |
| --- | --- | --- | --- | --- |
| 1 | 1 | 1 | 30.00 | GW-01 (20.00); changed in GR-03 |
| 2 | 1 | 2 | 30.00 | GW-01 |
| 3 | 1 | 3 | 40.00 | GW-01 (50.00); changed in GR-03 |
| 4 | 1 | 4 | 20.00 | GW-01 |
| 5 | 1 | 5 | 30.00 | GW-01 |
| 6 | 1 | 6 | 50.00 | GW-01 |
| 7 | 2 | 1 | 20.00 | Report setup |
| 8 | 2 | 2 | 30.00 | Report setup |
| 9 | 2 | 3 | 50.00 | Report setup |
| 10 | 2 | 4 | 20.00 | Report setup |
| 11 | 2 | 5 | 30.00 | Report setup |
| 12 | 2 | 6 | 50.00 | Report setup |

**GRADE_COMPONENT_SCORE**

| **score_id** | **enrollment_id** | **component_id** | **score** | **remarks** | **date_recorded** | **Set by** |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1 | 40 | — | test date | Juan – SC-01 |
| 2 | 1 | 2 | 90 | — | test date | Juan – SC-01 |
| 3 | 1 | 3 | 75 | — | test date | Juan – SC-01 (57); corrected in SC-06 |
| 4 | 1 | 4 | 45 | — | test date | Juan – SC-01 |
| 5 | 1 | 5 | 85 | — | test date | Juan – SC-01 |
| 6 | 1 | 6 | 80 | — | test date | Juan – SC-01 |
| 7 | 2 | 1 | 20 | — | test date | Pedro – SC-01 |
| 8 | 2 | 2 | 60 | — | test date | Pedro – SC-01 |
| 9 | 2 | 3 | 55 | — | test date | Pedro – SC-01 |
| 10 | 2 | 4 | 30 | — | test date | Pedro – SC-01 |
| 11 | 2 | 5 | 70 | — | test date | Pedro – SC-01 |
| 12 | 2 | 6 | 65 | — | test date | Pedro – SC-01 |
| 13 | 3 | 1 | 50 | — | test date | Ana – SC-01 |
| 14 | 3 | 2 | 100 | — | test date | Ana – SC-01 |
| 15 | 3 | 3 | 100 | — | test date | Ana – SC-01 |
| 17 | 3 | 5 | 95 | — | test date | Ana – SC-01 |
| 18 | 3 | 6 | 92 | — | test date | Ana – SC-01 |
| 19 | 3 | 4 | 48 | — | test date | Ana – re-entered in SC-07 (row 16 deleted) |
| 20 | 5 | 1 | 45 | — | test date | Juan (PATHFIT 3) – report setup |
| 21 | 5 | 2 | 90 | — | test date | Juan (PATHFIT 3) – report setup |
| 22 | 5 | 3 | 90 | — | test date | Juan (PATHFIT 3) – report setup |
| 23 | 5 | 4 | 45 | — | test date | Juan (PATHFIT 3) – report setup |
| 24 | 5 | 5 | 90 | — | test date | Juan (PATHFIT 3) – report setup |
| 25 | 5 | 6 | 90 | — | test date | Juan (PATHFIT 3) – report setup |

**GRADE**

*One row per enrollment. Percentages are kept with their grade points; final_equiv is the FG shown on the reports. Rows 1–3 come from GR-01 and GR-02 (rows 1 and 2 updated in GR-03); row 4 from the report setup.*

| **grade_id** | **enrollment_id** | **midterm_grade** | **finals_grade** | **overall_grade** | **midterm_equiv** | **final_equiv** | **remarks** | **date_encoded** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 81.00 | 83.50 | 82.50 | 2.50 | 2.25 | Passed | test date |
| 2 | 2 | 52.00 | 65.50 | 60.10 | 5.00 | 5.00 | Failed | test date |
| 3 | 3 | 100.00 | 93.70 | 96.22 | 1.00 | 1.25 | Passed | test date |
| 4 | 5 | 90.00 | 90.00 | 90.00 | 1.75 | 1.75 | Passed | test date |

**AUDIT_LOG (or equivalent)**

*Minimum entries checked in GR-04. Column names and wording may differ; extra entries (for example, for inserts) are fine.*

| **log_id** | **table_name** | **record_id** | **action** | **old_value** | **new_value** | **changed_by** | **changed_at** | **From** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | GRADE_COMPONENT_SCORE | 3 | UPDATE | score 57 | score 75 | tester | test date | SC-06 |
| 2 | GRADE_COMPONENT_SCORE | 16 | DELETE | score 48 | — | tester | test date | SC-07 |
| 3 | GRADE_COMPONENT_SCORE | 19 | INSERT | — | score 48 | tester | test date | SC-07 |
| 4 | GRADE_PERCENTAGE | 1 | UPDATE | 20.00 | 30.00 | tester | test date | GR-03 |
| 5 | GRADE_PERCENTAGE | 3 | UPDATE | 50.00 | 40.00 | tester | test date | GR-03 |
| 6 | GRADE | 1 | UPDATE | 80.50 / 82.30 (2.50 / 2.25) | 81.00 / 82.50 (2.50 / 2.25) | tester | test date | GR-03 |
| 7 | GRADE | 2 | UPDATE | 53.50 / 60.70 (5.00 / 5.00) | 52.00 / 60.10 (5.00 / 5.00) | tester | test date | GR-03 |

**Rows that must NOT exist**

- STUDENT: 2026-0099 (deleted in ST-06), a second 2026-0001 (ST-02) or a student with a blank name or number (ST-03).

- TEACHER: a second T-1001 or a teacher with a blank name (TE-02).

- SUBJECT: a second CSPC 103 or a subject with 0 or negative units (SU-02), and the temporary subject 2 (deleted in SU-05).

- CLASS: a class with no teacher, subject or term (CL-02).

- ENROLLMENT: a second row for Juan in class 1 (EN-02), any row for 2026-9999 (EN-03), and enrollment 4 for 2026-0098 (removed in EN-06).

- GRADE_PERCENTAGE: Midterm weights 20/30/40 (GW-02) or any negative or blank weight (GW-03).

- GRADE_COMPONENT_SCORE: a quiz score of 55 (SC-02), a score of –5 (SC-03), any score for 2026-0098 (SC-04), score row 16 (deleted in SC-07), or a second Midterm Exam row for Juan (SC-06).

- GRADE: more than one row for the same enrollment (GR-03).

- Any table: extra rows caused by the ' OR '1'='1 search in PS-02.

Notre Dame of Marbel University • Computer Studies Department • 1st Sem 2026–2027     Page 1