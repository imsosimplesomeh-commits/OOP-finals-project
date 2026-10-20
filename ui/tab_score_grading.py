# tab_score_grading.py - Tab for score entry and grade calculations

from tkinter import ttk, messagebox

from models import GradeComponentScore
from services.grading_service import GradingService
from services.score_service import ScoreService
from services.class_service import ClassService
from services.enrollment_service import EnrollmentService
from services.configuration_service import ConfigurationService
from ui.theme import style_table, add_message_bar, show_message, form_panel


class ScoreGradingTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Page.TFrame")
        self.class_service = ClassService()
        self.enrollment_service = EnrollmentService()
        self.config_service = ConfigurationService()
        self.score_service = ScoreService()
        self.grading_service = GradingService()

        self.class_map = {}
        self.student_map = {}
        self.component_map = {}
        self.comp_max_scores = {}

        self.selected_offering_id = None
        self.selected_enrollment_id = None

        self._build_ui()
        self.load_classes()

    def _build_ui(self):
        self.message_label = add_message_bar(self)
        self._build_filters()

        main_split = ttk.Frame(self, style="Page.TFrame")
        main_split.pack(fill="both", expand=True, padx=8, pady=8)

        self._build_score_section(main_split)
        self._build_grade_table(main_split)

    def _build_filters(self):
        top_bar = form_panel(self, text="Class and Weighting")
        top_bar.pack(fill="x", padx=8, pady=8)
        top_bar.columnconfigure(1, weight=1)

        ttk.Label(top_bar, text="Class Offering:").grid(row=0, column=0, padx=8, pady=8, sticky="e")
        self.cb_class = ttk.Combobox(top_bar, width=32, state="readonly")
        self.cb_class.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        self.cb_class.bind("<<ComboboxSelected>>", self.on_class_change)

        ttk.Label(top_bar, text="Midterm Weight %:").grid(row=0, column=2, padx=(16, 8), sticky="e")
        self.entry_mid_weight = ttk.Entry(top_bar, width=5)
        self.entry_mid_weight.insert(0, "40")
        self.entry_mid_weight.grid(row=0, column=3, padx=8, sticky="w")

        ttk.Label(top_bar, text="Finals Weight %:").grid(row=0, column=4, padx=(8, 8), sticky="e")
        self.entry_fin_weight = ttk.Entry(top_bar, width=5)
        self.entry_fin_weight.insert(0, "60")
        self.entry_fin_weight.grid(row=0, column=5, padx=8, sticky="w")

        ttk.Button(
            top_bar, text="Compute All",
            command=self.bulk_calculate_grades
        ).grid(row=1, column=0, columnspan=2, padx=8, pady=8, sticky="w")
        ttk.Button(
            top_bar, text="Refresh",
            command=self.refresh_all
        ).grid(row=1, column=2, columnspan=4, padx=8, pady=8, sticky="w")

    def _build_score_section(self, main_split):
        left_frame = ttk.LabelFrame(main_split, text="Score Entry", style="Section.TLabelframe")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self._build_score_form(left_frame)
        self._build_score_buttons(left_frame)
        self._build_score_table(left_frame)

    def _build_score_form(self, left_frame):
        f_entry = form_panel(left_frame, text="Score Form")
        f_entry.pack(fill="x", padx=8, pady=8)
        f_entry.columnconfigure(1, weight=1)

        ttk.Label(f_entry, text="Student:").grid(row=0, column=0, padx=8, pady=(0, 8), sticky="w")
        self.cb_student = ttk.Combobox(f_entry, width=18, state="readonly")
        self.cb_student.grid(row=0, column=1, padx=8, pady=(0, 8), sticky="ew")
        self.cb_student.bind("<<ComboboxSelected>>", self.on_student_change)

        ttk.Label(f_entry, text="Component:").grid(row=1, column=0, padx=8, pady=(0, 8), sticky="w")
        self.cb_comp = ttk.Combobox(f_entry, width=18, state="readonly")
        self.cb_comp.grid(row=1, column=1, padx=8, pady=(0, 8), sticky="ew")
        self.cb_comp.bind("<<ComboboxSelected>>", self.on_comp_change)

        ttk.Label(f_entry, text="Max Score:").grid(row=2, column=0, padx=8, pady=(0, 8), sticky="w")
        self.lbl_max_score = ttk.Label(f_entry, text="--")
        self.lbl_max_score.grid(row=2, column=1, padx=8, pady=(0, 8), sticky="ew")

        ttk.Label(f_entry, text="Raw Score:").grid(row=3, column=0, padx=8, pady=(0, 8), sticky="w")
        self.entry_raw_score = ttk.Entry(f_entry, width=15)
        self.entry_raw_score.grid(row=3, column=1, padx=8, pady=(0, 8), sticky="ew")

        ttk.Label(f_entry, text="Remarks:").grid(row=4, column=0, padx=8, pady=(0, 8), sticky="w")
        self.entry_remarks = ttk.Entry(f_entry, width=18)
        self.entry_remarks.grid(row=4, column=1, padx=8, pady=(0, 8), sticky="ew")

    def _build_score_buttons(self, left_frame):
        btn_score_box = ttk.Frame(left_frame)
        btn_score_box.pack(fill="x", padx=8, pady=8)
        btn_score_box.columnconfigure(0, weight=1, uniform="actions")
        btn_score_box.columnconfigure(1, weight=1, uniform="actions")
        ttk.Button(
            btn_score_box, text="Save Score",
            command=self.save_score
        ).grid(row=0, column=0, padx=(0, 8), pady=(0, 8), sticky="ew")
        ttk.Button(
            btn_score_box, text="Compute Student",
            command=self.calculate_selected_student
        ).grid(row=0, column=1, padx=(0, 8), pady=(0, 8), sticky="ew")
        ttk.Button(
            btn_score_box, text="Clear",
            command=self.clear_score_form
        ).grid(row=1, column=0, padx=(0, 8), pady=(0, 8), sticky="ew")
        ttk.Button(
            btn_score_box, text="Delete", style="Delete.TButton",
            command=self.delete_score
        ).grid(row=1, column=1, padx=(0, 8), pady=(0, 8), sticky="ew")

    def _build_score_table(self, left_frame):
        ttk.Label(left_frame, text="Recorded Scores").pack(anchor="w", padx=8, pady=(8, 8))

        cols_s = ("score_id", "component_id", "comp_name", "type", "score", "max", "norm", "remarks")
        self.tree_student_scores = ttk.Treeview(left_frame, columns=cols_s, show="headings", height=8)
        style_table(self.tree_student_scores)
        self.tree_student_scores.column("score_id", width=0, stretch=False)
        self.tree_student_scores.column("component_id", width=0, stretch=False)
        self.tree_student_scores.column("remarks", width=0, stretch=False)
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
        self.tree_student_scores.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree_student_scores.bind("<<TreeviewSelect>>", self.on_score_select)

    def _build_grade_table(self, main_split):
        right_frame = ttk.LabelFrame(main_split, text="Grades", style="Section.TLabelframe")
        right_frame.pack(side="right", fill="both", expand=True, padx=(8, 0))

        cols_g = ("enrollment_id", "student_name", "midterm", "finals", "final_grade", "rating", "remarks")
        self.tree_grades = ttk.Treeview(right_frame, columns=cols_g, show="headings", height=14)
        style_table(self.tree_grades)
        self.tree_grades.heading("enrollment_id", text="Enrollment ID")
        self.tree_grades.heading("student_name", text="Student Name")
        self.tree_grades.heading("midterm", text="Midterm")
        self.tree_grades.heading("finals", text="Finals")
        self.tree_grades.heading("final_grade", text="Overall Final")
        self.tree_grades.heading("rating", text="Rating")
        self.tree_grades.heading("remarks", text="Remarks")

        self.tree_grades.column("enrollment_id", width=0, stretch=False)
        self.tree_grades.column("student_name", width=120)
        self.tree_grades.column("midterm", width=75)
        self.tree_grades.column("finals", width=75)
        self.tree_grades.column("final_grade", width=110)
        self.tree_grades.column("rating", width=85, minwidth=85, stretch=False)
        self.tree_grades.column("remarks", width=85)

        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.tree_grades.yview)
        self.tree_grades.configure(yscrollcommand=scrollbar.set)
        self.tree_grades.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)

        self.tree_grades.bind("<<TreeviewSelect>>", self.on_grade_row_select)

    def refresh_all(self):
        self.load_classes()

    def load_classes(self):
        try:
            classes = self.class_service.find_all()
            self.class_map = {f"{c.class_code} - {c.subject_name or c.subject_code} ({c.section or 'N/A'})": c.class_id for c in classes}
            self.cb_class["values"] = list(self.class_map.keys())
            if self.class_map:
                if self.cb_class.get() not in self.class_map:
                    self.cb_class.current(0)
                self.on_class_change(None)
            else:
                self.cb_class.set("")
                self.selected_offering_id = None
                self.load_class_students()
                self.load_class_components()
                self.load_grades_table()
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not load records. Check the database connection.")

    def on_class_change(self, event):
        try:
            disp = self.cb_class.get()
            if not disp:
                return
            self.selected_offering_id = self.class_map.get(disp)
            self.load_class_students()
            self.load_class_components()
            self.load_grades_table()
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not load records. Check the database connection.")

    def load_class_students(self):
        enrollments = self.enrollment_service.get_class_enrollments(self.selected_offering_id)
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
        comps = self.config_service.get_class_components(self.selected_offering_id)
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
        try:
            disp = self.cb_student.get()
            if not disp:
                return
            self.selected_enrollment_id = self.student_map.get(disp)
            self.load_student_scores()
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not load records. Check the database connection.")

    def on_grade_row_select(self, event):
        try:
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
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not load records. Check the database connection.")

    def load_student_scores(self):
        for r in self.tree_student_scores.get_children():
            self.tree_student_scores.delete(r)
        if not self.selected_enrollment_id:
            return

        for index, (score, normalized) in enumerate(self.score_service.get_scores(self.selected_enrollment_id)):
            self.tree_student_scores.insert("", "end", tags=("even" if index % 2 == 0 else "odd",), values=(
                score.score_id, score.component_id, score.component_name, score.component_type,
                f"{score.score:.2f}", f"{score.max_score:.2f}", f"{normalized:.2f}%", score.remarks or "",
            ))

    def on_score_select(self, event):
        selected = self.tree_student_scores.selection()
        if not selected:
            return
        values = self.tree_student_scores.item(selected[0], "values")
        for display, component_id in self.component_map.items():
            if component_id == values[1]:
                self.cb_comp.set(display)
                self.on_comp_change(None)
                break
        self.entry_raw_score.delete(0, "end")
        self.entry_raw_score.insert(0, values[4])
        self.entry_remarks.delete(0, "end")
        self.entry_remarks.insert(0, values[7])

    def save_score(self):
        try:
            score = GradeComponentScore(
                enrollment_id=self.student_map.get(self.cb_student.get()),
                component_id=self.component_map.get(self.cb_comp.get()),
                score=self.entry_raw_score.get(),
                remarks=self.entry_remarks.get().strip() or None,
            )
            self.score_service.save(score)
            self.load_student_scores()
            self.load_grades_table()
            show_message(self, messagebox.showinfo, "Success", "Score saved.")
        except ValueError as error:
            show_message(self, messagebox.showwarning, "Invalid Score", str(error))
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not save the score. Check the database connection.")

    def delete_score(self):
        selected = self.tree_student_scores.selection()
        if not selected:
            show_message(self, messagebox.showwarning, "No Selection", "Select a score to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this score?"):
            return
        try:
            score_id = self.tree_student_scores.item(selected[0], "values")[0]
            self.score_service.delete(score_id)
            self.load_student_scores()
            self.load_grades_table()
            self.clear_score_form()
            show_message(self, messagebox.showinfo, "Success", "Score deleted.")
        except ValueError as error:
            show_message(self, messagebox.showwarning, "Cannot Delete", str(error))
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not delete the score. Refresh and try again.")

    def _get_weights(self):
        valid, message = self.grading_service.validate_percentages(self.selected_offering_id)
        if not valid:
            show_message(self, messagebox.showwarning, "Weight Configuration Error", message)
            return None
        try:
            return self.grading_service.validate_overall_weights(
                self.entry_mid_weight.get(), self.entry_fin_weight.get(),
            )
        except ValueError as error:
            show_message(self, messagebox.showwarning, "Invalid Weights", str(error))
            return None

    def calculate_selected_student(self):
        if not self.selected_enrollment_id or not self.selected_offering_id:
            show_message(self, messagebox.showwarning, "Validation", "Select a student to calculate grade.")
            return

        try:
            weights = self._get_weights()
            if weights is None:
                return
            mid_w, fin_w = weights
            grade = self.grading_service.generate_and_save_grade(
                self.selected_enrollment_id, self.selected_offering_id, mid_w, fin_w
            )
            finals_rating = self.grading_service.calculator.to_grade_point(grade.finals_grade)
            show_message(self, messagebox.showinfo,
                "Grade Computed",
                f"Midterm: {self.grade_text(grade.midterm_grade)}\n"
                f"Finals: {self.grade_text(grade.finals_grade)} ({self.grade_text(finals_rating)})\n"
                f"Overall Final Grade: {self.grade_text(grade.overall_grade)}\n"
                f"Remarks: {grade.remarks}"
            )
            self.load_grades_table()
        except ValueError as error:
            show_message(self, messagebox.showwarning, "Grade Calculation", str(error))
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not save the grade. Check the database connection.")

    def bulk_calculate_grades(self):
        if not self.selected_offering_id:
            show_message(self, messagebox.showwarning, "Validation", "Select a class offering.")
            return

        try:
            weights = self._get_weights()
            if weights is None:
                return
            mid_w, fin_w = weights
            grades = self.grading_service.bulk_compute_class_grades(
                self.selected_offering_id, mid_w, fin_w
            )
            show_message(self, messagebox.showinfo, "Bulk Calculation", f"Successfully computed grades for {len(grades)} students.")
            self.load_grades_table()
        except ValueError as error:
            show_message(self, messagebox.showwarning, "Grade Calculation", str(error))
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not save grades. Check the database connection.")

    def grade_text(self, value):
        return "Incomplete" if value is None else f"{value:.2f}"

    def load_grades_table(self):
        for r in self.tree_grades.get_children():
            self.tree_grades.delete(r)
        if not self.selected_offering_id:
            return

        enrollments = self.enrollment_service.get_class_enrollments(self.selected_offering_id)
        grades = self.grading_service.get_class_grades(self.selected_offering_id)
        grade_map = {g.enrollment_id: g for g in grades}

        for index, en in enumerate(enrollments):
            g = grade_map.get(en.enrollment_id)
            if g:
                mid_txt = self.grade_text(g.midterm_grade)
                fin_txt = self.grade_text(g.finals_grade)
                ovr_txt = self.grade_text(g.overall_grade)
                rating = self.grade_text(g.final_equiv)
                rem = g.remarks or ""
            else:
                mid_txt, fin_txt, ovr_txt, rating, rem = "Incomplete", "Incomplete", "Incomplete", "Incomplete", "Incomplete"

            self.tree_grades.insert("", "end", tags=("even" if index % 2 == 0 else "odd",), values=(
                en.enrollment_id, en.student_name, mid_txt, fin_txt, ovr_txt, rating, rem
            ))

    def clear_score_form(self):
        self.entry_raw_score.delete(0, "end")
        self.entry_remarks.delete(0, "end")
