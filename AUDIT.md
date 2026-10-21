# Audit: CSPC 103 CRUD Test Cases

Source of truth: `SPEC.md`. Table names in SPEC (STUDENT, GRADE, ...) map to the real plural tables (students, grades, ...).

## How the evidence was collected

- Database: scratch copy `Modelo_CSPC103_test` (schema only, no sample records). The demo database `Modelo_CSPC103` was never used.
- GUI run: a script opens the real `main.py` window, types into the real fields, picks from the real dropdowns, selects table rows and invokes the real buttons for every case in SPEC order. Every pop-up is recorded (confirmations answered Yes). After each step it compares the on-screen list with the database.
- Service run: the same 52 cases called directly on the service classes, with the expected numbers from SPEC.
- Baseline commit: `c56f071` (main). Result: 52/52 GUI cases and 60/60 service checks passed; final row counts matched the appendix.

## Baseline result per test case (commit c56f071)

| TC | Result | Handled by | Evidence |
| --- | --- | --- | --- |
| ST-01 | PASS | `StudentService.add` | 3 rows, success pop-up, list refreshed |
| ST-02 | PASS | `StudentService.add` | "That student number already exists." |
| ST-03 | PASS | `StudentService.validate` | "First name is required." / "Student number is required." |
| ST-04 | PASS | `StudentRepository.search` | search "Reyes" returns only 2026-0002; form shows Pedro |
| ST-05 | PASS | `StudentService.update` | program BSCS in list, form and DB after reopen |
| ST-06 | PASS | `StudentManagementView.delete_student` | confirmation shown; row gone from list and DB |
| ST-07 | PASS | `StudentService.delete` | "Cannot delete this student because enrollments depend on it." |
| TE-01 | PASS | `TeacherService.add` | row saved, list refreshed |
| TE-02 | PASS | `TeacherService.add` | "That teacher ID already exists." / "First name is required." |
| TE-03 | PASS | `TeacherManagementView.on_select` | details shown |
| TE-04 | PASS | `TeacherService.update` | new department in list, DB and Class List header |
| TE-05 | PASS | `TeacherService.delete` | "Cannot delete this teacher because class CSPC103-A depends on it." |
| SU-01 | PASS | `SubjectService.save` | row saved, list refreshed |
| SU-02 | PASS | `SubjectService.save` | "That subject code already exists." / "Units must be a positive whole number." |
| SU-03 | PASS | `SubjectManagementView.load_data` | CSPC 103 listed with details |
| SU-04 | PASS | `SubjectService.save` | description saved and shown |
| SU-05 | PASS | `SubjectService.delete` | temp subject deleted; CSPC 103 blocked naming CSPC103-A |
| CL-01 | PARTIAL | `ClassService.save` | saved with correct FKs, but semester stored as "1st Semester" while the appendix expects "1st" |
| CL-02 | PASS | `ClassService.save` | "Teacher is required." / "Subject is required." / "School year is required." |
| CL-03 | PASS | `ClassEnrollmentTab.load_classes` | Teacher filter: Santos shows CSPC103-A only |
| CL-04 | PASS | `ClassService.save` | room CS-202, schedule TTh 1:00-2:30 in list and after reopen |
| CL-05 | PASS | `ClassService.delete` | "Cannot delete this class because enrollments depend on it." |
| EN-01 | PASS | `EnrollmentService.enroll_student` | 3 rows, today's date, Enrolled |
| EN-02 | PASS | `EnrollmentService.enroll_student` | "Student 'Dela Cruz, Juan' is already enrolled in CSPC103-A." |
| EN-03 | PASS | `EnrollmentService.enroll_student` | "Student with ID '2026-9999' does not exist." |
| EN-04 | PASS | `ClassEnrollmentTab.load_enrollments` | 3 students with status |
| EN-05 | PASS | `EnrollmentService.update_status` | pop-ups "Enrollment status set to Dropped." / "...Enrolled."; DB matches |
| EN-06 | PASS | `EnrollmentService.remove_enrollment` | Carlo removed with confirmation; Juan blocked: "...scores depend on it." |
| GP-01 | PASS | `ConfigurationService.add_period` | Midterm 1, Finals 2 |
| GC-01 | PASS | `ConfigurationService.add_component` | 6 rows with correct period and max |
| GW-01 | PASS | `ConfigurationService.save_weights` | 6 rows 20/30/50 per period |
| GW-02 | PASS | `GradeCalculator.validate_weights` | "Weights total 90%, they must total 100%."; DB stays 20/30/50; boxes reload |
| GW-03 | PASS | `GradeCalculator.validate_weights` | "Weight cannot be negative." / "Enter a number for weight." |
| GC-02 | PARTIAL | `ClassEnrollmentTab.load_weights_and_components` | components and max shown, but weights are only visible one period at a time in edit boxes; no Weight column, no period total (teacher item 1) |
| GC-03 | PASS | `ConfigurationService.delete_component` | "Cannot delete this component because scores depend on it." |
| SC-01 | PASS | `ScoreService.save` | 18 rows with date |
| SC-02 | PASS | `GradeCalculator.normalize_score` | "Score 55 is above the maximum of 50." |
| SC-03 | PASS | `GradeCalculator.normalize_score` | "Score cannot be negative." |
| SC-04 | PASS | `ScoreGradingTab.save_score` | "'2026-0098' is not enrolled in this class, so no score can be saved. ..." |
| SC-05 | PASS | `ScoreGradingTab.load_student_scores` | scores reload after tab switch |
| SC-06 | PASS | `ScoreRepository.save` (upsert) | 18 rows, value 75 |
| SC-07 | PASS | `GradeCalculator.compute_period_grade` | Finals "Incomplete" after delete; 93.70 after re-entry |
| GR-01 | PASS | `GradingService.bulk_compute_class_grades` | 80.50/2.50, 53.50/5.00, 100.00/1.00 saved |
| GR-02 | PASS | same | Finals and Overall as SPEC |
| GR-03 | PASS | same | 81.00/82.50, 52.00/60.10, 100.00/96.22; 3 GRADE rows |
| GR-04 | PASS | `AuditRepository`, Audit Log tab | UPDATE rows for score 57 to 75, weights and grades, with who and when |
| RP-01 | PASS | `ReportService.generate_class_list_report` | header and alphabetical rows as SPEC |
| RP-02 | PASS | `ReportService.generate_grade_sheet_report` | 2.50/2.25, 1.00/1.25, 5.00/5.00 |
| RP-03 | PASS | `ReportService.generate_student_grade_report` | two rows as SPEC |
| RP-04 | PASS | same | Total Units 5, Subjects 2, GWA 2.05 |
| PS-01 | PASS | PostgreSQL | grade sheet identical after app restart |
| PS-02 | PASS | `StudentRepository.search` (parameter binding) | O'Brien saved; injection search returns 0 rows, no error |

