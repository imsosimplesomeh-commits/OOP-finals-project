# main.py - Student Information and Grading System GUI
# CSPC 103 Finals Project - Object Oriented Programming

import tkinter as tk
from tkinter import ttk, messagebox

from db import DB_CONFIG, init_db, reset_database
from ui.tab_management import ManagementTab
from ui.tab_class_enrollment import ClassEnrollmentTab
from ui.tab_score_grading import ScoreGradingTab
from ui.tab_reports import ReportsTab
from ui.theme import apply_theme


class StudentGradeManagementApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Information and Grading System - CSPC 103")
        self.geometry("1280x820")
        self.minsize(1180, 780)

        apply_theme(self)

        # make sure tables exist
        try:
            init_db()
        except Exception:
            messagebox.showwarning(
                "Database Warning",
                "Could not initialize the database. Check PostgreSQL and your connection settings."
            )

        # header title
        header = ttk.Frame(self, padding=(18, 14), style="Header.TFrame")
        header.pack(fill="x")
        ttk.Label(
            header,
            text="Student Information and Grading System",
            style="Title.TLabel"
        ).pack(side="left")
        ttk.Label(
            header,
            text="CSPC 103 Finals Project | NDMU CEAC",
            style="Subtitle.TLabel"
        ).pack(side="right", padx=10)
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=12, pady=(0, 6))

        # reserve space before the notebook fills the window
        status_bar = ttk.Frame(self, padding=(16, 6))
        status_bar.pack(fill="x", side="bottom")
        self.lbl_status = ttk.Label(
            status_bar,
            text="System Ready | PostgreSQL Database: Modelo_CSPC103",
            style="Status.TLabel"
        )
        self.lbl_status.pack(side="left")
        ttk.Button(status_bar, text="Reset Database", command=self._reset_database).pack(side="right")

        # 4 main tabs using ttk.Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        self._build_tabs()

    def _build_tabs(self):
        self.notebook.unbind("<<NotebookTabChanged>>")
        for tab in self.notebook.winfo_children():
            tab.destroy()
        self.tab_mgmt = ManagementTab(self.notebook)
        self.notebook.add(self.tab_mgmt, text="1. Management")

        self.tab_class = ClassEnrollmentTab(self.notebook)
        self.notebook.add(self.tab_class, text="2. Classes & Enrollment")

        self.tab_grading = ScoreGradingTab(self.notebook)
        self.notebook.add(self.tab_grading, text="3. Scores & Grades")

        self.tab_reports = ReportsTab(self.notebook)
        self.notebook.add(self.tab_reports, text="4. Reports")

        # reload dropdowns and tables whenever the user clicks another tab
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _reset_database(self):
        confirmed = messagebox.askyesno(
            "Reset Database",
            f"Permanently delete all records in database '{DB_CONFIG['dbname']}'?\n\n"
            "This clears all 11 project tables, including scores, grades, and the audit log.\n"
            "This cannot be undone.",
            icon="warning", default=messagebox.NO, parent=self,
        )
        if not confirmed:
            return
        try:
            reset_database()
        except Exception:
            messagebox.showerror("Reset Database", "Could not reset the database. No records were cleared.", parent=self)
            return
        try:
            self._build_tabs()
        except Exception:
            messagebox.showerror("Reset Database", "The database is empty. Restart the app to reload the forms.", parent=self)
            return
        self.lbl_status.config(text="Database reset | Ready for the CRUD test cases")
        messagebox.showinfo("Reset Database", "All project tables are empty. You can start the CRUD test cases.", parent=self)

    def _on_tab_changed(self, event):
        # refresh data on the selected tab so newly added rows show up
        if not self.notebook.tabs():
            return
        selected_index = self.notebook.index(self.notebook.select())
        if selected_index == 0:
            self.tab_mgmt.refresh()
        elif selected_index == 1:
            self.tab_class.refresh_all()
        elif selected_index == 2:
            self.tab_grading.refresh_all()
        elif selected_index == 3:
            self.tab_reports.load_dropdowns()


if __name__ == "__main__":
    app = StudentGradeManagementApp()
    app.mainloop()
