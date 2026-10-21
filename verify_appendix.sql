-- verify_appendix.sql - compares the database with the SPEC.md appendix after the full test run
-- Usage: psql -U postgres -d Modelo_CSPC103 -f verify_appendix.sql
-- Read-only: it only creates a temporary view that disappears when the session ends.
-- Rows are matched by meaning (student number, class code, component name), never by id number,
-- because ids can differ from the appendix. Schedules are compared with "-" and "–" treated the same.

CREATE TEMP VIEW appendix_checks AS
WITH
score_rows AS (
    SELECT e.student_id, c.class_code, gc.name AS component, s.score
    FROM grade_component_scores s
    JOIN enrollments e ON e.enrollment_id = s.enrollment_id
    JOIN class_offerings c ON c.class_id = e.class_id
    JOIN grade_components gc ON gc.component_id = s.component_id
),
expected_scores (student_id, class_code, component, score) AS (VALUES
    ('2026-0001', 'CSPC103-A', 'Midterm Quiz', 40), ('2026-0001', 'CSPC103-A', 'Midterm Laboratory/Project', 90),
    ('2026-0001', 'CSPC103-A', 'Midterm Examination', 75), ('2026-0001', 'CSPC103-A', 'Final Quiz', 45),
    ('2026-0001', 'CSPC103-A', 'Final Laboratory/Project', 85), ('2026-0001', 'CSPC103-A', 'Final Examination', 80),
    ('2026-0002', 'CSPC103-A', 'Midterm Quiz', 20), ('2026-0002', 'CSPC103-A', 'Midterm Laboratory/Project', 60),
    ('2026-0002', 'CSPC103-A', 'Midterm Examination', 55), ('2026-0002', 'CSPC103-A', 'Final Quiz', 30),
    ('2026-0002', 'CSPC103-A', 'Final Laboratory/Project', 70), ('2026-0002', 'CSPC103-A', 'Final Examination', 65),
    ('2026-0003', 'CSPC103-A', 'Midterm Quiz', 50), ('2026-0003', 'CSPC103-A', 'Midterm Laboratory/Project', 100),
    ('2026-0003', 'CSPC103-A', 'Midterm Examination', 100), ('2026-0003', 'CSPC103-A', 'Final Quiz', 48),
    ('2026-0003', 'CSPC103-A', 'Final Laboratory/Project', 95), ('2026-0003', 'CSPC103-A', 'Final Examination', 92),
    ('2026-0001', 'PATHFIT3-A', 'Midterm Quiz', 45), ('2026-0001', 'PATHFIT3-A', 'Midterm Laboratory/Project', 90),
    ('2026-0001', 'PATHFIT3-A', 'Midterm Examination', 90), ('2026-0001', 'PATHFIT3-A', 'Final Quiz', 45),
    ('2026-0001', 'PATHFIT3-A', 'Final Laboratory/Project', 90), ('2026-0001', 'PATHFIT3-A', 'Final Examination', 90)
),
weight_rows AS (
    SELECT c.class_code, gc.name AS component, w.percentage
    FROM grade_percentages w
    JOIN class_offerings c ON c.class_id = w.class_id
    JOIN grade_components gc ON gc.component_id = w.component_id
),
expected_weights (class_code, component, percentage) AS (VALUES
    ('CSPC103-A', 'Midterm Quiz', 30), ('CSPC103-A', 'Midterm Laboratory/Project', 30),
    ('CSPC103-A', 'Midterm Examination', 40), ('CSPC103-A', 'Final Quiz', 20),
    ('CSPC103-A', 'Final Laboratory/Project', 30), ('CSPC103-A', 'Final Examination', 50),
    ('PATHFIT3-A', 'Midterm Quiz', 20), ('PATHFIT3-A', 'Midterm Laboratory/Project', 30),
    ('PATHFIT3-A', 'Midterm Examination', 50), ('PATHFIT3-A', 'Final Quiz', 20),
    ('PATHFIT3-A', 'Final Laboratory/Project', 30), ('PATHFIT3-A', 'Final Examination', 50)
),
grade_rows AS (
    SELECT e.student_id, c.class_code, g.*
    FROM grades g
    JOIN enrollments e ON e.enrollment_id = g.enrollment_id
    JOIN class_offerings c ON c.class_id = e.class_id
),
expected_grades (student_id, class_code, midterm_grade, finals_grade, overall_grade, midterm_equiv, final_equiv, remarks) AS (VALUES
    ('2026-0001', 'CSPC103-A', 81.00, 83.50, 82.50, 2.50, 2.25, 'Passed'),
    ('2026-0002', 'CSPC103-A', 52.00, 65.50, 60.10, 5.00, 5.00, 'Failed'),
    ('2026-0003', 'CSPC103-A', 100.00, 93.70, 96.22, 1.00, 1.25, 'Passed'),
    ('2026-0001', 'PATHFIT3-A', 90.00, 90.00, 90.00, 1.75, 1.75, 'Passed')
),
audit_json AS (
    SELECT table_name, action, old_value::json AS old_row, new_value::json AS new_row
    FROM audit_log
),
checks (section, name, ok) AS (
    -- row counts
    SELECT 'count', 'STUDENT = 5', (SELECT count(*) FROM students) = 5
    UNION ALL SELECT 'count', 'TEACHER = 2', (SELECT count(*) FROM teachers) = 2
    UNION ALL SELECT 'count', 'SUBJECT = 2', (SELECT count(*) FROM subjects) = 2
    UNION ALL SELECT 'count', 'CLASS = 2', (SELECT count(*) FROM class_offerings) = 2
    UNION ALL SELECT 'count', 'ENROLLMENT = 4', (SELECT count(*) FROM enrollments) = 4
    UNION ALL SELECT 'count', 'GRADING_PERIOD = 2', (SELECT count(*) FROM grading_periods) = 2
    UNION ALL SELECT 'count', 'GRADE_COMPONENT = 6', (SELECT count(*) FROM grade_components) = 6
    UNION ALL SELECT 'count', 'GRADE_PERCENTAGE = 12', (SELECT count(*) FROM grade_percentages) = 12
    UNION ALL SELECT 'count', 'GRADE_COMPONENT_SCORE = 24', (SELECT count(*) FROM grade_component_scores) = 24
    UNION ALL SELECT 'count', 'GRADE = 4', (SELECT count(*) FROM grades) = 4
    UNION ALL SELECT 'count', 'AUDIT_LOG >= 7', (SELECT count(*) FROM audit_log) >= 7

    -- expected rows
    UNION ALL SELECT 'row', 'STUDENT rows', (
        SELECT count(*) FROM students s JOIN (VALUES
            ('2026-0001', 'Juan', 'Dela Cruz', 'BSCS', 2), ('2026-0002', 'Pedro', 'Reyes', 'BSCS', 2),
            ('2026-0003', 'Ana', 'Garcia', 'BSCS', 2), ('2026-0098', 'Carlo', 'Mendoza', 'BSIT', 1),
            ('2026-0004', 'Kevin', 'O''Brien', 'BSIT', 1)
        ) AS x(id, first_name, last_name, program, year_level)
          ON s.student_id = x.id AND s.first_name = x.first_name AND s.last_name = x.last_name
         AND s.program = x.program AND s.year_level = x.year_level AND s.email IS NULL AND s.status = 'Active') = 5
    UNION ALL SELECT 'row', 'TEACHER rows', (
        SELECT count(*) FROM teachers t JOIN (VALUES
            ('T-1001', 'Maria', 'Santos', 'Information Technology Department'),
            ('T-1002', 'Jose', 'Ramos', 'Physical Education Department')
        ) AS x(id, first_name, last_name, department)
          ON t.teacher_id = x.id AND t.first_name = x.first_name AND t.last_name = x.last_name
         AND t.department = x.department AND t.status = 'Active') = 2
    UNION ALL SELECT 'row', 'SUBJECT rows', (
        SELECT count(*) FROM subjects
        WHERE (subject_code = 'CSPC 103' AND subject_name = 'Object Oriented Programming' AND units = 3
               AND description = 'Object-oriented analysis, design and programming in Java')
           OR (subject_code = 'PATHFIT 3' AND subject_name = 'Physical Activity Towards Health and Fitness 3'
               AND units = 2 AND coalesce(description, '') = '')) = 2
    UNION ALL SELECT 'row', 'CLASS rows', (
        SELECT count(*) FROM class_offerings c
        JOIN subjects s ON s.subject_id = c.subject_id
        JOIN (VALUES
            ('CSPC103-A', 'CSPC 103', 'T-1001', 'TTh 1:00-2:30', 'CS-202'),
            ('PATHFIT3-A', 'PATHFIT 3', 'T-1002', 'TTh 3:00-5:00', 'Gym')
        ) AS x(class_code, subject_code, teacher_id, schedule, room)
          ON c.class_code = x.class_code AND s.subject_code = x.subject_code AND c.teacher_id = x.teacher_id
         AND replace(c.schedule, '–', '-') = x.schedule AND c.room = x.room
         AND c.section = 'A' AND c.school_year = '2026-2027' AND c.semester = '1st') = 2
    UNION ALL SELECT 'row', 'ENROLLMENT rows', (
        SELECT count(*) FROM enrollments e JOIN class_offerings c ON c.class_id = e.class_id
        WHERE e.status = 'Enrolled' AND (
              (c.class_code = 'CSPC103-A' AND e.student_id IN ('2026-0001', '2026-0002', '2026-0003'))
           OR (c.class_code = 'PATHFIT3-A' AND e.student_id = '2026-0001'))) = 4
    UNION ALL SELECT 'row', 'GRADING_PERIOD rows', (
        SELECT count(*) FROM grading_periods
        WHERE ((name = 'Midterm' AND period_order = 1) OR (name = 'Finals' AND period_order = 2))
          AND school_year = '2026-2027' AND semester = '1st') = 2
    UNION ALL SELECT 'row', 'GRADE_COMPONENT rows', (
        SELECT count(*) FROM grade_components gc JOIN grading_periods p ON p.period_id = gc.period_id
        JOIN (VALUES
            ('Midterm', 'Midterm Quiz', 'Quiz', 50), ('Midterm', 'Midterm Laboratory/Project', 'Laboratory', 100),
            ('Midterm', 'Midterm Examination', 'Exam', 100), ('Finals', 'Final Quiz', 'Quiz', 50),
            ('Finals', 'Final Laboratory/Project', 'Laboratory', 100), ('Finals', 'Final Examination', 'Exam', 100)
        ) AS x(period, name, type, max_score)
          ON p.name = x.period AND gc.name = x.name AND gc.type = x.type AND gc.max_score = x.max_score) = 6
    UNION ALL SELECT 'row', 'GRADE_PERCENTAGE rows', (
        SELECT count(*) FROM weight_rows w JOIN expected_weights x
          ON w.class_code = x.class_code AND w.component = x.component AND w.percentage = x.percentage) = 12
    UNION ALL SELECT 'row', 'GRADE_COMPONENT_SCORE rows', (
        SELECT count(*) FROM score_rows s JOIN expected_scores x
          ON s.student_id = x.student_id AND s.class_code = x.class_code AND s.component = x.component AND s.score = x.score) = 24
    UNION ALL SELECT 'row', 'GRADE rows', (
        SELECT count(*) FROM grade_rows g JOIN expected_grades x
          ON g.student_id = x.student_id AND g.class_code = x.class_code
         AND g.midterm_grade = x.midterm_grade AND g.finals_grade = x.finals_grade
         AND g.overall_grade = x.overall_grade AND g.midterm_equiv = x.midterm_equiv
         AND g.final_equiv = x.final_equiv AND g.remarks = x.remarks) = 4

    -- audit trail entries checked in GR-04
    UNION ALL SELECT 'audit', 'score 57 to 75 (SC-06)', EXISTS (
        SELECT 1 FROM audit_json WHERE table_name = 'GRADE_COMPONENT_SCORE' AND action = 'UPDATE'
          AND (old_row->>'score')::numeric = 57 AND (new_row->>'score')::numeric = 75)
    UNION ALL SELECT 'audit', 'score 48 deleted (SC-07)', EXISTS (
        SELECT 1 FROM audit_json WHERE table_name = 'GRADE_COMPONENT_SCORE' AND action = 'DELETE'
          AND (old_row->>'score')::numeric = 48)
    UNION ALL SELECT 'audit', 'score 48 re-entered (SC-07)', (
        SELECT count(*) FROM audit_json WHERE table_name = 'GRADE_COMPONENT_SCORE' AND action = 'INSERT'
          AND (new_row->>'score')::numeric = 48) >= 2
    UNION ALL SELECT 'audit', 'weight 20 to 30 (GR-03)', EXISTS (
        SELECT 1 FROM audit_json WHERE table_name = 'GRADE_PERCENTAGE' AND action = 'UPDATE'
          AND (old_row->>'percentage')::numeric = 20 AND (new_row->>'percentage')::numeric = 30)
    UNION ALL SELECT 'audit', 'weight 50 to 40 (GR-03)', EXISTS (
        SELECT 1 FROM audit_json WHERE table_name = 'GRADE_PERCENTAGE' AND action = 'UPDATE'
          AND (old_row->>'percentage')::numeric = 50 AND (new_row->>'percentage')::numeric = 40)
    UNION ALL SELECT 'audit', 'Juan overall 82.30 to 82.50 (GR-03)', EXISTS (
        SELECT 1 FROM audit_json WHERE table_name = 'GRADE' AND action = 'UPDATE'
          AND (old_row->>'overall_grade')::numeric = 82.30 AND (new_row->>'overall_grade')::numeric = 82.50)
    UNION ALL SELECT 'audit', 'Pedro overall 60.70 to 60.10 (GR-03)', EXISTS (
        SELECT 1 FROM audit_json WHERE table_name = 'GRADE' AND action = 'UPDATE'
          AND (old_row->>'overall_grade')::numeric = 60.70 AND (new_row->>'overall_grade')::numeric = 60.10)
    UNION ALL SELECT 'audit', 'every entry has who and when', NOT EXISTS (
        SELECT 1 FROM audit_log WHERE coalesce(changed_by, '') = '' OR changed_at IS NULL)

    -- rows that must NOT exist
    UNION ALL SELECT 'must not', 'no student 2026-0099 or blank name/number', NOT EXISTS (
        SELECT 1 FROM students WHERE student_id = '2026-0099' OR trim(student_id) = ''
           OR trim(first_name) = '' OR trim(last_name) = '')
    UNION ALL SELECT 'must not', 'no teacher with a blank name', NOT EXISTS (
        SELECT 1 FROM teachers WHERE trim(first_name) = '' OR trim(last_name) = '')
    UNION ALL SELECT 'must not', 'no second CSPC 103, no units <= 0, no temporary subject', NOT EXISTS (
        SELECT 1 FROM subjects WHERE units <= 0 OR subject_code NOT IN ('CSPC 103', 'PATHFIT 3'))
    UNION ALL SELECT 'must not', 'no class without teacher, subject or term', NOT EXISTS (
        SELECT 1 FROM class_offerings WHERE teacher_id IS NULL OR subject_id IS NULL
           OR trim(school_year) = '' OR trim(semester) = '')
    UNION ALL SELECT 'must not', 'no enrollment for 2026-9999 or 2026-0098, no duplicate', NOT EXISTS (
        SELECT 1 FROM enrollments WHERE student_id IN ('2026-9999', '2026-0098'))
        AND NOT EXISTS (SELECT 1 FROM enrollments GROUP BY student_id, class_id HAVING count(*) > 1)
    UNION ALL SELECT 'must not', 'no negative weight, every period totals 100', NOT EXISTS (
        SELECT 1 FROM grade_percentages WHERE percentage < 0)
        AND NOT EXISTS (
            SELECT 1 FROM grade_percentages w JOIN grade_components gc ON gc.component_id = w.component_id
            GROUP BY w.class_id, gc.period_id HAVING sum(w.percentage) <> 100)
    UNION ALL SELECT 'must not', 'no score above max or negative', NOT EXISTS (
        SELECT 1 FROM grade_component_scores s JOIN grade_components gc ON gc.component_id = s.component_id
        WHERE s.score < 0 OR s.score > gc.max_score)
    UNION ALL SELECT 'must not', 'no score for 2026-0098, no duplicate score row', NOT EXISTS (
        SELECT 1 FROM score_rows WHERE student_id = '2026-0098')
        AND NOT EXISTS (SELECT 1 FROM grade_component_scores GROUP BY enrollment_id, component_id HAVING count(*) > 1)
    UNION ALL SELECT 'must not', 'no second GRADE row per enrollment', NOT EXISTS (
        SELECT 1 FROM grades GROUP BY enrollment_id HAVING count(*) > 1)
)
SELECT section, name, CASE WHEN ok THEN 'PASS' ELSE 'FAIL' END AS result FROM checks;

SELECT * FROM appendix_checks;
SELECT count(*) FILTER (WHERE result = 'PASS') AS passed,
       count(*) FILTER (WHERE result = 'FAIL') AS failed
FROM appendix_checks;
