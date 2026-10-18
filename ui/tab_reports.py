# tab_reports.py - Tab for generating and exporting academic reports

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

from services.class_service import ClassService
from services.student_service import StudentService
from services import ReportService


class ReportsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.class_service = ClassService()
        self.student_service = StudentService()
        self.report_service = ReportService()

        self.class_map = {}
        self.student_map = {}
        self.current_report_data = None
        self.current_report_type = "Class List"

        self._build_ui()
        self.load_dropdowns()

    def _build_ui(self):
        # 1. Report Selector & Filter Controls
        ctrl_frame = ttk.LabelFrame(self, text="Select Report Type & Scope")
        ctrl_frame.pack(fill="x", padx=10, pady=6)

        f1 = ttk.Frame(ctrl_frame)
        f1.pack(fill="x", padx=6, pady=4)

        ttk.Label(f1, text="Report Type:").pack(side="left", padx=4)
        self.cb_report_type = ttk.Combobox(
            f1, values=["Class List", "Grade Sheet", "Student Grade Report"],
            width=22, state="readonly"
        )
        self.cb_report_type.set("Class List")
        self.cb_report_type.pack(side="left", padx=4)
        self.cb_report_type.bind("<<ComboboxSelected>>", self.on_report_type_change)

        self.lbl_filter = ttk.Label(f1, text="Class Offering:")
        self.lbl_filter.pack(side="left", padx=(15, 4))
        self.cb_filter = ttk.Combobox(f1, width=32, state="readonly")
        self.cb_filter.pack(side="left", padx=4)

        ttk.Button(f1, text="Generate Report", command=self.generate_report).pack(side="left", padx=8)
        ttk.Button(f1, text="Export / Save to File", command=self.export_report).pack(side="left", padx=4)

        # 2. Notebook with Document View and Table View
        self.nb_views = ttk.Notebook(self)
        self.nb_views.pack(fill="both", expand=True, padx=10, pady=6)

        # Tab A: Formatted Document View
        self.doc_frame = ttk.Frame(self.nb_views)
        self.nb_views.add(self.doc_frame, text="Document View")

        self.txt_preview = tk.Text(self.doc_frame, wrap="none", font=("Consolas", 10), bg="#fcfcfc")
        scroll_y = ttk.Scrollbar(self.doc_frame, orient="vertical", command=self.txt_preview.yview)
        scroll_x = ttk.Scrollbar(self.doc_frame, orient="horizontal", command=self.txt_preview.xview)
        self.txt_preview.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.txt_preview.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        # Tab B: Grid Table View
        self.grid_frame = ttk.Frame(self.nb_views)
        self.nb_views.add(self.grid_frame, text="Data Table View")

        self.tree = ttk.Treeview(self.grid_frame, show="headings")
        t_scroll_y = ttk.Scrollbar(self.grid_frame, orient="vertical", command=self.tree.yview)
        t_scroll_x = ttk.Scrollbar(self.grid_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=t_scroll_y.set, xscrollcommand=t_scroll_x.set)

        self.tree.pack(side="left", fill="both", expand=True)
        t_scroll_y.pack(side="right", fill="y")
        t_scroll_x.pack(side="bottom", fill="x")

    def load_dropdowns(self):
        try:
            classes = self.class_service.find_all()
            self.class_map = {f"{c.class_code} - {c.subject_name or c.subject_code} ({c.section or 'N/A'})": c.class_id for c in classes}

            students = self.student_service.find_all()
            self.student_map = {f"{s.full_name} ({s.email})": s.student_id for s in students}

            self.on_report_type_change(None)
        except Exception:
            messagebox.showerror("Database Error", "Could not load report choices. Check the database connection.")

    def on_report_type_change(self, event):
        rtype = self.cb_report_type.get()
        self.current_report_type = rtype

        if rtype in ["Class List", "Grade Sheet"]:
            self.lbl_filter.config(text="Class Offering:")
            self.cb_filter["values"] = list(self.class_map.keys())
            if self.class_map:
                self.cb_filter.current(0)
            else:
                self.cb_filter.set("")
        else:
            self.lbl_filter.config(text="Student:")
            self.cb_filter["values"] = list(self.student_map.keys())
            if self.student_map:
                self.cb_filter.current(0)
            else:
                self.cb_filter.set("")

    def generate_report(self):
        filter_val = self.cb_filter.get()
        if not filter_val:
            messagebox.showwarning("Validation", "Please select a target class or student.")
            return

        rtype = self.cb_report_type.get()
        try:
            if rtype == "Class List":
                offering_id = self.class_map.get(filter_val)
                data = self.report_service.generate_class_list_report(offering_id)
                self.current_report_data = data
                self._display_class_list(data)
            elif rtype == "Grade Sheet":
                offering_id = self.class_map.get(filter_val)
                data = self.report_service.generate_grade_sheet_report(offering_id)
                self.current_report_data = data
                self._display_grade_sheet(data)
            elif rtype == "Student Grade Report":
                student_id = self.student_map.get(filter_val)
                data = self.report_service.generate_student_grade_report(student_id)
                self.current_report_data = data
                self._display_student_report(data)
        except ValueError as error:
            messagebox.showwarning("Report", str(error))
        except Exception:
            messagebox.showerror("Report", "Could not generate the report. Check the database connection.")

    def _display_class_list(self, data):
        # document preview text
        doc = [
            "=" * 78,
            f"{'NOTRE DAME OF MARBEL UNIVERSITY':^78}",
            f"{'COLLEGE OF ENGINEERING, ARCHITECTURE & COMPUTING':^78}",
            f"{'COMPUTER STUDIES DEPARTMENT':^78}",
            f"{'OFFICIAL CLASS LIST':^78}",
            "=" * 78,
            f"Class Code:  {data['class_code']:<25} Subject:     {data['subject_code']} - {data['subject_name']}",
            f"Teacher:     {data['teacher_name']:<25} Section:     {data['section']}",
            f"Schedule:    {data['schedule']:<25} Room:        {data['room']}",
            f"School Year: {data['school_year']:<25} Semester:    {data['semester']}",
            "-" * 78,
            f"{'No.':<4} {'Student Name':<28} {'Email':<25} {'Program':<10} {'Status':<8}",
            "-" * 78,
        ]
        for s in data["students"]:
            doc.append(f"{s['no']:<4} {s['student_name']:<28} {s['email']:<25} {s['program']:<10} {s['status']:<8}")
        doc.extend([
            "-" * 78,
            f"Total Enrolled Students: {data['total_students']}",
            "",
            "Generated by Student Information and Grading System (CSPC 103)",
            "=" * 78
        ])

        self.txt_preview.delete("1.0", "end")
        self.txt_preview.insert("1.0", "\n".join(doc))

        # treeview table
        cols = ("no", "student_name", "email", "program", "enroll_date", "status")
        self._setup_tree(cols, ["No.", "Student Name", "Email", "Program", "Enroll Date", "Status"])
        for s in data["students"]:
            self.tree.insert("", "end", values=(s["no"], s["student_name"], s["email"], s["program"], s["enroll_date"], s["status"]))

    def _display_grade_sheet(self, data):
        doc = [
            "=" * 85,
            f"{'NOTRE DAME OF MARBEL UNIVERSITY':^85}",
            f"{'COLLEGE OF ENGINEERING, ARCHITECTURE & COMPUTING':^85}",
            f"{'OFFICIAL CLASS GRADE SHEET':^85}",
            "=" * 85,
            f"Class Code:  {data['class_code']:<25} Subject:  {data['subject_code']} - {data['subject_name']}",
            f"Teacher:     {data['teacher_name']:<25} Section:  {data['section']}",
            f"School Year: {data['school_year']:<25} Semester: {data['semester']}",
            "-" * 85,
            f"{'No.':<4} {'Student Name':<26} {'Midterm':<10} {'Finals':<10} {'Overall':<10} {'Rating':<8} {'Remarks':<10}",
            "-" * 85,
        ]
        for g in data["grades"]:
            doc.append(f"{g['no']:<4} {g['student_name']:<26} {g['midterm_grade']:<10} {g['finals_grade']:<10} {g['final_grade']:<10} {g['rating']:<8} {g['remarks']:<10}")
        doc.extend([
            "-" * 85,
            f"Total Students: {len(data['grades'])}",
            "",
            "Instructor's Signature: __________________________   Date: __________________",
            "=" * 85
        ])

        self.txt_preview.delete("1.0", "end")
        self.txt_preview.insert("1.0", "\n".join(doc))

        cols = ("no", "student_name", "midterm", "finals", "overall", "rating", "remarks")
        self._setup_tree(cols, ["No.", "Student Name", "Midterm Grade", "Finals Grade", "Final Grade", "Rating", "Remarks"])
        for g in data["grades"]:
            self.tree.insert("", "end", values=(
                g["no"], g["student_name"], g["midterm_grade"], g["finals_grade"], g["final_grade"], g["rating"], g["remarks"]
            ))

    def _display_student_report(self, data):
        doc = [
            "=" * 80,
            f"{'NOTRE DAME OF MARBEL UNIVERSITY':^80}",
            f"{'OFFICIAL STUDENT ACADEMIC GRADE REPORT':^80}",
            "=" * 80,
            f"Student Name: {data['student_name']:<30} Program: {data['program']}",
            f"Email:        {data['email']:<30} Status:  {data['status']}",
            "-" * 80,
            f"{'Code':<10} {'Subject Name':<28} {'Units':<6} {'Midterm':<9} {'Finals':<9} {'Grade':<8} {'Rating':<7} {'Remarks':<8}",
            "-" * 80,
        ]
        for c in data["courses"]:
            doc.append(f"{c['class_code']:<10} {c['subject_name'][:26]:<28} {c['units']:<6} {c['midterm']:<9} {c['finals']:<9} {c['final_grade']:<8} {c['rating']:<7} {c['remarks']:<8}")
        doc.extend([
            "-" * 80,
            f"Total Units: {data['total_units']:<20} General Weighted Average (GWA): {data['gwa']}",
            "",
            "Dean / Registrar Signature: ______________________   Date: __________________",
            "=" * 80
        ])

        self.txt_preview.delete("1.0", "end")
        self.txt_preview.insert("1.0", "\n".join(doc))

        cols = ("code", "name", "units", "teacher", "midterm", "finals", "final_grade", "rating", "remarks")
        self._setup_tree(cols, ["Class Code", "Subject Name", "Units", "Teacher", "Midterm", "Finals", "Final Grade", "Rating", "Remarks"])
        for c in data["courses"]:
            self.tree.insert("", "end", values=(
                c["class_code"], c["subject_name"], c["units"], c["teacher"],
                c["midterm"], c["finals"], c["final_grade"], c["rating"], c["remarks"]
            ))

    def _setup_tree(self, cols, headings):
        for r in self.tree.get_children():
            self.tree.delete(r)
        self.tree["columns"] = cols
        for col, head in zip(cols, headings):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=110, stretch=True)

    def export_report(self):
        content = self.txt_preview.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("Empty", "Generate a report first.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt"), ("CSV File", "*.csv"), ("All Files", "*.*")],
            title="Save Academic Report"
        )
        if not file_path:
            return

        try:
            if file_path.endswith(".csv") and self.current_report_data:
                self._export_csv(file_path)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            messagebox.showinfo("Export Successful", f"Report saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def _export_csv(self, file_path):
        data = self.current_report_data
        rtype = self.current_report_type
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if rtype == "Class List":
                writer.writerow(["No.", "Student ID", "Student Name", "Email", "Program", "Status"])
                for s in data["students"]:
                    writer.writerow([s["no"], s["student_id"], s["student_name"], s["email"], s["program"], s["status"]])
            elif rtype == "Grade Sheet":
                writer.writerow(["No.", "Student Name", "Midterm Grade", "Finals Grade", "Final Grade", "Rating", "Remarks"])
                for g in data["grades"]:
                    writer.writerow([g["no"], g["student_name"], g["midterm_grade"], g["finals_grade"], g["final_grade"], g["rating"], g["remarks"]])
            elif rtype == "Student Grade Report":
                writer.writerow(["Class Code", "Subject Name", "Units", "Teacher", "Midterm", "Finals", "Final Grade", "Rating", "Remarks"])
                for c in data["courses"]:
                    writer.writerow([c["class_code"], c["subject_name"], c["units"], c["teacher"], c["midterm"], c["finals"], c["final_grade"], c["rating"], c["remarks"]])
