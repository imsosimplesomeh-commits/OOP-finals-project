# rehearse_52.py - runs the 52 test cases in order, with the checklist data, on a practice database
# Usage:  python rehearse_52.py
# It uses its own database (default Modelo_CSPC103_rehearsal), so your demo database is never touched.
# The practice database is emptied first, then the cases run in checklist order.

import os
import sys

# choose the practice database BEFORE importing db.py, because db.py reads the name when it loads
os.environ.setdefault("PGDATABASE", "Modelo_CSPC103_rehearsal")
if os.environ["PGDATABASE"] == "Modelo_CSPC103":
    sys.exit("Stop: this script empties its database. Use a different PGDATABASE than the demo one.")

from db import init_db, reset_database, get_connection
from models import Student, Teacher, Subject, ClassOffering, GradeComponent, GradeComponentScore
from services.student_service import StudentService
from services.teacher_service import TeacherService
from services.subject_service import SubjectService
from services.class_service import ClassService
from services.enrollment_service import EnrollmentService
from services.configuration_service import ConfigurationService
from services.score_service import ScoreService
from services.grading_service import GradingService
from services.report_service import ReportService

students = StudentService()
teachers = TeacherService()
subjects = SubjectService()
classes = ClassService()
enrollments = EnrollmentService()
config = ConfigurationService()
scores = ScoreService()
grading = GradingService()
reports = ReportService()

results = []  # (test case, passed, detail)


def check(test_case, passed, detail=""):
    results.append((test_case, passed))
    print(("PASS  " if passed else "FAIL  ") + test_case + ("  " + detail if detail else ""))


def is_rejected(action, *words):
    # True when the action raises an error whose message contains every word
    try:
        action()
    except ValueError as error:
        message = str(error).lower()
        return all(word.lower() in message for word in words)
    return False


def query(sql, params=()):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def count_rows(table):
    return query("SELECT COUNT(*) FROM " + table)[0][0]  # table names here are fixed words, not user input


def new_student(student_id, first, last, program, year):
    return Student(student_id=student_id, first_name=first, last_name=last, program=program, year_level=year)


def new_class(code, subject_id, teacher_id, room, schedule):
    return classes.save(ClassOffering(
        class_code=code, subject_id=subject_id, teacher_id=teacher_id, section="A",
        school_year="2026-2027", semester="1st", schedule=schedule, room=room))


