# tab_management.py - Tab for managing Students, Teachers, and Subjects

import tkinter as tk
from tkinter import ttk, messagebox

from models import Student, Teacher, Subject
from services.student_service import StudentService
from services.teacher_service import TeacherService
from services.subject_service import SubjectService


class ManagementTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.student_service = StudentService()
        self.teacher_service = TeacherService()
        self.subject_service = SubjectService()

        self._build_subnotebook()

    def _build_subnotebook(self):
        self.sub_notebook = ttk.Notebook(self)
        self.sub_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.student_view = StudentManagementView(self.sub_notebook, self.student_service)
        self.sub_notebook.add(self.student_view, text="Students")

        self.teacher_view = TeacherManagementView(self.sub_notebook, self.teacher_service)
        self.sub_notebook.add(self.teacher_view, text="Teachers")

        self.subject_view = SubjectManagementView(self.sub_notebook, self.subject_service)
        self.sub_notebook.add(self.subject_view, text="Subjects")

    def refresh(self):
        self.student_view.load_data()
        self.teacher_view.load_data()
        self.subject_view.load_data()


# -------------------------------------------------------------
# 1. Student Management View
# -------------------------------------------------------------
class StudentManagementView(ttk.Frame):
    def __init__(self, parent, service):
        super().__init__(parent)
        self.service = service
        self.selected_id = None

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        # input form
        form_frame = ttk.LabelFrame(self, text="Student Details")
        form_frame.pack(fill="x", padx=10, pady=8)

        self.entries = {}
        fields = [
            ("Student Number", "student_id", 0, 0),
            ("First Name", "first_name", 0, 2),
            ("Last Name", "last_name", 1, 0),
            ("Email (optional)", "email", 1, 2),
            ("Program", "program", 2, 0),
            ("Year Level", "year_level", 2, 2),
            ("Status", "status", 3, 0),
        ]

        for label_text, key, r, c in fields:
            ttk.Label(form_frame, text=label_text + ":").grid(row=r, column=c, padx=6, pady=4, sticky="e")
            if key == "status":
                entry = ttk.Combobox(form_frame, values=["active", "inactive", "graduated", "leave"], width=28)
                entry.set("active")
            else:
                entry = ttk.Entry(form_frame, width=30)
            entry.grid(row=r, column=c + 1, padx=6, pady=4, sticky="w")
            self.entries[key] = entry

        # search bar
        search_frame = ttk.Frame(form_frame)
        search_frame.grid(row=3, column=2, columnspan=2, padx=6, pady=4, sticky="w")
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=2)
        self.search_entry = ttk.Entry(search_frame, width=20)
        self.search_entry.pack(side="left", padx=4)
        ttk.Button(search_frame, text="Find", command=self.search_data).pack(side="left", padx=2)
        ttk.Button(search_frame, text="Reset", command=self.load_data).pack(side="left", padx=2)

        # action buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=4)
        ttk.Button(btn_frame, text="Add Student", command=self.add_student).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Update Student", command=self.update_student).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Delete Student", command=self.delete_student).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_form).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Refresh", command=self.load_data).pack(side="left", padx=4)

        # table
        cols = ("id", "first_name", "last_name", "email", "program", "status", "year_level")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        self.tree.heading("id", text="ID")
        self.tree.heading("first_name", text="First Name")
        self.tree.heading("last_name", text="Last Name")
        self.tree.heading("email", text="Email")
        self.tree.heading("program", text="Program")
        self.tree.heading("year_level", text="Year Level")
        self.tree.column("year_level", width=70)
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=110)
        self.tree.column("first_name", width=140)
        self.tree.column("last_name", width=140)
        self.tree.column("email", width=180)
        self.tree.column("program", width=120)
        self.tree.column("status", width=90)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=8)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            students = self.service.find_all()
            for s in students:
                self.tree.insert("", "end", values=(
                    s.student_id, s.first_name, s.last_name, s.email or "", s.program or "", s.status, s.year_level
                ))
        except Exception:
            messagebox.showerror("Error", "Could not load records. Check the database connection.")

    def search_data(self):
        query = self.search_entry.get().strip()
        if not query:
            self.load_data()
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            students = self.service.search(query)
            for s in students:
                self.tree.insert("", "end", values=(
                    s.student_id, s.first_name, s.last_name, s.email or "", s.program or "", s.status, s.year_level
                ))
        except Exception:
            messagebox.showerror("Error", "Could not load records. Check the database connection.")

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        self.selected_id = vals[0]
        self.entries["student_id"].delete(0, "end")
        self.entries["student_id"].insert(0, vals[0])
        self.entries["first_name"].delete(0, "end")
        self.entries["first_name"].insert(0, vals[1])
        self.entries["last_name"].delete(0, "end")
        self.entries["last_name"].insert(0, vals[2])
        self.entries["email"].delete(0, "end")
        self.entries["email"].insert(0, vals[3])
        self.entries["program"].delete(0, "end")
        self.entries["program"].insert(0, vals[4])
        self.entries["status"].set(vals[5])
        self.entries["year_level"].delete(0, "end")
        self.entries["year_level"].insert(0, vals[6])

    def add_student(self):
        self.save_form(False)

    def update_student(self):
        self.save_form(True)

    def save_form(self, updating):
        if updating and not self.selected_id:
            messagebox.showwarning("No Selection", "Select a student to update.")
            return
        try:
            record = Student(
                student_id=self.entries["student_id"].get(),
                first_name=self.entries["first_name"].get(),
                last_name=self.entries["last_name"].get(),
                email=self.entries["email"].get(),
                program=self.entries["program"].get(),
                year_level=self.entries["year_level"].get(),
                status=self.entries["status"].get()
            )
            if updating:
                self.service.update(record, self.selected_id)
            else:
                self.service.add(record)
            messagebox.showinfo("Success", "Student saved.")
            self.clear_form()
            self.load_data()
        except ValueError as error:
            messagebox.showwarning("Validation", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not save the student. Check the database connection.")

    def delete_student(self):
        if not self.selected_id:
            messagebox.showwarning("No Selection", "Select a student to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this student?"):
            return
        try:
            self.service.delete(self.selected_id)
            messagebox.showinfo("Success", "Student deleted.")
            self.clear_form()
            self.load_data()
        except ValueError as error:
            messagebox.showwarning("Cannot Delete", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not delete the student. Refresh the list and try again.")

    def clear_form(self):
        for k in ["student_id", "first_name", "last_name", "email", "program", "year_level"]:
            self.entries[k].delete(0, "end")
        self.entries["status"].set("active")
        self.selected_id = None
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())


# -------------------------------------------------------------
# 2. Teacher Management View
# -------------------------------------------------------------
class TeacherManagementView(ttk.Frame):
    def __init__(self, parent, service):
        super().__init__(parent)
        self.service = service
        self.selected_id = None

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        form_frame = ttk.LabelFrame(self, text="Teacher Details")
        form_frame.pack(fill="x", padx=10, pady=8)

        self.entries = {}
        fields = [
            ("Teacher ID", "teacher_id", 0, 0),
            ("First Name", "first_name", 0, 2),
            ("Last Name", "last_name", 1, 0),
            ("Email (optional)", "email", 1, 2),
            ("Department", "department", 2, 0),
            ("Status", "status", 2, 2),
        ]

        for label_text, key, r, c in fields:
            ttk.Label(form_frame, text=label_text + ":").grid(row=r, column=c, padx=6, pady=4, sticky="e")
            if key == "status":
                entry = ttk.Combobox(form_frame, values=["active", "inactive", "on-leave"], width=28)
                entry.set("active")
            else:
                entry = ttk.Entry(form_frame, width=30)
            entry.grid(row=r, column=c + 1, padx=6, pady=4, sticky="w")
            self.entries[key] = entry

        # search bar
        search_frame = ttk.Frame(form_frame)
        search_frame.grid(row=3, column=2, columnspan=2, padx=6, pady=4, sticky="w")
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=2)
        self.search_entry = ttk.Entry(search_frame, width=20)
        self.search_entry.pack(side="left", padx=4)
        ttk.Button(search_frame, text="Find", command=self.search_data).pack(side="left", padx=2)
        ttk.Button(search_frame, text="Reset", command=self.load_data).pack(side="left", padx=2)

        # buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=4)
        ttk.Button(btn_frame, text="Add Teacher", command=self.add_teacher).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Update Teacher", command=self.update_teacher).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Delete Teacher", command=self.delete_teacher).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_form).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Refresh", command=self.load_data).pack(side="left", padx=4)

        # table
        cols = ("id", "first_name", "last_name", "email", "department", "status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        self.tree.heading("id", text="ID")
        self.tree.heading("first_name", text="First Name")
        self.tree.heading("last_name", text="Last Name")
        self.tree.heading("email", text="Email")
        self.tree.heading("department", text="Department")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=110)
        self.tree.column("first_name", width=140)
        self.tree.column("last_name", width=140)
        self.tree.column("email", width=180)
        self.tree.column("department", width=140)
        self.tree.column("status", width=90)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=8)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            teachers = self.service.find_all()
            for t in teachers:
                self.tree.insert("", "end", values=(
                    t.teacher_id, t.first_name, t.last_name, t.email or "", t.department or "", t.status
                ))
        except Exception:
            messagebox.showerror("Error", "Could not load records. Check the database connection.")

    def search_data(self):
        query = self.search_entry.get().strip()
        if not query:
            self.load_data()
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            teachers = self.service.search(query)
            for t in teachers:
                self.tree.insert("", "end", values=(
                    t.teacher_id, t.first_name, t.last_name, t.email or "", t.department or "", t.status
                ))
        except Exception:
            messagebox.showerror("Error", "Could not load records. Check the database connection.")

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        self.selected_id = vals[0]
        self.entries["teacher_id"].delete(0, "end")
        self.entries["teacher_id"].insert(0, vals[0])
        self.entries["first_name"].delete(0, "end")
        self.entries["first_name"].insert(0, vals[1])
        self.entries["last_name"].delete(0, "end")
        self.entries["last_name"].insert(0, vals[2])
        self.entries["email"].delete(0, "end")
        self.entries["email"].insert(0, vals[3])
        self.entries["department"].delete(0, "end")
        self.entries["department"].insert(0, vals[4])
        self.entries["status"].set(vals[5])

    def add_teacher(self):
        self.save_form(False)

    def update_teacher(self):
        self.save_form(True)

    def save_form(self, updating):
        if updating and not self.selected_id:
            messagebox.showwarning("No Selection", "Select a teacher to update.")
            return
        try:
            record = Teacher(
                teacher_id=self.entries["teacher_id"].get(),
                first_name=self.entries["first_name"].get(),
                last_name=self.entries["last_name"].get(),
                email=self.entries["email"].get(),
                department=self.entries["department"].get(),
                status=self.entries["status"].get()
            )
            if updating:
                self.service.update(record, self.selected_id)
            else:
                self.service.add(record)
            messagebox.showinfo("Success", "Teacher saved.")
            self.clear_form()
            self.load_data()
        except ValueError as error:
            messagebox.showwarning("Validation", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not save the teacher. Check the database connection.")

    def delete_teacher(self):
        if not self.selected_id:
            messagebox.showwarning("No Selection", "Select a teacher to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this teacher?"):
            return
        try:
            self.service.delete(self.selected_id)
            messagebox.showinfo("Success", "Teacher deleted.")
            self.clear_form()
            self.load_data()
        except ValueError as error:
            messagebox.showwarning("Cannot Delete", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not delete the teacher. Refresh the list and try again.")

    def clear_form(self):
        for k in ["teacher_id", "first_name", "last_name", "email", "department"]:
            self.entries[k].delete(0, "end")
        self.entries["status"].set("active")
        self.selected_id = None
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())


# -------------------------------------------------------------
# 3. Subject Management View
# -------------------------------------------------------------
class SubjectManagementView(ttk.Frame):
    def __init__(self, parent, service):
        super().__init__(parent)
        self.service = service
        self.selected_id = None

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        form_frame = ttk.LabelFrame(self, text="Subject Details")
        form_frame.pack(fill="x", padx=10, pady=8)

        self.entries = {}
        fields = [
            ("Subject Code", "subject_code", 0, 0),
            ("Subject Name", "subject_name", 0, 2),
            ("Units", "units", 1, 0),
            ("Description", "description", 1, 2),
        ]

        for label_text, key, r, c in fields:
            ttk.Label(form_frame, text=label_text + ":").grid(row=r, column=c, padx=6, pady=4, sticky="e")
            entry = ttk.Entry(form_frame, width=30)
            entry.grid(row=r, column=c + 1, padx=6, pady=4, sticky="w")
            self.entries[key] = entry
        self.entries["units"].insert(0, "3")

        # buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=4)
        ttk.Button(btn_frame, text="Add Subject", command=self.add_subject).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Update Subject", command=self.update_subject).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Delete Subject", command=self.delete_subject).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Clear Form", command=self.clear_form).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Refresh", command=self.load_data).pack(side="left", padx=4)

        # table
        cols = ("id", "code", "name", "units", "description")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        self.tree.heading("id", text="ID")
        self.tree.heading("code", text="Subject Code")
        self.tree.heading("name", text="Subject Name")
        self.tree.heading("units", text="Units")
        self.tree.heading("description", text="Description")

        self.tree.column("id", width=0, stretch=False)
        self.tree.column("code", width=120)
        self.tree.column("name", width=220)
        self.tree.column("units", width=70)
        self.tree.column("description", width=250)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=8)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            subjects = self.service.find_all()
            for s in subjects:
                self.tree.insert("", "end", values=(
                    s.subject_id, s.subject_code, s.subject_name, s.units, s.description or ""
                ))
        except Exception:
            messagebox.showerror("Error", "Could not load records. Check the database connection.")

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        self.selected_id = vals[0]
        self.entries["subject_code"].delete(0, "end")
        self.entries["subject_code"].insert(0, vals[1])
        self.entries["subject_name"].delete(0, "end")
        self.entries["subject_name"].insert(0, vals[2])
        self.entries["units"].delete(0, "end")
        self.entries["units"].insert(0, vals[3])
        self.entries["description"].delete(0, "end")
        self.entries["description"].insert(0, vals[4])

    def add_subject(self):
        self.save_form(False)

    def update_subject(self):
        self.save_form(True)

    def save_form(self, updating):
        if updating and not self.selected_id:
            messagebox.showwarning("No Selection", "Select a subject to update.")
            return
        try:
            record = Subject(
                subject_id=self.selected_id if updating else None,
                subject_code=self.entries["subject_code"].get(),
                subject_name=self.entries["subject_name"].get(),
                units=self.entries["units"].get(),
                description=self.entries["description"].get()
            )
            self.service.save(record)
            messagebox.showinfo("Success", "Subject saved.")
            self.clear_form()
            self.load_data()
        except ValueError as error:
            messagebox.showwarning("Validation", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not save the subject. Check the database connection.")

    def delete_subject(self):
        if not self.selected_id:
            messagebox.showwarning("No Selection", "Select a subject to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this subject?"):
            return
        try:
            self.service.delete(self.selected_id)
            messagebox.showinfo("Success", "Subject deleted.")
            self.clear_form()
            self.load_data()
        except ValueError as error:
            messagebox.showwarning("Cannot Delete", str(error))
        except Exception:
            messagebox.showerror("Database Error", "Could not delete the subject. Refresh the list and try again.")

    def clear_form(self):
        for k in ["subject_code", "subject_name", "description"]:
            self.entries[k].delete(0, "end")
        self.entries["units"].delete(0, "end")
        self.entries["units"].insert(0, "3")
        self.selected_id = None
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())
