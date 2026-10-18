# tab_score_grading.py - Tab for score entry and grade calculations

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from models import GradeComponentScore
from repositories import (
    ClassRepository, EnrollmentRepository, GradeComponentRepository,
    GradingPeriodRepository, ScoreRepository, GradeRepository, GradePercentageRepository
)
from services import GradingService


class ScoreGradingTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.class_repo = ClassRepository()
        self.enrollment_repo = EnrollmentRepository()
        self.component_repo = GradeComponentRepository()
        self.period_repo = GradingPeriodRepository()
        self.score_repo = ScoreRepository()
        self.grade_repo = GradeRepository()
        self.percentage_repo = GradePercentageRepository()

        self.grading_service = GradingService(
            self.enrollment_repo, self.percentage_repo, self.component_repo,
            self.score_repo, self.grade_repo, self.period_repo
        )

        self.class_map = {}
        self.student_map = {}
        self.component_map = {}
        self.comp_max_scores = {}

        self.selected_offering_id = None
        self.selected_enrollment_id = None

        self._build_ui()
        self.load_classes()

    def _build_ui(self):
        # 1. Top filter bar
        top_bar = ttk.LabelFrame(self, text="Select Class & Weighting")
        top_bar.pack(fill="x", padx=10, pady=5)

        ttk.Label(top_bar, text="Class Offering:").pack(side="left", padx=5, pady=4)
        self.cb_class = ttk.Combobox(top_bar, width=32, state="readonly")
        self.cb_class.pack(side="left", padx=5, pady=4)
        self.cb_class.bind("<<ComboboxSelected>>", self.on_class_change)

        ttk.Label(top_bar, text="Midterm Weight %:").pack(side="left", padx=(15, 2))
        self.entry_mid_weight = ttk.Entry(top_bar, width=5)
        self.entry_mid_weight.insert(0, "40")
        self.entry_mid_weight.pack(side="left", padx=2)

        ttk.Label(top_bar, text="Finals Weight %:").pack(side="left", padx=(10, 2))
        self.entry_fin_weight = ttk.Entry(top_bar, width=5)
        self.entry_fin_weight.insert(0, "60")
        self.entry_fin_weight.pack(side="left", padx=2)

        ttk.Button(top_bar, text="Bulk Calculate All", command=self.bulk_calculate_grades).pack(side="right", padx=10, pady=4)
        ttk.Button(top_bar, text="Refresh", command=self.refresh_all).pack(side="right", padx=4, pady=4)

        # 2. Main split: score entry on left, class grade summary on right
        main_split = ttk.Frame(self)
        main_split.pack(fill="both", expand=True, padx=10, pady=5)

        # Left: score entry form
        left_frame = ttk.LabelFrame(main_split, text="Component Score Entry")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        f_entry = ttk.Frame(left_frame)
        f_entry.pack(fill="x", padx=6, pady=4)

        ttk.Label(f_entry, text="Student:").grid(row=0, column=0, padx=4, pady=3, sticky="e")
        self.cb_student = ttk.Combobox(f_entry, width=28, state="readonly")
        self.cb_student.grid(row=0, column=1, padx=4, pady=3, sticky="w")
        self.cb_student.bind("<<ComboboxSelected>>", self.on_student_change)

        ttk.Label(f_entry, text="Component:").grid(row=1, column=0, padx=4, pady=3, sticky="e")
        self.cb_comp = ttk.Combobox(f_entry, width=28, state="readonly")
        self.cb_comp.grid(row=1, column=1, padx=4, pady=3, sticky="w")
        self.cb_comp.bind("<<ComboboxSelected>>", self.on_comp_change)

        ttk.Label(f_entry, text="Max Score:").grid(row=2, column=0, padx=4, pady=3, sticky="e")
        self.lbl_max_score = ttk.Label(f_entry, text="--", font=("Segoe UI", 9, "bold"))
        self.lbl_max_score.grid(row=2, column=1, padx=4, pady=3, sticky="w")

        ttk.Label(f_entry, text="Raw Score:").grid(row=3, column=0, padx=4, pady=3, sticky="e")
        self.entry_raw_score = ttk.Entry(f_entry, width=15)
        self.entry_raw_score.grid(row=3, column=1, padx=4, pady=3, sticky="w")

        ttk.Label(f_entry, text="Remarks:").grid(row=4, column=0, padx=4, pady=3, sticky="e")
        self.entry_remarks = ttk.Entry(f_entry, width=28)
        self.entry_remarks.grid(row=4, column=1, padx=4, pady=3, sticky="w")

        btn_score_box = ttk.Frame(left_frame)
        btn_score_box.pack(fill="x", padx=6, pady=4)
        ttk.Button(btn_score_box, text="Save Score", command=self.save_score).pack(side="left", padx=4)
        ttk.Button(btn_score_box, text="Calculate Student", command=self.calculate_selected_student).pack(side="left", padx=4)
        ttk.Button(btn_score_box, text="Clear", command=self.clear_score_form).pack(side="left", padx=4)

        ttk.Label(left_frame, text="Recorded Scores for Selected Student:", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=8, pady=(8, 2))

        cols_s = ("comp_name", "type", "score", "max", "norm")
        self.tree_student_scores = ttk.Treeview(left_frame, columns=cols_s, show="headings", height=8)
        self.tree_student_scores.heading("comp_name", text="Component")
        self.tree_student_scores.heading("type", text="Category")
        self.tree_student_scores.heading("score", text="Score")
        self.tree_student_scores.heading("max", text="Max")
        self.tree_student_scores.heading("norm", text="Normalized")

        self.tree_student_scores.column("comp_name", width=120)
        self.tree_student_scores.column("type", width=80)
        self.tree_student_scores.column("score", width=55)
        self.tree_student_scores.column("max", width=55)
        self.tree_student_scores.column("norm", width=75)
        self.tree_student_scores.pack(fill="both", expand=True, padx=6, pady=4)

        # Right: consolidated class grades table
        right_frame = ttk.LabelFrame(main_split, text="Consolidated Class Grades")
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        cols_g = ("enrollment_id", "student_name", "midterm", "finals", "final_grade", "rating", "remarks")
        self.tree_grades = ttk.Treeview(right_frame, columns=cols_g, show="headings", height=14)
        self.tree_grades.heading("enrollment_id", text="Enrollment ID")
        self.tree_grades.heading("student_name", text="Student Name")
        self.tree_grades.heading("midterm", text="Midterm")
        self.tree_grades.heading("finals", text="Finals")
        self.tree_grades.heading("final_grade", text="Overall Final")
        self.tree_grades.heading("rating", text="Rating")
        self.tree_grades.heading("remarks", text="Remarks")

        self.tree_grades.column("enrollment_id", width=0, stretch=False)
        self.tree_grades.column("student_name", width=160)
        self.tree_grades.column("midterm", width=75)
        self.tree_grades.column("finals", width=75)
        self.tree_grades.column("final_grade", width=90)
        self.tree_grades.column("rating", width=65)
        self.tree_grades.column("remarks", width=85)

        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.tree_grades.yview)
        self.tree_grades.configure(yscrollcommand=scrollbar.set)
        self.tree_grades.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=4)

        self.tree_grades.bind("<<TreeviewSelect>>", self.on_grade_row_select)

    def refresh_all(self):
        self.load_classes()

    def load_classes(self):
        classes = self.class_repo.find_all()
        self.class_map = {f"{c.class_code} - {c.subject_name or c.subject_code} ({c.section or 'N/A'})": c.class_id for c in classes}
        self.cb_class["values"] = list(self.class_map.keys())
        if self.class_map and not self.selected_offering_id:
            self.cb_class.current(0)
            self.on_class_change(None)

    def on_class_change(self, event):
        disp = self.cb_class.get()
        if not disp:
            return
        self.selected_offering_id = self.class_map.get(disp)
        self.load_class_students()
        self.load_class_components()
        self.load_grades_table()

    def load_class_students(self):
        enrollments = self.enrollment_repo.find_by_offering(self.selected_offering_id)
        self.student_map = {f"{e.student_name}": e.enrollment_id for e in enrollments}
        self.cb_student["values"] = list(self.student_map.keys())
        if self.student_map:
            self.cb_student.current(0)
            self.selected_enrollment_id = list(self.student_map.values())[0]
            self.load_student_scores()
        else:
            self.selected_enrollment_id = None
            self.cb_student.set("")
            for r in self.tree_student_scores.get_children():
                self.tree_student_scores.delete(r)

    def load_class_components(self):
        comps = self.component_repo.find_by_offering(self.selected_offering_id)
        self.component_map = {}
        self.comp_max_scores = {}
        for c in comps:
            d = f"[{c.period_name or 'Period'}] {c.name} ({c.type})"
            self.component_map[d] = c.component_id
            self.comp_max_scores[c.component_id] = c.max_score
        self.cb_comp["values"] = list(self.component_map.keys())
        if self.component_map:
            self.cb_comp.current(0)
            self.on_comp_change(None)
        else:
            self.cb_comp.set("")
            self.lbl_max_score.config(text="--")

    def on_comp_change(self, event):
        disp = self.cb_comp.get()
        if not disp:
            return
        cid = self.component_map.get(disp)
        if cid:
            max_s = self.comp_max_scores.get(cid, 100.0)
            self.lbl_max_score.config(text=f"{max_s:.1f}")

    def on_student_change(self, event):
        disp = self.cb_student.get()
        if not disp:
            return
        self.selected_enrollment_id = self.student_map.get(disp)
        self.load_student_scores()

    def on_grade_row_select(self, event):
        sel = self.tree_grades.selection()
        if not sel:
            return
        vals = self.tree_grades.item(sel[0], "values")
        eid = vals[0]
        self.selected_enrollment_id = eid
        for disp, sid in self.student_map.items():
            if sid == eid:
                self.cb_student.set(disp)
                break
        self.load_student_scores()

    def load_student_scores(self):
        for r in self.tree_student_scores.get_children():
            self.tree_student_scores.delete(r)
        if not self.selected_enrollment_id:
            return

        scores = self.score_repo.find_by_enrollment(self.selected_enrollment_id)
        for s in scores:
            max_s = s.max_score or 100.0
            norm = (s.score / max_s * 100.0) if max_s > 0 else 0.0
            self.tree_student_scores.insert("", "end", values=(
                s.component_name or "Component", s.component_type or "N/A",
                f"{s.score:.1f}", f"{max_s:.1f}", f"{norm:.1f}%"
            ))

    def save_score(self):
        if not self.selected_enrollment_id:
            messagebox.showwarning("Validation", "Select an enrolled student.")
            return
        c_disp = self.cb_comp.get()
        if not c_disp:
            messagebox.showwarning("Validation", "Select a component.")
            return

        comp_id = self.component_map.get(c_disp)
        max_s = self.comp_max_scores.get(comp_id, 100.0)
        score_str = self.entry_raw_score.get().strip()

        if not score_str:
            messagebox.showwarning("Validation", "Enter a score.")
            return

        try:
            score_val = float(score_str)
            if score_val < 0:
                raise ValueError("Score cannot be negative.")
            if score_val > max_s:
                raise ValueError(f"Score ({score_val}) exceeds maximum allowed score ({max_s}).")
        except ValueError as ve:
            messagebox.showwarning("Invalid Score", str(ve))
            return

        remarks = self.entry_remarks.get().strip()
        score_obj = GradeComponentScore(
            enrollment_id=self.selected_enrollment_id,
            component_id=comp_id,
            score=score_val,
            remarks=remarks if remarks else None,
            date_recorded=date.today()
        )

        try:
            self.score_repo.save(score_obj)
            messagebox.showinfo("Success", f"Recorded score {score_val}/{max_s}.")
            self.load_student_scores()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record score: {e}")

    def _get_weights(self):
        try:
            mid = float(self.entry_mid_weight.get().strip())
            fin = float(self.entry_fin_weight.get().strip())
            if mid != 40 or fin != 60:
                raise ValueError()
            return mid, fin
        except ValueError:
            messagebox.showwarning("Invalid Weights", "Use 40% Midterm and 60% Finals.")
            return None

    def calculate_selected_student(self):
        if not self.selected_enrollment_id or not self.selected_offering_id:
            messagebox.showwarning("Validation", "Select a student to calculate grade.")
            return

        try:
            valid, msg = self.grading_service.validate_percentages(self.selected_offering_id)
            if not valid:
                messagebox.showwarning("Weight Configuration Error", msg)
                return
            weights = self._get_weights()
            if weights is None:
                return
            mid_w, fin_w = weights
            grade = self.grading_service.generate_and_save_grade(
                self.selected_enrollment_id, self.selected_offering_id, mid_w, fin_w
            )
            messagebox.showinfo(
                "Grade Computed",
                f"Midterm: {self.grade_text(grade.midterm_grade)}\n"
                f"Finals: {self.grade_text(grade.finals_grade)}\n"
                f"Overall Final Grade: {self.grade_text(grade.overall_grade)}\n"
                f"Remarks: {grade.remarks}"
            )
            self.load_grades_table()
        except ValueError as error:
            messagebox.showwarning("Grade Calculation", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not save the grade. Check the database connection.")

    def bulk_calculate_grades(self):
        if not self.selected_offering_id:
            messagebox.showwarning("Validation", "Select a class offering.")
            return

        try:
            valid, msg = self.grading_service.validate_percentages(self.selected_offering_id)
            if not valid:
                messagebox.showwarning("Weight Configuration Error", msg)
                return
            weights = self._get_weights()
            if weights is None:
                return
            mid_w, fin_w = weights
            grades = self.grading_service.bulk_compute_class_grades(
                self.selected_offering_id, mid_w, fin_w
            )
            messagebox.showinfo("Bulk Calculation", f"Successfully computed grades for {len(grades)} students.")
            self.load_grades_table()
        except ValueError as error:
            messagebox.showwarning("Grade Calculation", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not save grades. Check the database connection.")

    def grade_text(self, value):
        return "Incomplete" if value is None else f"{value:.2f}"

    def load_grades_table(self):
        for r in self.tree_grades.get_children():
            self.tree_grades.delete(r)
        if not self.selected_offering_id:
            return

        enrollments = self.enrollment_repo.find_by_offering(self.selected_offering_id)
        grades = self.grade_repo.find_by_offering(self.selected_offering_id)
        grade_map = {g.enrollment_id: g for g in grades}

        for en in enrollments:
            g = grade_map.get(en.enrollment_id)
            if g:
                mid_txt = self.grade_text(g.midterm_grade)
                fin_txt = self.grade_text(g.finals_grade)
                ovr_txt = self.grade_text(g.overall_grade)
                rating = self.grade_text(g.final_equiv)
                rem = g.remarks or ""
            else:
                mid_txt, fin_txt, ovr_txt, rating, rem = "Incomplete", "Incomplete", "Incomplete", "Incomplete", "Incomplete"

            self.tree_grades.insert("", "end", values=(
                en.enrollment_id, en.student_name, mid_txt, fin_txt, ovr_txt, rating, rem
            ))

    def clear_score_form(self):
        self.entry_raw_score.delete(0, "end")
        self.entry_remarks.delete(0, "end")
