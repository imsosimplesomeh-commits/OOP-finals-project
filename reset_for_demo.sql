-- reset_for_demo.sql - empties every table and restarts all ids at 1, keeping the schema
-- WARNING: this deletes all rows. Run it only on the database you mean to clear, for example:
--   psql -U postgres -d Modelo_CSPC103 -f reset_for_demo.sql
-- It does the same as the Reset Database button in the app.

TRUNCATE TABLE grade_component_scores, grades, grade_percentages,
    enrollments, grade_components, grading_periods, class_offerings,
    students, teachers, subjects, audit_log
RESTART IDENTITY;