# ---------------- Part A: master records and enrollment ----------------
def part_a():
    for sid, first, last, program in [("2026-0001", "Juan", "Dela Cruz", "BSCS"),
                                      ("2026-0002", "Pedro", "Reyes", "BSCS"),
                                      ("2026-0003", "Ana", "Garcia", "BSIT")]:
        students.add(new_student(sid, first, last, program, 2))
    check("ST-01", count_rows("students") == 3)
    check("ST-02", is_rejected(lambda: students.add(new_student("2026-0001", "X", "Y", "BSCS", 2)), "already")
          and count_rows("students") == 3)
    check("ST-03", is_rejected(lambda: students.add(new_student("2026-0100", "", "Y", "BSCS", 2)), "required")
          and is_rejected(lambda: students.add(new_student("", "X", "Y", "BSCS", 2)), "required")
          and count_rows("students") == 3)
    check("ST-04", [s.student_id for s in students.search("Reyes")] == ["2026-0002"])
    ana = students.find_by_id("2026-0003")
    ana.program = "BSCS"
    students.update(ana, "2026-0003")
    ana = students.find_by_id("2026-0003")
    check("ST-05", ana.program == "BSCS" and ana.first_name == "Ana" and ana.year_level == 2)
    students.add(new_student("2026-0099", "Lea", "Ramos", "BSIT", 1))
    students.delete("2026-0099")
    check("ST-06", students.find_by_id("2026-0099") is None)

    teachers.add(Teacher(teacher_id="T-1001", first_name="Maria", last_name="Santos",
                         department="Computer Studies Department"))
    check("TE-01", count_rows("teachers") == 1)
    check("TE-02", is_rejected(lambda: teachers.add(Teacher(teacher_id="T-1001", first_name="A", last_name="B", department="D")), "already")
          and is_rejected(lambda: teachers.add(Teacher(teacher_id="T-1009", first_name="", last_name="B", department="D")), "required")
          and count_rows("teachers") == 1)
    check("TE-03", teachers.find_by_id("T-1001").department == "Computer Studies Department")
    maria = teachers.find_by_id("T-1001")
    maria.department = "Information Technology Department"
    teachers.update(maria, "T-1001")
    check("TE-04", teachers.find_by_id("T-1001").department == "Information Technology Department")

    subjects.save(Subject(subject_code="CSPC 103", subject_name="Object Oriented Programming", units=3))
    check("SU-01", count_rows("subjects") == 1)
    check("SU-02", is_rejected(lambda: subjects.save(Subject(subject_code="CSPC 103", subject_name="X", units=3)), "already")
          and is_rejected(lambda: subjects.save(Subject(subject_code="ZZ 1", subject_name="X", units=0)), "units")
          and is_rejected(lambda: subjects.save(Subject(subject_code="ZZ 2", subject_name="X", units=-2)), "units")
          and count_rows("subjects") == 1)
    check("SU-03", [s.subject_code for s in subjects.find_all()] == ["CSPC 103"])
    cspc = subjects.find_by_id("1")
    cspc.description = "Object-oriented analysis, design and programming in Java"
    subjects.save(cspc)
    check("SU-04", subjects.find_by_id("1").description.startswith("Object-oriented analysis"))
    temp = subjects.save(Subject(subject_code="TMP 101", subject_name="Temporary 1", units=1))
    subjects.delete(temp.subject_id)  # the unused subject is deleted (part 1 of SU-05)

    new_class("CSPC103-A", "1", "T-1001", "CS-201", "MWF 9:00-10:00")
    check("CL-01", count_rows("class_offerings") == 1)
    blanks = []
    for field in ("teacher_id", "subject_id", "school_year"):
        bad = ClassOffering(class_code="BAD", subject_id="1", teacher_id="T-1001", section="A",
                            school_year="2026-2027", semester="1st")
        setattr(bad, field, "")
        blanks.append(is_rejected(lambda: classes.save(bad), "required"))
    check("CL-02", all(blanks) and count_rows("class_offerings") == 1)
    check("CL-03", [c.class_code for c in classes.find_all() if c.teacher_id == "T-1001"] == ["CSPC103-A"])
    offering = classes.find_by_id("1")
    offering.room, offering.schedule = "CS-202", "TTh 1:00-2:30"
    classes.save(offering)
    offering = classes.find_by_id("1")
    check("CL-04", offering.room == "CS-202" and offering.schedule == "TTh 1:00-2:30")

    for sid in ("2026-0001", "2026-0002", "2026-0003"):
        enrollments.enroll_student(sid, "1")
    check("EN-01", count_rows("enrollments") == 3)
    check("ST-07", is_rejected(lambda: students.delete("2026-0001"), "enrollments")
          and students.find_by_id("2026-0001") is not None)
    check("TE-05", is_rejected(lambda: teachers.delete("T-1001"), "CSPC103-A"))
    check("SU-05", is_rejected(lambda: subjects.delete("1"), "CSPC103-A") and subjects.find_by_id("2") is None)
    check("CL-05", is_rejected(lambda: classes.delete("1"), "enrollments"))
    check("EN-02", enrollments.enroll_student("2026-0001", "1")[0] is False and count_rows("enrollments") == 3)
    check("EN-03", enrollments.enroll_student("2026-9999", "1")[0] is False and count_rows("enrollments") == 3)
    check("EN-04", len(enrollments.get_class_enrollments("1")) == 3)
    pedro = [e for e in enrollments.get_class_enrollments("1") if e.student_id == "2026-0002"][0]
    enrollments.update_status(pedro.enrollment_id, "Dropped")
    dropped = enrollments.enrollment_repo.find_by_id(pedro.enrollment_id).status
    enrollments.update_status(pedro.enrollment_id, "Enrolled")
    back = enrollments.enrollment_repo.find_by_id(pedro.enrollment_id).status
    check("EN-05", dropped == "Dropped" and back == "Enrolled")
    students.add(new_student("2026-0098", "Carlo", "Mendoza", "BSIT", 1))
    _, _, carlo = enrollments.enroll_student("2026-0098", "1")
    enrollments.remove_enrollment(carlo.enrollment_id)  # part 1 of EN-06