## Baseline: teacher's 4 items (CLAUDE_CODE_PROMPT.md section 4)

| Item | Result | Evidence |
| --- | --- | --- |
| 1. Weight beside max score | FAIL | Config table headings: ID, Period, Component Name, Category, Max Score. Score dropdown: "[Midterm] Midterm Quiz (Quiz)", max label "50.0". No weight, no period total. |
| 2. Midterm, Finals, Overall | PARTIAL | Values shown, but headings mixed ("Overall Final", "Rating"), no Status column, no formula label; 40/60 are editable boxes that only accept 40/60 (magic numbers in service and UI). |
| 3. Remarks automatic | PASS | Remarks come from `GradeCalculator.remarks_for`; the score form's "Remarks:" box is a score note and reads like grade remarks. |
| 4. Grade without Finals | FAIL | Class with Midterm weights only: compute raises "Finals: No weights entered." A Finals component with weights but no scores cannot be deleted ("grading weights depend on it"). |

## Baseline: other checks

| Area | Result | Evidence |
| --- | --- | --- |
| Grade scale | PASS | One table in `GradeCalculator.GRADE_SCALE`; lookup on unrounded value. |
| Grade math precision | PASS | Float sums are cleaned with `round(x, 6)` before lookup; boundary values 97.00/96.99/75.00/74.99 map correctly (unit tests). No change needed. |
| Report layouts | PASS | Column order and headings match; alphabetical by last name, first name. |
| GWA | PASS | 2.05 from saved grades and units. |
| DB constraints | PASS | PKs, FKs, UNIQUE (student id, teacher id, subject code, class code, enrollment per class, score per component, grade per enrollment), CHECK (units > 0, score >= 0, weight 0..100). |
| Confirmations | PASS | Every delete asks first; Reset asks first. |
| Appendix | PARTIAL | Row counts match; semester values are "1st Semester" instead of "1st". |
| Code cleanup | PARTIAL | Unused `find_by_offering_and_period`; overall weights 40/60 repeated in service and UI; `db.init_db` (151 lines) duplicates the schema. |

