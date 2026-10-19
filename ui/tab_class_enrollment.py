# tab_class_enrollment.py - Tab for Class Offerings, Grading Weights, and Enrollment

import tkinter as tk
from tkinter import ttk, messagebox

from models import ClassOffering, GradeComponent
from services.class_service import ClassService
from services.student_service import StudentService
from services.teacher_service import TeacherService
from services.subject_service import SubjectService
from services.configuration_service import ConfigurationService
from services.enrollment_service import EnrollmentService
from ui.theme import PANEL, style_table


class ClassEnrollmentTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.class_service = ClassService()
        self.student_service = StudentService()
        self.teacher_service = TeacherService()
        self.subject_service = SubjectService()
        self.config_service = ConfigurationService()
        self.enrollment_service = EnrollmentService()
        self.weight_entries = {}

        self.selected_offering_id = None
        self.subject_map = {}
        self.teacher_map = {}
        self.student_map = {}

        self._build_ui()
        self.refresh_all()

    def _build_ui(self):
        # keep the lower forms reachable on smaller screens
        self.canvas = tk.Canvas(self, background=PANEL, highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.content = ttk.Frame(self.canvas)
        self.content_window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_content)

        # 1. Class offerings form and table
        top_frame = ttk.LabelFrame(self.content, text="1. Class Offerings")
        top_frame.pack(fill="x", padx=10, pady=5)

        form = ttk.Frame(top_frame)
        form.pack(fill="x", padx=5, pady=5)

        ttk.Label(form, text="Class Code:").grid(row=0, column=0, padx=4, pady=3, sticky="e")
        self.entry_code = ttk.Entry(form, width=18)
        self.entry_code.grid(row=0, column=1, padx=4, pady=3, sticky="w")

        ttk.Label(form, text="Subject:").grid(row=0, column=2, padx=4, pady=3, sticky="e")
        self.cb_subject = ttk.Combobox(form, width=28, state="readonly")
        self.cb_subject.grid(row=0, column=3, padx=4, pady=3, sticky="w")

        ttk.Label(form, text="Teacher:").grid(row=0, column=4, padx=4, pady=3, sticky="e")
        self.cb_teacher = ttk.Combobox(form, width=24, state="readonly")
        self.cb_teacher.grid(row=0, column=5, padx=4, pady=3, sticky="w")

        ttk.Label(form, text="Section:").grid(row=1, column=0, padx=4, pady=3, sticky="e")
        self.entry_section = ttk.Entry(form, width=18)
        self.entry_section.grid(row=1, column=1, padx=4, pady=3, sticky="w")

        ttk.Label(form, text="Schedule:").grid(row=1, column=2, padx=4, pady=3, sticky="e")
        self.entry_schedule = ttk.Entry(form, width=28)
        self.entry_schedule.grid(row=1, column=3, padx=4, pady=3, sticky="w")

        ttk.Label(form, text="Room:").grid(row=1, column=4, padx=4, pady=3, sticky="e")
        self.entry_room = ttk.Entry(form, width=24)
        self.entry_room.grid(row=1, column=5, padx=4, pady=3, sticky="w")

        ttk.Label(form, text="School Year:").grid(row=2, column=0, padx=4, pady=3, sticky="e")
        self.entry_sy = ttk.Entry(form, width=18)
        self.entry_sy.insert(0, "2026-2027")
        self.entry_sy.grid(row=2, column=1, padx=4, pady=3, sticky="w")

        ttk.Label(form, text="Semester:").grid(row=2, column=2, padx=4, pady=3, sticky="e")
        self.cb_semester = ttk.Combobox(form, values=["1st Semester", "2nd Semester", "Summer"], width=26, state="readonly")
        self.cb_semester.set("1st Semester")
        self.cb_semester.grid(row=2, column=3, padx=4, pady=3, sticky="w")

        btn_bar = ttk.Frame(top_frame)
        btn_bar.pack(fill="x", padx=5, pady=4)
        ttk.Button(btn_bar, text="Add Class", command=self.add_class).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="Update Class", command=self.update_class).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="Delete Class", command=self.delete_class).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="Clear", command=self.clear_class_form).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="Refresh All", command=self.refresh_all).pack(side="left", padx=4)

        # classes table
        cols = ("id", "code", "subject", "teacher", "section", "schedule", "room", "term")
        self.tree_classes = ttk.Treeview(top_frame, columns=cols, show="headings", height=5)
        style_table(self.tree_classes)
        self.tree_classes.heading("id", text="ID")
        self.tree_classes.heading("code", text="Class Code")
        self.tree_classes.heading("subject", text="Subject")
        self.tree_classes.heading("teacher", text="Teacher")
        self.tree_classes.heading("section", text="Section")
        self.tree_classes.heading("schedule", text="Schedule")
        self.tree_classes.heading("room", text="Room")
        self.tree_classes.heading("term", text="Term / SY")

        self.tree_classes.column("id", width=0, stretch=False)
        self.tree_classes.column("code", width=100)
        self.tree_classes.column("subject", width=160)
        self.tree_classes.column("teacher", width=140)
        self.tree_classes.column("section", width=90)
        self.tree_classes.column("schedule", width=130)
        self.tree_classes.column("room", width=90)
        self.tree_classes.column("term", width=130)
        self.tree_classes.pack(fill="x", padx=5, pady=5)
        self.tree_classes.bind("<<TreeviewSelect>>", self.on_class_select)

        # bottom split: weights & components on left, student enrollments on right
        bottom_frame = ttk.Frame(self.content)
        bottom_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 2. Grading Weights & Components
        left_frame = ttk.LabelFrame(bottom_frame, text="2. Grading Weights & Components (for selected class)")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        w_ctrl = ttk.Frame(left_frame)
        w_ctrl.pack(fill="x", padx=5, pady=3)
        ttk.Label(w_ctrl, text="Period:").pack(side="left", padx=2)
        self.cb_weight_period = ttk.Combobox(w_ctrl, width=12, state="readonly")
        self.cb_weight_period.pack(side="left", padx=2)
        self.cb_weight_period.bind("<<ComboboxSelected>>", self.load_weights_and_components)
        ttk.Button(w_ctrl, text="Save Period Weights", command=self.save_weight).pack(side="left", padx=3)
        self.weight_form = ttk.Frame(left_frame)
        self.weight_form.pack(fill="x", padx=5, pady=3)
        self.lbl_weight_total = ttk.Label(left_frame, text="No saved weights")
        self.lbl_weight_total.pack(anchor="w", padx=8, pady=2)

        period_box = ttk.LabelFrame(left_frame, text="Add Grading Period")
        period_box.pack(fill="x", padx=5, pady=3)
        ttk.Label(period_box, text="Name:").pack(side="left", padx=2)
        self.entry_period_name = ttk.Entry(period_box, width=12)
        self.entry_period_name.pack(side="left", padx=2)
        ttk.Label(period_box, text="Order:").pack(side="left", padx=2)
        self.entry_period_order = ttk.Entry(period_box, width=4)
        self.entry_period_order.pack(side="left", padx=2)
        ttk.Button(period_box, text="Add Period", command=self.add_period).pack(side="left", padx=3)

        # add component box
        comp_box = ttk.LabelFrame(left_frame, text="Add Assessable Component")
        comp_box.pack(fill="x", padx=5, pady=5)
        c_row1 = ttk.Frame(comp_box)
        c_row1.pack(fill="x", padx=4, pady=2)
        ttk.Label(c_row1, text="Period:").pack(side="left", padx=2)
        self.cb_period = ttk.Combobox(c_row1, width=10, state="readonly")
        self.cb_period.pack(side="left", padx=2)
        ttk.Label(c_row1, text="Category:").pack(side="left", padx=2)
        self.cb_comp_weight = ttk.Combobox(c_row1, values=["Quiz", "Laboratory", "Exam", "Project", "Assignment"], width=12, state="readonly")
        self.cb_comp_weight.set("Quiz")
        self.cb_comp_weight.pack(side="left", padx=2)

        c_row2 = ttk.Frame(comp_box)
        c_row2.pack(fill="x", padx=4, pady=2)
        ttk.Label(c_row2, text="Name:").pack(side="left", padx=2)
        self.entry_comp_name = ttk.Entry(c_row2, width=14)
        self.entry_comp_name.pack(side="left", padx=2)
        ttk.Label(c_row2, text="Max Score:").pack(side="left", padx=2)
        self.entry_comp_max = ttk.Entry(c_row2, width=6)
        self.entry_comp_max.insert(0, "100")
        self.entry_comp_max.pack(side="left", padx=2)
        ttk.Button(c_row2, text="Add Component", command=self.add_component).pack(side="left", padx=4)
        ttk.Button(c_row2, text="Delete Selected", command=self.delete_component).pack(side="left", padx=4)

        comp_table = ttk.Frame(left_frame)
        comp_table.pack(fill="both", expand=True, padx=5, pady=3)
        cols_c = ("id", "period", "name", "type", "max_score")
        self.tree_comps = ttk.Treeview(comp_table, columns=cols_c, show="headings", height=4)
        style_table(self.tree_comps)
        self.tree_comps.heading("id", text="ID")
        self.tree_comps.heading("period", text="Period")
        self.tree_comps.heading("name", text="Component Name")
        self.tree_comps.heading("type", text="Category")
        self.tree_comps.heading("max_score", text="Max Score")
        self.tree_comps.column("id", width=0, stretch=False)
        self.tree_comps.column("period", width=70)
        self.tree_comps.column("name", width=210)
        self.tree_comps.column("type", width=80)
        self.tree_comps.column("max_score", width=70)
        comp_scroll = ttk.Scrollbar(comp_table, orient="vertical", command=self.tree_comps.yview)
        self.tree_comps.configure(yscrollcommand=comp_scroll.set)
        comp_scroll.pack(side="right", fill="y")
        self.tree_comps.pack(side="left", fill="both", expand=True)

        # 3. Class Enrollment
        right_frame = ttk.LabelFrame(bottom_frame, text="3. Student Enrollment (for selected class)")
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        en_ctrl = ttk.Frame(right_frame)
        en_ctrl.pack(fill="x", padx=5, pady=4)
        ttk.Label(en_ctrl, text="Select Student:").pack(side="left", padx=3)
        self.cb_enroll_student = ttk.Combobox(en_ctrl, width=22)
        self.cb_enroll_student.pack(side="left", padx=3)
        en_buttons = ttk.Frame(right_frame)
        en_buttons.pack(fill="x", padx=5, pady=4)
        ttk.Button(en_buttons, text="Enroll Student", command=self.enroll_student).grid(row=0, column=0, padx=3, pady=3)
        ttk.Button(en_buttons, text="Drop Selected", command=self.drop_student).grid(row=0, column=1, padx=3, pady=3)
        ttk.Button(en_buttons, text="Restore", command=self.restore_student).grid(row=1, column=0, padx=3, pady=3, sticky="ew")
        ttk.Button(en_buttons, text="Remove", command=self.remove_enrollment).grid(row=1, column=1, padx=3, pady=3, sticky="ew")

        cols_e = ("id", "student_id", "student_name", "program", "enroll_date", "status")
        self.tree_enrollments = ttk.Treeview(right_frame, columns=cols_e, show="headings", height=10)
        style_table(self.tree_enrollments)
        self.tree_enrollments.heading("id", text="ID")
        self.tree_enrollments.heading("student_id", text="Student ID")
        self.tree_enrollments.heading("student_name", text="Student Name")
        self.tree_enrollments.heading("program", text="Program")
        self.tree_enrollments.heading("enroll_date", text="Enroll Date")
        self.tree_enrollments.heading("status", text="Status")

        self.tree_enrollments.column("id", width=0, stretch=False)
        self.tree_enrollments.column("student_id", width=100)
        self.tree_enrollments.column("student_name", width=160)
        self.tree_enrollments.column("program", width=90)
        self.tree_enrollments.column("enroll_date", width=90)
        self.tree_enrollments.column("status", width=80)
        self.tree_enrollments.pack(fill="both", expand=True, padx=5, pady=4)

    def _update_scroll_region(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_content(self, event):
        self.canvas.itemconfigure(self.content_window, width=event.width)

    def refresh_all(self):
        try:
            self.load_dropdowns()
            self.load_classes()
            self.load_weights_and_components()
        except Exception:
            messagebox.showerror("Database Error", "Could not load records. Check the database connection.")

    def load_dropdowns(self):
        # subjects dropdown
        subjects = self.subject_service.find_all()
        self.subject_map = {f"{s.subject_code} - {s.subject_name}": s.subject_id for s in subjects}
        self.cb_subject["values"] = list(self.subject_map.keys())

        # teachers dropdown
        teachers = self.teacher_service.find_all()
        self.teacher_map = {f"{t.full_name} ({t.department or 'Faculty'})": t.teacher_id for t in teachers}
        self.cb_teacher["values"] = list(self.teacher_map.keys())

        # students dropdown
        students = self.student_service.find_all()
        self.student_map = {f"{s.student_id} - {s.full_name}": s.student_id for s in students}
        self.cb_enroll_student["values"] = list(self.student_map.keys())

        # grading periods
        periods = self.config_service.get_periods()
        self.period_map = {p.name: p.period_id for p in periods}
        self.cb_period["values"] = list(self.period_map.keys())
        self.cb_weight_period["values"] = list(self.period_map.keys())
        if self.period_map:
            self.cb_period.current(0)
            if not self.cb_weight_period.get():
                self.cb_weight_period.current(0)

    def load_classes(self):
        for r in self.tree_classes.get_children():
            self.tree_classes.delete(r)
        classes = self.class_service.find_all()
        for index, c in enumerate(classes):
            self.tree_classes.insert("", "end", tags=("even" if index % 2 == 0 else "odd",), values=(
                c.class_id, c.class_code, c.subject_name or c.subject_code,
                c.teacher_name, c.section or "", c.schedule or "", c.room or "",
                f"{c.semester} {c.school_year}"
            ))

    def on_class_select(self, event):
        try:
            sel = self.tree_classes.selection()
            if not sel:
                return
            vals = self.tree_classes.item(sel[0], "values")
            self.selected_offering_id = vals[0]
            offering = self.class_service.find_by_id(self.selected_offering_id)
            if offering:
                self.entry_code.delete(0, "end")
                self.entry_code.insert(0, offering.class_code)
                self.entry_section.delete(0, "end")
                self.entry_section.insert(0, offering.section or "")
                self.entry_schedule.delete(0, "end")
                self.entry_schedule.insert(0, offering.schedule or "")
                self.entry_room.delete(0, "end")
                self.entry_room.insert(0, offering.room or "")
                self.entry_sy.delete(0, "end")
                self.entry_sy.insert(0, offering.school_year)
                self.cb_semester.set(offering.semester)

                for disp, sid in self.subject_map.items():
                    if sid == offering.subject_id:
                        self.cb_subject.set(disp)
                        break

                for disp, tid in self.teacher_map.items():
                    if tid == offering.teacher_id:
                        self.cb_teacher.set(disp)
                        break

            self.load_weights_and_components()
            self.load_enrollments()
        except Exception:
            messagebox.showerror("Database Error", "Could not load records. Check the database connection.")

    def clear_class_form(self):
        self.entry_code.delete(0, "end")
        self.entry_section.delete(0, "end")
        self.entry_schedule.delete(0, "end")
        self.entry_room.delete(0, "end")
        self.cb_subject.set("")
        self.cb_teacher.set("")
        self.selected_offering_id = None
        if self.tree_classes.selection():
            self.tree_classes.selection_remove(self.tree_classes.selection())

    def add_class(self):
        self.save_class_form(False)

    def update_class(self):
        self.save_class_form(True)

    def save_class_form(self, updating):
        if updating and not self.selected_offering_id:
            messagebox.showwarning("No Selection", "Select a class to update.")
            return
        try:
            offering = ClassOffering(
                class_id=self.selected_offering_id if updating else None,
                class_code=self.entry_code.get(),
                subject_id=self.subject_map.get(self.cb_subject.get()),
                teacher_id=self.teacher_map.get(self.cb_teacher.get()),
                section=self.entry_section.get(), schedule=self.entry_schedule.get(),
                room=self.entry_room.get(), school_year=self.entry_sy.get(),
                semester=self.cb_semester.get(),
            )
            self.class_service.save(offering)
            messagebox.showinfo("Success", "Class saved.")
            self.load_classes()
        except ValueError as error:
            messagebox.showwarning("Validation", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not save the class. Check the database connection.")

    def delete_class(self):
        if not self.selected_offering_id:
            messagebox.showwarning("No Selection", "Select a class to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this class?"):
            return
        try:
            self.class_service.delete(self.selected_offering_id)
            messagebox.showinfo("Success", "Class deleted.")
            self.clear_class_form()
            self.load_classes()
            self.load_weights_and_components()
            self.load_enrollments()
        except ValueError as error:
            messagebox.showwarning("Cannot Delete", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not delete the class. Refresh and try again.")

    def load_weights_and_components(self, event=None):
        try:
            for widget in self.weight_form.winfo_children():
                widget.destroy()
            self.weight_entries = {}
            for row in self.tree_comps.get_children():
                self.tree_comps.delete(row)
            components = self.config_service.get_components()
            for index, component in enumerate(components):
                self.tree_comps.insert("", "end", tags=("even" if index % 2 == 0 else "odd",), values=(
                    component.component_id, component.period_name, component.name,
                    component.type, component.max_score,
                ))
            period_id = self.period_map.get(self.cb_weight_period.get())
            if not self.selected_offering_id:
                self.lbl_weight_total.config(text="Select a class to set its weights.")
                return
            saved = {w.component_id: w.percentage for w in self.config_service.get_weights(self.selected_offering_id)}
            for component in components:
                if component.period_id != period_id:
                    continue
                row = len(self.weight_entries)
                ttk.Label(self.weight_form, text=component.name).grid(row=row, column=0, sticky="w", padx=3)
                entry = ttk.Entry(self.weight_form, width=8)
                entry.grid(row=row, column=1, padx=3, pady=2)
                if component.component_id in saved:
                    entry.insert(0, f"{saved[component.component_id]:.2f}")
                self.weight_entries[component.component_id] = entry
            self.lbl_weight_total.config(text=self.config_service.weight_summary(self.selected_offering_id))
        except Exception:
            messagebox.showerror("Database Error", "Could not load records. Check the database connection.")

    def save_weight(self):
        try:
            values = [(component_id, entry.get()) for component_id, entry in self.weight_entries.items()]
            message = self.config_service.save_weights(
                self.selected_offering_id, self.period_map.get(self.cb_weight_period.get()), values,
            )
            messagebox.showinfo("Success", message)
            self.load_weights_and_components()
        except ValueError as error:
            messagebox.showwarning("Invalid Weights", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not save weights. Check the database connection.")

    def add_period(self):
        try:
            period = self.config_service.add_period(
                self.entry_period_name.get(), self.entry_period_order.get(),
                self.entry_sy.get(), self.cb_semester.get(),
            )
            self.load_dropdowns()
            self.cb_period.set(period.name)
            self.cb_weight_period.set(period.name)
            self.load_weights_and_components()
            messagebox.showinfo("Success", "Grading period added.")
        except ValueError as error:
            messagebox.showwarning("Validation", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not save the period. Check the database connection.")

    def add_component(self):
        try:
            component = GradeComponent(
                period_id=self.period_map.get(self.cb_period.get()),
                name=self.entry_comp_name.get(), type=self.cb_comp_weight.get(),
                max_score=self.entry_comp_max.get(),
            )
            self.config_service.add_component(component)
            self.entry_comp_name.delete(0, "end")
            self.load_weights_and_components()
            messagebox.showinfo("Success", "Component added.")
        except ValueError as error:
            messagebox.showwarning("Validation", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not save the component. Check the database connection.")

    def delete_component(self):
        selected = self.tree_comps.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a component to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this component?"):
            return
        try:
            self.config_service.delete_component(self.tree_comps.item(selected[0], "values")[0])
            self.load_weights_and_components()
        except ValueError as error:
            messagebox.showwarning("Cannot Delete", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not delete the component. Refresh and try again.")

    def load_enrollments(self):
        try:
            for r in self.tree_enrollments.get_children():
                self.tree_enrollments.delete(r)
            if not self.selected_offering_id:
                return
            enrollments = self.enrollment_service.get_class_enrollments(self.selected_offering_id)
            for index, e in enumerate(enrollments):
                self.tree_enrollments.insert("", "end", tags=("even" if index % 2 == 0 else "odd",), values=(
                    e.enrollment_id, e.student_id, e.student_name,
                    e.student_program or "", str(e.enroll_date or ""), e.status
                ))
        except Exception:
            messagebox.showerror("Database Error", "Could not load records. Check the database connection.")

    def enroll_student(self):
        try:
            value = self.cb_enroll_student.get().strip()
            student_id = self.student_map.get(value, value)
            success, message, _ = self.enrollment_service.enroll_student(student_id, self.selected_offering_id)
            if success:
                messagebox.showinfo("Success", message)
                self.load_enrollments()
            else:
                messagebox.showwarning("Enrollment Issue", message)
        except ValueError as error:
            messagebox.showwarning("Validation", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not save the enrollment. Check the database connection.")

    def drop_student(self):
        self.change_status("Dropped")

    def restore_student(self):
        self.change_status("Enrolled")

    def change_status(self, status):
        selected = self.tree_enrollments.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select an enrolled student.")
            return
        try:
            enrollment_id = self.tree_enrollments.item(selected[0], "values")[0]
            self.enrollment_service.update_status(enrollment_id, status)
            self.load_enrollments()
        except ValueError as error:
            messagebox.showwarning("Validation", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not update the enrollment. Check the database connection.")

    def remove_enrollment(self):
        selected = self.tree_enrollments.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select an enrolled student.")
            return
        if not messagebox.askyesno("Confirm Delete", "Remove this enrollment?"):
            return
        try:
            enrollment_id = self.tree_enrollments.item(selected[0], "values")[0]
            self.enrollment_service.remove_enrollment(enrollment_id)
            self.load_enrollments()
        except ValueError as error:
            messagebox.showwarning("Cannot Remove", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not remove the enrollment. Refresh and try again.")
