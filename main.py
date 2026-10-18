# main.py - Student Information and Grading System GUI
# CSPC 103 Finals Project - Object Oriented Programming

import tkinter as tk
from tkinter import ttk, messagebox

from db import init_db
from ui.tab_management import ManagementTab
from ui.tab_class_enrollment import ClassEnrollmentTab
from ui.tab_score_grading import ScoreGradingTab
from ui.tab_reports import ReportsTab


class StudentGradeManagementApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Information and Grading System - CSPC 103")
        self.geometry("1120x720")
        self.minsize(980, 620)

        self._apply_theme()

        # make sure tables exist
        try:
            init_db()
        except Exception:
            messagebox.showwarning(
                "Database Warning",
                "Could not initialize the database. Check PostgreSQL and your connection settings."
            )

        # header title
        header = ttk.Frame(self, padding=(10, 8))
        header.pack(fill="x")
        ttk.Label(
            header,
            text="Student Information and Grading System",
            font=("Segoe UI", 14, "bold")
        ).pack(side="left")
        ttk.Label(
            header,
            text="CSPC 103 Finals Project | NDMU CEAC",
            font=("Segoe UI", 9, "italic"),
            foreground="#555555"
        ).pack(side="right", padx=10)

        # 4 main tabs using ttk.Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        self.tab_mgmt = ManagementTab(self.notebook)
        self.notebook.add(self.tab_mgmt, text="1. Management (Students, Teachers, Subjects)")

        self.tab_class = ClassEnrollmentTab(self.notebook)
        self.notebook.add(self.tab_class, text="2. Class Offerings & Enrollment")

        self.tab_grading = ScoreGradingTab(self.notebook)
        self.notebook.add(self.tab_grading, text="3. Score Entry & Grade Calculation")

        self.tab_reports = ReportsTab(self.notebook)
        self.notebook.add(self.tab_reports, text="4. Reports (Class List, Grade Sheet, Student Report)")

        # reload dropdowns and tables whenever the user clicks another tab
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # bottom status bar
        status_bar = ttk.Frame(self, relief="sunken", padding=(6, 2))
        status_bar.pack(fill="x", side="bottom")
        self.lbl_status = ttk.Label(
            status_bar,
            text="System Ready | PostgreSQL Database: Modelo_CSPC103",
            font=("Segoe UI", 8)
        )
        self.lbl_status.pack(side="left")

    def _apply_theme(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TNotebook.Tab", padding=(12, 6), font=("Segoe UI", 9, "bold"))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("TLabelframe.Label", font=("Segoe UI", 9, "bold"))

    def _on_tab_changed(self, event):
        # refresh data on the selected tab so newly added rows show up
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