## Final result (branch `refinements`)

Run on a fresh scratch database built from `schema.sql`, in SPEC order, through the real GUI.

| Check | Result |
| --- | --- |
| 52 test cases through the GUI | 52/52 PASS |
| Service-level checks with SPEC numbers | 60/60 PASS |
| `verify_appendix.sql` after the full run | 38/38 PASS (row counts, expected rows, audit entries, must-not-exist rows) |
| Unit tests (`python -m unittest discover tests`) | 21/21 OK |
| Teacher items 1-4 through the GUI | 17/17 PASS |
| Empty database: every button on every tab clicked | no crash, no traceback; each shows a clear message or does nothing |

Changes per baseline finding:

| Baseline finding | Now | Fix |
| --- | --- | --- |
| CL-01 PARTIAL: semester "1st Semester" | PASS | Semester dropdown stores "1st" / "2nd" / "Summer"; reports print "1st Semester" |
| GC-02 PARTIAL: weights not in the table | PASS | Config table: Period, Component, Category, Max Score, Weight (%) for the selected class, plus a total row per period; "-" when no weight is set |
| Item 1 FAIL | PASS | Score dropdown shows "Midterm Quiz (/50 - 20%)"; the Max / Weight label shows "50 / 20%"; Recorded Scores has a Weight column |
| Item 2 PARTIAL | PASS | Grades table: Midterm %, Midterm GP, Finals %, Finals GP, Overall %, Overall GP, Remarks, Status; formula label "Overall = Midterm 40% + Finals 60%" read from `GradeCalculator` constants; the editable 40/60 boxes are gone |
| Item 3 | PASS | Remarks come only from `GradeCalculator.remarks_for`; the score form's note box is labelled "Score Note" |
| Item 4 FAIL | PASS | Period states Complete / Incomplete / N/A; Midterm-only provisional Overall behind `SHOW_MIDTERM_ONLY_OVERALL`; reports mark it `*` with "* Midterm only"; deleting an unscored component removes its weights in one transaction with audit rows, and the grade still shows Midterm |
| GWA rounding (found during the audit) | PASS | The report rounded with Python's default half-even rule (2.125 printed 2.12); it now uses `GradeCalculator.weighted_average` (half up, 2.13). SPEC value 2.05 unchanged |
| Code cleanup PARTIAL | PASS | `schema.sql` is the one schema source (pg_dump identical to the old DDL); unused methods removed; main window constructor split |

Behavior changes to know about:

- The saved GRADE row is refreshed on every score save, so grades are viewable before Compute is pressed. Compute All still recomputes every student (needed after a weight change, GR-03) and updates the same row.
- Components are shared by all classes. Adding a component to a period leaves that period "Incomplete" in every class until its weights include the new component.

Still open:

- Finals GP is converted from the saved two-decimal Finals percentage, because GRADE has no column for it. A Finals percentage from 96.995 to 96.999 would show 1.00 instead of 1.25. Midterm GP and Overall GP are stored from the unrounded value and are exact. The SPEC data never reaches this edge.
- `seed_data.py` and `ui/theme.py` keep long declarative blocks (sample data, style table). They were not split; splitting them would not make them clearer.
