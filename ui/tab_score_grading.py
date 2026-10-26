# tab_score_grading.py - Tab for score entry and grade calculations

from tkinter import ttk, messagebox, font as tkfont

from models import GradeComponentScore
from services.grading_service import GradingService
from services.score_service import ScoreService
from services.class_service import ClassService
from services.enrollment_service import EnrollmentService
from services.configuration_service import ConfigurationService
from services.grade_calculator import GradeCalculator, COMPLETE, MIDTERM_ONLY, INCOMPLETE, NOT_SET
from services.grading_service import MIDTERM_ORDER, FINALS_ORDER
from ui.theme import style_table, add_message_bar, show_message, form_panel

# Raw Scores grid: names wider than this (pixels) wrap so all columns fit at the default window size
MAX_HEADING_WIDTH = 150
RAW_COLUMN_PADDING = 16


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
        self.student_number_map = {}
        self.component_map = {}
        self.comp_max_scores = {}
        self.comp_weights = {}

        self.selected_offering_id = None
        self.selected_enrollment_id = None

        self._build_ui()
        self.load_classes()

    def _build_ui(self):
        self.message_label = add_message_bar(self)
        self._build_filters()

        # score entry and the read-only raw scores grid share the space below the filters
        views = ttk.Notebook(self)
        views.pack(fill="both", expand=True, padx=8, pady=8)
        main_split = ttk.Frame(views, style="Page.TFrame")
        views.add(main_split, text="Score Entry")

        self._build_score_section(main_split)
        self._build_grade_table(main_split)
        self._build_raw_scores(views)

    def _build_raw_scores(self, views):
        # like the Raw scores table in the checklist: one row per student, one column per component
        frame = ttk.Frame(views, style="Page.TFrame")
        views.add(frame, text="Raw Scores")
        ttk.Style(self).configure("RawScores.Treeview.Heading", justify="center")
        self.tree_raw = ttk.Treeview(frame, show="headings", height=12, style="RawScores.Treeview")
        style_table(self.tree_raw)
        scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=self.tree_raw.xview)
        self.tree_raw.configure(xscrollcommand=scroll_x.set)
        self.tree_raw.pack(fill="both", expand=True, padx=8, pady=(8, 0))
        scroll_x.pack(fill="x", padx=8, pady=(0, 8))

    def _build_filters(self):
        top_bar = form_panel(self, text="Class and Grade Formula")
        top_bar.pack(fill="x", padx=8, pady=8)
        top_bar.columnconfigure(1, weight=1)

        ttk.Label(top_bar, text="Class Offering:").grid(row=0, column=0, padx=8, pady=8, sticky="e")
        self.cb_class = ttk.Combobox(top_bar, width=32, state="readonly")
        self.cb_class.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        self.cb_class.bind("<<ComboboxSelected>>", self.on_class_change)

        # the formula comes from GradeCalculator so the screen never disagrees with the math
        ttk.Label(top_bar, text=GradeCalculator.formula_text()).grid(row=0, column=2, padx=(16, 8), sticky="e")

        ttk.Button(
            top_bar, text="Compute All",
            command=self.bulk_calculate_grades
        ).grid(row=1, column=0, columnspan=2, padx=8, pady=8, sticky="w")
        ttk.Button(
            top_bar, text="Refresh",
            command=self.refresh_all
        ).grid(row=1, column=2, padx=8, pady=8, sticky="w")

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
        # not readonly, so a student number can be typed (SC-04 shows why it is refused)
        self.cb_student = ttk.Combobox(f_entry, width=18)
        self.cb_student.grid(row=0, column=1, padx=8, pady=(0, 8), sticky="ew")
        self.cb_student.bind("<<ComboboxSelected>>", self.on_student_change)

        ttk.Label(f_entry, text="Component:").grid(row=1, column=0, padx=8, pady=(0, 8), sticky="w")
        self.cb_comp = ttk.Combobox(f_entry, width=18, state="readonly")
        self.cb_comp.grid(row=1, column=1, padx=8, pady=(0, 8), sticky="ew")
        self.cb_comp.bind("<<ComboboxSelected>>", self.on_comp_change)

        ttk.Label(f_entry, text="Max / Weight:").grid(row=2, column=0, padx=8, pady=(0, 8), sticky="w")
        self.lbl_max_score = ttk.Label(f_entry, text="--")
        self.lbl_max_score.grid(row=2, column=1, padx=8, pady=(0, 8), sticky="ew")

        ttk.Label(f_entry, text="Raw Score:").grid(row=3, column=0, padx=8, pady=(0, 8), sticky="w")
        self.entry_raw_score = ttk.Entry(f_entry, width=15)
        self.entry_raw_score.grid(row=3, column=1, padx=8, pady=(0, 8), sticky="ew")

        # a note about this one score; the grade remarks (Passed/Failed) are automatic
        ttk.Label(f_entry, text="Score Note:").grid(row=4, column=0, padx=8, pady=(0, 8), sticky="w")
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

        cols_s = ("score_id", "component_id", "comp_name", "type", "score", "max", "weight", "norm", "remarks")
        self.tree_student_scores = ttk.Treeview(left_frame, columns=cols_s, show="headings", height=8)
        style_table(self.tree_student_scores)
        self.tree_student_scores.column("score_id", width=0, stretch=False)
        self.tree_student_scores.column("component_id", width=0, stretch=False)
        self.tree_student_scores.column("remarks", width=0, stretch=False)
        self.tree_student_scores.heading("comp_name", text="Component")
        self.tree_student_scores.heading("type", text="Category")
        self.tree_student_scores.heading("score", text="Score")
        self.tree_student_scores.heading("max", text="Max")
        self.tree_student_scores.heading("weight", text="Weight")
        self.tree_student_scores.heading("norm", text="Normalized")

        self.tree_student_scores.column("comp_name", width=120)
        self.tree_student_scores.column("type", width=80)
        self.tree_student_scores.column("score", width=55)
        self.tree_student_scores.column("max", width=55)
        self.tree_student_scores.column("weight", width=60)
        self.tree_student_scores.column("norm", width=75)
        self.tree_student_scores.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree_student_scores.bind("<<TreeviewSelect>>", self.on_score_select)

    def _build_grade_table(self, main_split):
        right_frame = ttk.LabelFrame(main_split, text="Grades", style="Section.TLabelframe")
        right_frame.pack(side="right", fill="both", expand=True, padx=(8, 0))

        cols_g = ("enrollment_id", "student_name", "midterm", "mid_gp", "finals", "fin_gp", "final_grade", "rating", "remarks", "status")
        self.tree_grades = ttk.Treeview(right_frame, columns=cols_g, show="headings", height=14)
        style_table(self.tree_grades)
        self.tree_grades.heading("enrollment_id", text="Enrollment ID")
        self.tree_grades.heading("student_name", text="Student Name")
        self.tree_grades.heading("midterm", text="Midterm %")
        self.tree_grades.heading("mid_gp", text="Midterm GP")
        self.tree_grades.heading("finals", text="Finals %")
        self.tree_grades.heading("fin_gp", text="Finals GP")
        self.tree_grades.heading("final_grade", text="Overall %")
        self.tree_grades.heading("rating", text="Overall GP")
        self.tree_grades.heading("remarks", text="Remarks")
        self.tree_grades.heading("status", text="Status")

        self.tree_grades.column("enrollment_id", width=0, stretch=False)
        self.tree_grades.column("student_name", width=120)
        for column in ("midterm", "mid_gp", "finals", "fin_gp", "final_grade", "rating"):
            self.tree_grades.column(column, width=80)
        self.tree_grades.column("remarks", width=80)
        self.tree_grades.column("status", width=95)

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
                self.load_raw_scores()
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
            self.load_raw_scores()
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not load records. Check the database connection.")

    def load_class_students(self):
        enrollments = self.enrollment_service.get_class_enrollments(self.selected_offering_id)
        self.student_map = {f"{e.student_name}": e.enrollment_id for e in enrollments}
        self.student_number_map = {e.student_id: e.enrollment_id for e in enrollments}
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
        self.comp_weights = {}
        for c in comps:
            d = f"[{c.period_name or 'Period'}] {c.name} (/{c.max_score:g} - {self.weight_text(c.percentage_value)})"
            self.component_map[d] = c.component_id
            self.comp_max_scores[c.component_id] = c.max_score
            self.comp_weights[c.component_id] = c.percentage_value
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
            self.lbl_max_score.config(text=f"{max_s:g} / {self.weight_text(self.comp_weights.get(cid))}")

    @staticmethod
    def weight_text(weight):
        return "-" if weight is None else f"{weight:g}%"

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
                f"{score.score:.2f}", f"{score.max_score:.2f}",
                self.weight_text(self.comp_weights.get(score.component_id)), f"{normalized:.2f}%", score.remarks or "",
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
        self.entry_remarks.insert(0, values[8])

    def save_score(self):
        value = self.cb_student.get().strip()
        enrollment_id = self.student_map.get(value) or self.student_number_map.get(value)
        if not enrollment_id:
            if not value:
                message = "Select a student first."
            else:
                message = (f"'{value}' is not enrolled in this class, so no score can be saved. "
                           "Only enrolled students appear in the Student list.")
            show_message(self, messagebox.showwarning, "Not Enrolled", message)
            return
        self.selected_enrollment_id = enrollment_id
        try:
            score = GradeComponentScore(
                enrollment_id=enrollment_id,
                component_id=self.component_map.get(self.cb_comp.get()),
                score=self.entry_raw_score.get(),
                remarks=self.entry_remarks.get().strip() or None,
            )
            self.score_service.save(score)
            self.load_student_scores()
            self.load_grades_table()
            self.load_raw_scores()
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
            self.load_raw_scores()
            self.clear_score_form()
            show_message(self, messagebox.showinfo, "Success", "Score deleted.")
        except ValueError as error:
            show_message(self, messagebox.showwarning, "Cannot Delete", str(error))
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not delete the score. Refresh and try again.")

    def calculate_selected_student(self):
        if not self.selected_enrollment_id or not self.selected_offering_id:
            show_message(self, messagebox.showwarning, "Validation", "Select a student to compute the grade.")
            return
        try:
            grade = self.grading_service.generate_and_save_grade(self.selected_enrollment_id, self.selected_offering_id)
            finals_point = GradeCalculator.to_grade_point(grade.finals_grade)
            show_message(self, messagebox.showinfo,
                "Grade Computed",
                f"Midterm: {self.grade_text(grade.midterm_grade)} ({self.grade_text(grade.midterm_equiv)})\n"
                f"Finals: {self.period_text(grade.finals_grade, FINALS_ORDER)} ({self.grade_text(finals_point)})\n"
                f"Overall: {self.grade_text(grade.overall_grade)} ({self.grade_text(grade.final_equiv)})\n"
                f"Remarks: {grade.remarks}\n"
                f"Status: {GradeCalculator.status_of(grade)}"
            )
            self.load_grades_table()
        except ValueError as error:
            show_message(self, messagebox.showwarning, "Grade Calculation", str(error))
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not save the grade. Check the database connection.")

    def bulk_calculate_grades(self):
        if not self.selected_offering_id:
            show_message(self, messagebox.showwarning, "Validation", "Select a class to compute.")
            return
        try:
            grades = self.grading_service.bulk_compute_class_grades(self.selected_offering_id)
            statuses = [GradeCalculator.status_of(g) for g in grades]
            counts = ", ".join(f"{name}: {statuses.count(name)}" for name in (COMPLETE, MIDTERM_ONLY, INCOMPLETE))
            show_message(self, messagebox.showinfo, "Bulk Calculation",
                         f"Successfully computed grades for {len(grades)} student{'' if len(grades) == 1 else 's'}.\n{counts}")
            self.load_grades_table()
        except ValueError as error:
            show_message(self, messagebox.showwarning, "Grade Calculation", str(error))
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not save grades. Check the database connection.")

    def load_raw_scores(self):
        # read-only view of saved scores; a missing score shows "-", never 0
        self.tree_raw.delete(*self.tree_raw.get_children())
        components = self.config_service.get_class_components(self.selected_offering_id) if self.selected_offering_id else []
        enrollments = self.enrollment_service.get_class_enrollments(self.selected_offering_id) if self.selected_offering_id else []
        rows = []
        for en in enrollments:
            saved = {score.component_id: score.score for score, _ in self.score_service.get_scores(en.enrollment_id)}
            rows.append([en.student_name] + [f"{saved[c.component_id]:g}" if c.component_id in saved else "-"
                                             for c in components])
        style = ttk.Style(self)
        heading_font = tkfont.Font(font=style.lookup("Treeview.Heading", "font"))
        headings = [["Student"]] + [
            self._wrap_name(c.name, heading_font) + [f"(/{c.max_score:g} - {self.weight_text(c.percentage_value)})"]
            for c in components
        ]
        self.tree_raw["columns"] = ["student"] + [c.component_id for c in components]
        # Tk sizes the header row from column #0, so its blank lines make room for the tallest heading
        self.tree_raw.heading("#0", text="\n" * (max(len(lines) for lines in headings) - 1))
        body_font = tkfont.Font(font=style.lookup("Treeview", "font"))
        for index, (column, lines) in enumerate(zip(self.tree_raw["columns"], headings)):
            # as wide as the widest heading line or cell, so no heading is cut off
            widest = max([heading_font.measure(line) for line in lines] + [body_font.measure(row[index]) for row in rows])
            self.tree_raw.heading(column, text="\n".join(lines))
            self.tree_raw.column(column, width=widest + RAW_COLUMN_PADDING, minwidth=widest + RAW_COLUMN_PADDING,
                                 stretch=False, anchor="w" if index == 0 else "center")
        for index, row in enumerate(rows):
            self.tree_raw.insert("", "end", tags=("even" if index % 2 == 0 else "odd",), values=row)

    @staticmethod
    def _wrap_name(name, font):
        # a long name is split at the space that gives the shortest lines, so the grid fits the default window
        if font.measure(name) <= MAX_HEADING_WIDTH or " " not in name:
            return [name]
        words = name.split(" ")
        splits = [[" ".join(words[:i]), " ".join(words[i:])] for i in range(1, len(words))]
        return min(splits, key=lambda lines: max(font.measure(line) for line in lines))

    def grade_text(self, value):
        return INCOMPLETE if value is None else f"{value:.2f}"

    def period_text(self, value, period_order):
        # a period with no components at all is "N/A"; one with a missing score or weight is "Incomplete"
        if value is None and not self.grading_service.period_has_components(period_order):
            return NOT_SET
        return self.grade_text(value)

    def load_grades_table(self):
        # rows come from the saved GRADE table, so the screen always matches the database
        for r in self.tree_grades.get_children():
            self.tree_grades.delete(r)
        if not self.selected_offering_id:
            return
        enrollments = self.enrollment_service.get_class_enrollments(self.selected_offering_id)
        grade_map = {g.enrollment_id: g for g in self.grading_service.get_class_grades(self.selected_offering_id)}
        for index, en in enumerate(enrollments):
            self.tree_grades.insert("", "end", tags=("even" if index % 2 == 0 else "odd",),
                                    values=(en.enrollment_id, en.student_name, *self.grade_row(grade_map.get(en.enrollment_id))))

    def grade_row(self, g):
        if g is None:
            return [INCOMPLETE] * 8
        # the finals grade point is not stored in GRADE, so convert it with the shared scale
        finals_point = GradeCalculator.to_grade_point(g.finals_grade)
        return [
            self.period_text(g.midterm_grade, MIDTERM_ORDER), self.grade_text(g.midterm_equiv),
            self.period_text(g.finals_grade, FINALS_ORDER), self.grade_text(finals_point),
            self.grade_text(g.overall_grade), self.grade_text(g.final_equiv),
            g.remarks or INCOMPLETE, GradeCalculator.status_of(g),
        ]

    def clear_score_form(self):
        self.entry_raw_score.delete(0, "end")
        self.entry_remarks.delete(0, "end")
