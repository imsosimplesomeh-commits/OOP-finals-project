import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import psycopg2

import db
from main import StudentGradeManagementApp
from tests import test_checklist_flow


class TestGuiChecklist(unittest.TestCase):
    def setUp(self):
        self.flow = test_checklist_flow.TestChecklistFlow()
        self.flow.setUp()
        self.addCleanup(self.flow.doCleanups)
        connect = psycopg2.connect

        def test_connection(*args, **kwargs):
            # every app connection stays inside this test's schema
            self.assertEqual(kwargs.get("dbname"), self.flow.config["dbname"])
            kwargs["options"] = "-c search_path=" + self.flow.schema
            return connect(*args, **kwargs)

        self.enterContext(patch.dict(db.DB_CONFIG, self.flow.config))
        self.enterContext(patch("psycopg2.connect", side_effect=test_connection))
        self.info = self.enterContext(patch("tkinter.messagebox.showinfo"))
        self.warning = self.enterContext(patch("tkinter.messagebox.showwarning"))
        self.error = self.enterContext(patch("tkinter.messagebox.showerror"))
        self.confirm = self.enterContext(patch("tkinter.messagebox.askyesno", return_value=True))
        self.app = None
        self.open_app()
        self.addCleanup(self.close_app)

    def open_app(self):
        self.app = StudentGradeManagementApp()
        self.app.withdraw()
        self.callback_errors = []
        self.app.report_callback_exception = lambda *error: self.callback_errors.append(error)
        self.app.update()

    def close_app(self):
        if self.app is not None:
            self.app.destroy()
            self.app = None

    def select_record(self, tree, record_id, callback):
        item = next(item for item in tree.get_children()
                    if tree.item(item, "values")[0] == str(record_id))
        tree.selection_set(item)
        callback(None)

    def refresh_view(self, case_id):
        group = case_id.split("-")[0]
        if group in ("ST", "TE", "SU", "PS"):
            self.app.notebook.select(self.app.tab_mgmt)
            self.app.tab_mgmt.refresh()
            views = [(self.app.tab_mgmt.student_view, self.flow.students),
                     (self.app.tab_mgmt.teacher_view, self.flow.teachers),
                     (self.app.tab_mgmt.subject_view, self.flow.subjects)]
            for view, repo in views:
                self.assertEqual(len(view.tree.get_children()), len(repo.find_all()))
        elif group in ("CL", "EN", "GP", "GC", "GW"):
            self.app.notebook.select(self.app.tab_class)
            tab = self.app.tab_class
            tab.refresh_all()
            self.assertEqual(len(tab.tree_classes.get_children()), len(self.flow.classes.find_all()))
            if hasattr(self.flow, "main_class"):
                self.select_record(tab.tree_classes, self.flow.main_class.class_id, tab.on_class_select)
                self.assertEqual(len(tab.tree_enrollments.get_children()),
                                 len(self.flow.enrollments.find_by_offering(self.flow.main_class.class_id)))
            self.assertEqual(len(tab.tree_comps.get_children()), len(self.flow.components.find_all()))
        elif group in ("SC", "GR"):
            self.app.notebook.select(self.app.tab_grading)
            tab = self.app.tab_grading
            tab.refresh_all()
            self.assertEqual(len(tab.tree_grades.get_children()), 3)
            for enrollment in self.flow.enrollment_list:
                choice = next(name for name, value in tab.student_map.items()
                              if value == enrollment.enrollment_id)
                tab.cb_student.set(choice)
                tab.on_student_change(None)
                rows = [tab.tree_student_scores.item(item, "values")
                        for item in tab.tree_student_scores.get_children()]
                expected = self.flow.scores.find_by_enrollment(enrollment.enrollment_id)
                self.assertEqual({row[1]: float(row[4]) for row in rows},
                                 {score.component_id: float(score.score) for score in expected})
        elif group == "RP":
            self.show_report(case_id)
        self.app.update()
        self.error.assert_not_called()
        self.assertEqual(self.callback_errors, [])

    def show_report(self, case_id):
        self.app.notebook.select(self.app.tab_reports)
        tab = self.app.tab_reports
        tab.load_dropdowns()
        report_type = {"RP-01": "Class List", "RP-02": "Grade Sheet"}.get(case_id, "Student Grade Report")
        tab.cb_report_type.set(report_type)
        tab.on_report_type_change(None)
        tab.generate_report()
        self.assertTrue(tab.current_report_data)
        self.assertIn(tab.current_report_data["title"], tab.txt_preview.get("1.0", "end"))
        self.assertNotIn("Semester Semester", tab.txt_preview.get("1.0", "end"))
        return tab.current_report_data

    def export_report(self, folder, case_id):
        path = Path(folder) / (case_id + ".pdf")
        with patch("ui.tab_reports.filedialog.asksaveasfilename", return_value=str(path)):
            self.app.tab_reports.export_pdf()
        self.assertTrue(path.read_bytes().startswith(b"%PDF-"))
        self.assertTrue(path.read_bytes().rstrip().endswith(b"%%EOF"))
        self.error.assert_not_called()

    def check_restart(self):
        before = self.flow.snapshot()
        expected = self.flow.report.generate_grade_sheet_report(self.flow.main_class.class_id)
        self.close_app()
        # a new python process opens the app and reads the saved report
        script = """
import json
from unittest.mock import patch
from main import StudentGradeManagementApp
with patch('tkinter.messagebox.showerror', side_effect=RuntimeError('GUI load failed')):
    app = StudentGradeManagementApp()
    app.withdraw()
    app.update()
    tab = app.tab_reports
    tab.cb_report_type.set('Grade Sheet')
    tab.on_report_type_change(None)
    tab.generate_report()
    print(json.dumps(tab.current_report_data))
    app.destroy()
"""
        env = dict(os.environ, PGDATABASE=self.flow.config["dbname"],
                   PGOPTIONS="-c search_path=" + self.flow.schema)
        result = subprocess.run([sys.executable, "-c", script], env=env,
                                capture_output=True, text=True, timeout=30, check=True)
        self.assertEqual(json.loads(result.stdout), expected)
        self.assertEqual(self.flow.snapshot(), before)
        self.open_app()

    def test_cases_pdf_and_reset(self):
        with tempfile.TemporaryDirectory() as folder:
            for case_id, action in self.flow.checklist_cases():
                with self.subTest(case_id=case_id, phase=action.__name__):
                    action()
                    if case_id == "PS-01":
                        self.check_restart()
                    elif case_id.startswith("RP-"):
                        self.refresh_view(case_id)
                        self.export_report(folder, case_id)
                    elif case_id != "report setup":
                        self.refresh_view(case_id)
                    if case_id == "GR-02":
                        tab = self.app.tab_grading
                        tab.selected_enrollment_id = self.flow.enrollment_list[2].enrollment_id
                        tab.calculate_selected_student()
                        self.assertIn("Finals: 93.70 (1.50)", self.info.call_args.args[1])
                    print(case_id, action.__name__, "PASS", flush=True)

            for table, count in test_checklist_flow.ROW_COUNTS.items():
                self.assertEqual(len(self.flow.rows(table)), count, table)
            self.assertGreaterEqual(len(self.flow.rows("audit_log")), 7)

            self.show_report("RP-03")
            tab = self.app.tab_reports
            with patch("ui.tab_reports.filedialog.asksaveasfilename", return_value=""), \
                    patch("ui.tab_reports.export_pdf") as writer:
                tab.export_pdf()
                writer.assert_not_called()
            with patch("ui.tab_reports.filedialog.asksaveasfilename", return_value=str(Path(folder) / "blocked.pdf")), \
                    patch("ui.tab_reports.export_pdf", side_effect=PermissionError):
                tab.export_pdf()
                self.error.assert_called_once()
            self.error.reset_mock()

            before = self.flow.snapshot()
            self.confirm.return_value = False
            self.app._reset_database()
            self.assertEqual(self.flow.snapshot(), before)
            self.assertEqual(self.confirm.call_args.kwargs["default"], "no")
            self.confirm.return_value = True
            self.app._reset_database()
            self.app.update()
            self.assertTrue(all(not rows for rows in self.flow.snapshot().values()))
            self.assertIsNone(self.app.tab_reports.current_report_data)
            self.assertEqual(self.app.tab_reports.txt_preview.get("1.0", "end").strip(), "")
            self.assertEqual(self.app.tab_class.selected_offering_id, None)
            self.assertEqual(self.app.tab_grading.selected_enrollment_id, None)
            self.error.assert_not_called()
            self.assertEqual(self.callback_errors, [])
            with patch("ui.tab_reports.filedialog.asksaveasfilename") as dialog:
                self.app.tab_reports.export_pdf()
                dialog.assert_not_called()
            subject = self.flow.subject.save(test_checklist_flow.Subject(
                subject_code="NEW", subject_name="New Subject", units=3))
            self.assertEqual(subject.subject_id, "1")
            print("PDF cancel/error, reset cancel/confirm, empty views, ID restart PASS", flush=True)

    def test_reset_failure_preserves_records(self):
        self.flow.case_st01()
        conn = self.flow.connect()
        try:
            with conn, conn.cursor() as cur:
                cur.execute("CREATE TABLE outside_table (student_id TEXT REFERENCES students(student_id))")
        finally:
            conn.close()
        before = self.flow.snapshot()
        self.app._reset_database()
        self.error.assert_called_once()
        self.assertEqual(self.flow.snapshot(), before)
        self.assertIn("No records were cleared", self.error.call_args.args[1])
