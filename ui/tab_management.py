# tab_management.py - Tab for managing Students, Teachers, and Subjects

from tkinter import ttk, messagebox

from models import Student, Teacher, Subject
from services.student_service import StudentService
from services.teacher_service import TeacherService
from services.subject_service import SubjectService
from ui.theme import style_table, compact_header, add_message_bar, show_message, form_panel


class ManagementTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Page.TFrame")
        compact_header(self.winfo_toplevel())
        self.student_service = StudentService()
        self.teacher_service = TeacherService()
        self.subject_service = SubjectService()

        self._build_subnotebook()

    def _build_subnotebook(self):
        self.sub_notebook = ttk.Notebook(self)
        self.sub_notebook.pack(fill="both", expand=True, padx=8, pady=8)

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
        super().__init__(parent, style="Page.TFrame")
        self.service = service
        self.selected_id = None

        self.message_label = add_message_bar(self)
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        self._build_form()
        self._build_buttons()
        self._build_table()

    def _build_form(self):
        form_frame = form_panel(self, text="Student Form")
        form_frame.pack(fill="x", padx=8, pady=8)

        form_frame.columnconfigure(1, weight=1, uniform="fields")
        form_frame.columnconfigure(3, weight=1, uniform="fields")

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
            ttk.Label(form_frame, text=label_text + ":").grid(row=r, column=c, padx=8, pady=8, sticky="w")
            if key == "status":
                entry = ttk.Combobox(form_frame, values=["active", "inactive", "graduated", "leave"], width=20)
                entry.set("active")
            else:
                entry = ttk.Entry(form_frame, width=20)
            entry.grid(row=r, column=c + 1, padx=8, pady=8, sticky="ew")
            self.entries[key] = entry

    def _build_buttons(self):
        btn_frame = ttk.Frame(self, style="Page.TFrame")
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))
        for column in range(5):
            btn_frame.columnconfigure(column, weight=1, uniform="actions")
        ttk.Button(
            btn_frame, text="Add",
            command=self.add_student
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ttk.Button(
            btn_frame, text="Update",
            command=self.update_student
        ).grid(row=0, column=1, padx=(0, 8), sticky="ew")
        ttk.Button(
            btn_frame, text="Delete", style="Delete.TButton",
            command=self.delete_student
        ).grid(row=0, column=2, padx=(0, 8), sticky="ew")
        ttk.Button(
            btn_frame, text="Clear",
            command=self.clear_form
        ).grid(row=0, column=3, padx=(0, 8), sticky="ew")
        ttk.Button(
            btn_frame, text="View",
            command=self.load_data
        ).grid(row=0, column=4, padx=(0, 8), sticky="ew")

    def _build_table(self):
        list_header = ttk.Frame(self, style="Page.TFrame")
        list_header.pack(fill="x", padx=8, pady=(8, 8))
        ttk.Label(list_header, text="Student Records", style="Heading.TLabel").pack(side="left")
        search_frame = ttk.Frame(list_header, style="Page.TFrame")
        search_frame.pack(side="right")
        ttk.Label(search_frame, text="Search:", style="Page.TLabel").pack(side="left", padx=8)
        self.search_entry = ttk.Entry(search_frame, width=24)
        self.search_entry.pack(side="left", padx=8)
        ttk.Button(
            search_frame, text="Search",
            command=self.search_data
        ).pack(side="left", padx=8)
        ttk.Button(
            search_frame, text="View All",
            command=self.load_data
        ).pack(side="left", padx=8)

        table_frame = ttk.Frame(self, style="Page.TFrame")
        table_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        cols = ("id", "first_name", "last_name", "email", "program", "status", "year_level")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        style_table(self.tree)
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
        self.tree.column("email", width=144, minwidth=96, stretch=False)
        self.tree.column("program", width=120)
        self.tree.column("status", width=90)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_data(self, query=""):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            students = self.service.search(query) if query else self.service.find_all()
            for index, s in enumerate(students):
                self.tree.insert("", "end", tags=("even" if index % 2 == 0 else "odd",), values=(
                    s.student_id, s.first_name, s.last_name, s.email or "", s.program or "", s.status, s.year_level
                ))
        except Exception:
            show_message(self, messagebox.showerror, "Error", "Could not load records. Check the database connection.")

    def search_data(self):
        self.load_data(self.search_entry.get().strip())

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
            show_message(self, messagebox.showwarning, "No Selection", "Select a student to update.")
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
            show_message(self, messagebox.showinfo, "Success", "Student saved.")
            self.clear_form()
            self.load_data()
        except ValueError as error:
            show_message(self, messagebox.showwarning, "Validation", str(error))
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not save the student. Check the database connection.")

    def delete_student(self):
        if not self.selected_id:
            show_message(self, messagebox.showwarning, "No Selection", "Select a student to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this student?"):
            return
        try:
            self.service.delete(self.selected_id)
            show_message(self, messagebox.showinfo, "Success", "Student deleted.")
            self.clear_form()
            self.load_data()
        except ValueError as error:
            show_message(self, messagebox.showwarning, "Cannot Delete", str(error))
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not delete the student. Refresh the list and try again.")

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
        super().__init__(parent, style="Page.TFrame")
        self.service = service
        self.selected_id = None

        self.message_label = add_message_bar(self)
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        self._build_form()
        self._build_buttons()
        self._build_table()

    def _build_form(self):
        form_frame = form_panel(self, text="Teacher Form")
        form_frame.pack(fill="x", padx=8, pady=8)

        form_frame.columnconfigure(1, weight=1, uniform="fields")
        form_frame.columnconfigure(3, weight=1, uniform="fields")

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
            ttk.Label(form_frame, text=label_text + ":").grid(row=r, column=c, padx=8, pady=8, sticky="w")
            if key == "status":
                entry = ttk.Combobox(form_frame, values=["active", "inactive", "on-leave"], width=20)
                entry.set("active")
            else:
                entry = ttk.Entry(form_frame, width=20)
            entry.grid(row=r, column=c + 1, padx=8, pady=8, sticky="ew")
            self.entries[key] = entry

    def _build_buttons(self):
        btn_frame = ttk.Frame(self, style="Page.TFrame")
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))
        for column in range(5):
            btn_frame.columnconfigure(column, weight=1, uniform="actions")
        ttk.Button(
            btn_frame, text="Add",
            command=self.add_teacher
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ttk.Button(
            btn_frame, text="Update",
            command=self.update_teacher
        ).grid(row=0, column=1, padx=(0, 8), sticky="ew")
        ttk.Button(
            btn_frame, text="Delete", style="Delete.TButton",
            command=self.delete_teacher
        ).grid(row=0, column=2, padx=(0, 8), sticky="ew")
        ttk.Button(
            btn_frame, text="Clear",
            command=self.clear_form
        ).grid(row=0, column=3, padx=(0, 8), sticky="ew")
        ttk.Button(
            btn_frame, text="View",
            command=self.load_data
        ).grid(row=0, column=4, padx=(0, 8), sticky="ew")

    def _build_table(self):
        list_header = ttk.Frame(self, style="Page.TFrame")
        list_header.pack(fill="x", padx=8, pady=(8, 8))
        ttk.Label(list_header, text="Teacher Records", style="Heading.TLabel").pack(side="left")
        search_frame = ttk.Frame(list_header, style="Page.TFrame")
        search_frame.pack(side="right")
        ttk.Label(search_frame, text="Search:", style="Page.TLabel").pack(side="left", padx=8)
        self.search_entry = ttk.Entry(search_frame, width=24)
        self.search_entry.pack(side="left", padx=8)
        ttk.Button(
            search_frame, text="Search",
            command=self.search_data
        ).pack(side="left", padx=8)
        ttk.Button(
            search_frame, text="View All",
            command=self.load_data
        ).pack(side="left", padx=8)

        table_frame = ttk.Frame(self, style="Page.TFrame")
        table_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        cols = ("id", "first_name", "last_name", "email", "department", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        style_table(self.tree)
        self.tree.heading("id", text="ID")
        self.tree.heading("first_name", text="First Name")
        self.tree.heading("last_name", text="Last Name")
        self.tree.heading("email", text="Email")
        self.tree.heading("department", text="Department")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=110)
        self.tree.column("first_name", width=140)
        self.tree.column("last_name", width=140)
        self.tree.column("email", width=144, minwidth=96, stretch=False)
        self.tree.column("department", width=280)
        self.tree.column("status", width=90)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_data(self, query=""):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            teachers = self.service.search(query) if query else self.service.find_all()
            for index, t in enumerate(teachers):
                self.tree.insert("", "end", tags=("even" if index % 2 == 0 else "odd",), values=(
                    t.teacher_id, t.first_name, t.last_name, t.email or "", t.department or "", t.status
                ))
        except Exception:
            show_message(self, messagebox.showerror, "Error", "Could not load records. Check the database connection.")

    def search_data(self):
        self.load_data(self.search_entry.get().strip())

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
            show_message(self, messagebox.showwarning, "No Selection", "Select a teacher to update.")
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
            show_message(self, messagebox.showinfo, "Success", "Teacher saved.")
            self.clear_form()
            self.load_data()
        except ValueError as error:
            show_message(self, messagebox.showwarning, "Validation", str(error))
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not save the teacher. Check the database connection.")

    def delete_teacher(self):
        if not self.selected_id:
            show_message(self, messagebox.showwarning, "No Selection", "Select a teacher to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this teacher?"):
            return
        try:
            self.service.delete(self.selected_id)
            show_message(self, messagebox.showinfo, "Success", "Teacher deleted.")
            self.clear_form()
            self.load_data()
        except ValueError as error:
            show_message(self, messagebox.showwarning, "Cannot Delete", str(error))
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not delete the teacher. Refresh the list and try again.")

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
        super().__init__(parent, style="Page.TFrame")
        self.service = service
        self.selected_id = None

        self.message_label = add_message_bar(self)
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        self._build_form()
        self._build_buttons()
        self._build_table()

    def _build_form(self):
        form_frame = form_panel(self, text="Subject Form")
        form_frame.pack(fill="x", padx=8, pady=8)

        form_frame.columnconfigure(1, weight=1, uniform="fields")
        form_frame.columnconfigure(3, weight=1, uniform="fields")

        self.entries = {}
        fields = [
            ("Subject Code", "subject_code", 0, 0),
            ("Subject Name", "subject_name", 0, 2),
            ("Units", "units", 1, 0),
            ("Description", "description", 1, 2),
        ]

        for label_text, key, r, c in fields:
            ttk.Label(form_frame, text=label_text + ":").grid(row=r, column=c, padx=8, pady=8, sticky="w")
            entry = ttk.Entry(form_frame, width=20)
            entry.grid(row=r, column=c + 1, padx=8, pady=8, sticky="ew")
            self.entries[key] = entry
        self.entries["units"].insert(0, "3")

    def _build_buttons(self):
        btn_frame = ttk.Frame(self, style="Page.TFrame")
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))
        for column in range(5):
            btn_frame.columnconfigure(column, weight=1, uniform="actions")
        ttk.Button(
            btn_frame, text="Add",
            command=self.add_subject
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ttk.Button(
            btn_frame, text="Update",
            command=self.update_subject
        ).grid(row=0, column=1, padx=(0, 8), sticky="ew")
        ttk.Button(
            btn_frame, text="Delete", style="Delete.TButton",
            command=self.delete_subject
        ).grid(row=0, column=2, padx=(0, 8), sticky="ew")
        ttk.Button(
            btn_frame, text="Clear",
            command=self.clear_form
        ).grid(row=0, column=3, padx=(0, 8), sticky="ew")
        ttk.Button(
            btn_frame, text="View",
            command=self.load_data
        ).grid(row=0, column=4, padx=(0, 8), sticky="ew")

    def _build_table(self):
        list_header = ttk.Frame(self, style="Page.TFrame")
        list_header.pack(fill="x", padx=8, pady=(8, 8))
        ttk.Label(list_header, text="Subject Records", style="Heading.TLabel").pack(side="left")
        table_frame = ttk.Frame(self, style="Page.TFrame")
        table_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        cols = ("id", "code", "name", "units", "description")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        style_table(self.tree)
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

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            subjects = self.service.find_all()
            for index, s in enumerate(subjects):
                self.tree.insert("", "end", tags=("even" if index % 2 == 0 else "odd",), values=(
                    s.subject_id, s.subject_code, s.subject_name, s.units, s.description or ""
                ))
        except Exception:
            show_message(self, messagebox.showerror, "Error", "Could not load records. Check the database connection.")

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
            show_message(self, messagebox.showwarning, "No Selection", "Select a subject to update.")
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
            show_message(self, messagebox.showinfo, "Success", "Subject saved.")
            self.clear_form()
            self.load_data()
        except ValueError as error:
            show_message(self, messagebox.showwarning, "Validation", str(error))
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not save the subject. Check the database connection.")

    def delete_subject(self):
        if not self.selected_id:
            show_message(self, messagebox.showwarning, "No Selection", "Select a subject to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this subject?"):
            return
        try:
            self.service.delete(self.selected_id)
            show_message(self, messagebox.showinfo, "Success", "Subject deleted.")
            self.clear_form()
            self.load_data()
        except ValueError as error:
            show_message(self, messagebox.showwarning, "Cannot Delete", str(error))
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not delete the subject. Refresh the list and try again.")

    def clear_form(self):
        for k in ["subject_code", "subject_name", "description"]:
            self.entries[k].delete(0, "end")
        self.entries["units"].delete(0, "end")
        self.entries["units"].insert(0, "3")
        self.selected_id = None
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())