# ---------------- Part B: grading, computation, reports ----------------
COMPONENTS = [("Midterm Quiz", "Quiz", 50), ("Midterm Laboratory/Project", "Laboratory", 100),
              ("Midterm Examination", "Exam", 100), ("Final Quiz", "Quiz", 50),
              ("Final Laboratory/Project", "Laboratory", 100), ("Final Examination", "Exam", 100)]


def set_weights(class_id, period, component_ids, weights):
    values = list(zip(component_ids, weights))
    config.save_weights(class_id, period.period_id, values, changed_by="tester")


def part_b():
    midterm = config.add_period("Midterm", 1, "2026-2027", "1st")
    finals = config.add_period("Finals", 2, "2026-2027", "1st")
    check("GP-01", count_rows("grading_periods") == 2)
    ids = []
    for name, kind, max_score in COMPONENTS:
        period = midterm if name.startswith("Midterm") else finals
        ids.append(config.add_component(GradeComponent(
            period_id=period.period_id, name=name, type=kind, max_score=max_score)).component_id)
    check("GC-01", count_rows("grade_components") == 6)
    mid_ids, fin_ids = ids[:3], ids[3:]
    set_weights("1", midterm, mid_ids, [20, 30, 50])
    set_weights("1", finals, fin_ids, [20, 30, 50])
    check("GW-01", count_rows("grade_percentages") == 6)
    saved = lambda: [float(r[0]) for r in query("SELECT percentage FROM grade_percentages WHERE class_id = 1 ORDER BY component_id")]
    check("GW-02", is_rejected(lambda: set_weights("1", midterm, mid_ids, [20, 30, 40]), "100")
          and saved() == [20, 30, 50, 20, 30, 50])
    check("GW-03", is_rejected(lambda: set_weights("1", midterm, mid_ids, [-10, 60, 50]), "negative")
          and is_rejected(lambda: set_weights("1", midterm, mid_ids, ["", 30, 70]), "number"))
    check("GC-02", len(config.get_weights("1")) == 6, config.weight_summary("1"))

    raw = {"2026-0001": [40, 90, 57, 45, 85, 80],  # Juan's Midterm Exam is 57 first (fixed in SC-06)
           "2026-0002": [20, 60, 55, 30, 70, 65],
           "2026-0003": [50, 100, 100, 48, 95, 92]}
    enrollment_of = {e.student_id: e.enrollment_id for e in enrollments.get_class_enrollments("1")}

    def save_score(student_id, component_id, value):
        scores.save(GradeComponentScore(enrollment_id=enrollment_of[student_id], component_id=component_id, score=value),
                    changed_by="tester")

    for student_id, values in raw.items():
        for component_id, value in zip(ids, values):
            save_score(student_id, component_id, value)
    check("SC-01", count_rows("grade_component_scores") == 18)
    check("GC-03", is_rejected(lambda: config.delete_component(ids[0]), "score") and count_rows("grade_components") == 6)
    carlo_removed = query("SELECT COUNT(*) FROM enrollments WHERE student_id = '2026-0098'")[0][0] == 0
    juan_blocked = is_rejected(lambda: enrollments.remove_enrollment(enrollment_of["2026-0001"]), "scores")
    check("EN-06", carlo_removed and juan_blocked and count_rows("enrollments") == 3)
    check("SC-02", is_rejected(lambda: save_score("2026-0002", ids[0], 55), "maximum"))
    check("SC-03", is_rejected(lambda: save_score("2026-0001", ids[0], -5), "negative"))
    # Carlo (2026-0098) has no enrollment, so the app has no enrollment_id to attach a score to
    no_enrollment = lambda: scores.save(GradeComponentScore(enrollment_id="999", component_id=ids[0], score=10))
    check("SC-04", is_rejected(no_enrollment, "enrolled") and count_rows("grade_component_scores") == 18)
    check("SC-05", len(scores.get_scores(enrollment_of["2026-0001"])) == 6)
    save_score("2026-0001", ids[2], 75)
    juan_exam = query("SELECT COUNT(*), MAX(score) FROM grade_component_scores WHERE enrollment_id = %s AND component_id = %s",
                      (enrollment_of["2026-0001"], ids[2]))[0]
    check("SC-06", count_rows("grade_component_scores") == 18 and juan_exam == (1, 75))

    ana_quiz = query("SELECT score_id FROM grade_component_scores WHERE enrollment_id = %s AND component_id = %s",
                     (enrollment_of["2026-0003"], ids[3]))[0][0]
    scores.delete(ana_quiz, changed_by="tester")
    ana_finals = query("SELECT finals_grade FROM grades WHERE enrollment_id = %s", (enrollment_of["2026-0003"],))[0][0]
    save_score("2026-0003", ids[3], 48)
    ana_back = float(query("SELECT finals_grade FROM grades WHERE enrollment_id = %s", (enrollment_of["2026-0003"],))[0][0])
    check("SC-07", ana_finals is None and abs(ana_back - 93.70) <= 0.01)

    def grades_by_student(class_id):
        rows = query("SELECT e.student_id, g.midterm_grade, g.finals_grade, g.overall_grade, g.midterm_equiv, g.final_equiv "
                     "FROM grades g JOIN enrollments e ON e.enrollment_id = g.enrollment_id WHERE e.class_id = %s", (class_id,))
        return {r[0]: [float(x) for x in r[1:]] for r in rows}

    def close(actual, expected):
        return all(abs(a - e) <= 0.01 for a, e in zip(actual, expected))

    grading.bulk_compute_class_grades("1", changed_by="tester")
    got = grades_by_student("1")
    check("GR-01", close(got["2026-0001"][:1], [80.50]) and close(got["2026-0002"][:1], [53.50]) and close(got["2026-0003"][:1], [100.00])
          and [got[s][3] for s in ("2026-0001", "2026-0002", "2026-0003")] == [2.50, 5.00, 1.00])
    check("GR-02", close(got["2026-0001"][1:3], [83.50, 82.30]) and close(got["2026-0002"][1:3], [65.50, 60.70])
          and close(got["2026-0003"][1:3], [93.70, 96.22])
          and [got[s][4] for s in ("2026-0001", "2026-0002", "2026-0003")] == [2.25, 5.00, 1.25])
    set_weights("1", midterm, mid_ids, [30, 30, 40])
    grading.bulk_compute_class_grades("1", changed_by="tester")
    got = grades_by_student("1")
    check("GR-03", close(got["2026-0001"][:3], [81.00, 83.50, 82.50]) and close(got["2026-0002"][:3], [52.00, 65.50, 60.10])
          and close(got["2026-0003"][:3], [100.00, 93.70, 96.22]) and count_rows("grades") == 3)
    kinds = {(r[0], r[1]) for r in query("SELECT table_name, action FROM audit_log")}
    check("GR-04", ("GRADE_COMPONENT_SCORE", "UPDATE") in kinds and ("GRADE_COMPONENT_SCORE", "DELETE") in kinds
          and ("GRADE_COMPONENT_SCORE", "INSERT") in kinds and ("GRADE_PERCENTAGE", "UPDATE") in kinds
          and ("GRADE", "UPDATE") in kinds and count_rows("audit_log") >= 7)

    class_list = reports.generate_class_list_report("1")
    header = " ".join(class_list["header"])
    check("RP-01", [r[1] for r in class_list["rows"]] == ["Dela Cruz, Juan", "Garcia, Ana", "Reyes, Pedro"]
          and "Information Technology Department" in header and "TTh 1:00-2:30" in header and "CS-202" in header)
    sheet = reports.generate_grade_sheet_report("1")
    check("RP-02", [r[1:] for r in sheet["rows"]] == [["Dela Cruz, Juan", "BSCS", "2.50", "2.25"],
                                                      ["Garcia, Ana", "BSCS", "1.00", "1.25"],
                                                      ["Reyes, Pedro", "BSCS", "5.00", "5.00"]])

    # report setup records
    teachers.add(Teacher(teacher_id="T-1002", first_name="Jose", last_name="Ramos", department="Physical Education Department"))
    subjects.save(Subject(subject_code="PATHFIT 3", subject_name="Physical Activity Towards Health and Fitness 3", units=2))
    subject_id = [s.subject_id for s in subjects.find_all() if s.subject_code == "PATHFIT 3"][0]
    new_class("PATHFIT3-A", subject_id, "T-1002", "Gym", "TTh 3:00-5:00")
    _, _, juan_pathfit = enrollments.enroll_student("2026-0001", "2")
    set_weights("2", midterm, mid_ids, [20, 30, 50])
    set_weights("2", finals, fin_ids, [20, 30, 50])
    for component_id, value in zip(ids, [45, 90, 90, 45, 90, 90]):
        scores.save(GradeComponentScore(enrollment_id=juan_pathfit.enrollment_id, component_id=component_id, score=value),
                    changed_by="tester")
    grading.bulk_compute_class_grades("2", changed_by="tester")
    student_grade = reports.generate_student_grade_report("2026-0001")
    check("RP-03", [r[1:] for r in student_grade["rows"]] ==
          [["CSPC 103", "Object Oriented Programming", "Maria Santos", 3, "2.25"],
           ["PATHFIT 3", "Physical Activity Towards Health and Fitness 3", "Jose Ramos", 2, "1.75"]]
          and "Year: 2nd" in student_grade["header"][0])
    check("RP-04", student_grade["total_units"] == 5 and student_grade["subject_count"] == 2 and student_grade["gwa"] == "2.05",
          "GWA " + student_grade["gwa"])

    # persistence and security
    students.add(new_student("2026-0004", "Kevin", "O'Brien", "BSIT", 1))
    check("PS-02", students.find_by_id("2026-0004").last_name == "O'Brien" and students.search("' OR '1'='1") == [])
    print("PS-01 is done by hand: close the app, start it again, open the Grade Sheet.")


def compare_row_counts():
    expected = {"students": 5, "teachers": 2, "subjects": 2, "class_offerings": 2, "enrollments": 4,
                "grading_periods": 2, "grade_components": 6, "grade_percentages": 12,
                "grade_component_scores": 24, "grades": 4}
    print("\nRow counts against the Appendix:")
    all_match = True
    for table, wanted in expected.items():
        actual = count_rows(table)
        all_match = all_match and actual == wanted
        print(f"  {table:24s} {actual:3d}   expected {wanted:3d}   {'OK' if actual == wanted else 'DIFFERENT'}")
    audit = count_rows("audit_log")
    print(f"  {'audit_log':24s} {audit:3d}   expected 7 or more   {'OK' if audit >= 7 else 'DIFFERENT'}")
    return all_match and audit >= 7


if __name__ == "__main__":
    init_db()
    reset_database()
    part_a()
    part_b()
    counts_ok = compare_row_counts()
    failed = [name for name, passed in results if not passed]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks passed.", "Failed: " + ", ".join(failed) if failed else "")
    sys.exit(0 if not failed and counts_ok else 1)
