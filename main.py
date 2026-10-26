# main.py - Student Information and Grading System GUI
# CSPC 103 Finals Project - Object Oriented Programming

import tkinter as tk
from tkinter import ttk, messagebox

from db import DB_CONFIG, init_db, reset_database
from ui.tab_management import ManagementTab
from ui.tab_class_enrollment import ClassEnrollmentTab
from ui.tab_score_grading import ScoreGradingTab
from ui.tab_reports import ReportsTab
from ui.tab_audit import AuditLogTab
from ui.theme import apply_theme, toggle_theme


class StudentGradeManagementApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("The Registry")
        self.geometry("1280x820")
        self.minsize(1180, 780)

        apply_theme(self)

        # Keep the footer consistent with the existing database check.
        database_ready = True
        try:
            init_db()
        except Exception:
            database_ready = False
            messagebox.showwarning(
                "Database Warning",
                "Could not initialize the database. Check PostgreSQL and your connection settings."
            )

        self._build_header()
        self._build_status_bar(database_ready)

        # The notebook keeps the original page-change and refresh behavior.
        self.notebook = ttk.Notebook(self, style="Sidebar.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=16, pady=(0, 6))
        self._build_tabs()

    def _build_header(self):
        header = ttk.Frame(self, padding=(18, 12), style="Banner.TFrame")
        header.pack(fill="x", padx=16, pady=(14, 8))
        ttk.Label(
            header,
            text="◆   T H E   R E G I S T R Y   ◆",
            style="Title.TLabel"
        ).pack(pady=(3, 2))
        ttk.Label(
            header,
            text="Student Records and Grading · CSPC 103 · NDMU",
            style="Subtitle.TLabel"
        ).pack()
        ttk.Separator(self, orient="horizontal").pack(
            fill="x", padx=32, pady=(0, 6)
        )

    def _build_status_bar(self, database_ready):
        # reserve space before the notebook fills the window
        status_bar = ttk.Frame(self, padding=(16, 6), style="Page.TFrame")
        status_bar.pack(fill="x", side="bottom")
        self.lbl_status = ttk.Label(
            status_bar,
            text=(f"Database ready | {DB_CONFIG['dbname']}" if database_ready
                  else "Database unavailable | Check PostgreSQL and connection settings"),
            style="Success.Status.TLabel" if database_ready else "Error.Status.TLabel"
        )
        self.lbl_status.pack(side="left")
        ttk.Button(status_bar, text="Reset Database",
                   command=self._reset_database).pack(side="right")
        ttk.Button(status_bar, text="Light / Dark",
                   command=lambda: toggle_theme(self)).pack(side="right", padx=(0, 8))
        ttk.Label(status_bar, text="CSPC 103 | NDMU CEAC",
                  style="Status.TLabel").pack(side="right", padx=16)

    def _build_tabs(self):
        self.notebook.unbind("<<NotebookTabChanged>>")
        for tab in self.notebook.winfo_children():
            tab.destroy()
        self.tab_mgmt = ManagementTab(self.notebook)
        self.notebook.add(self.tab_mgmt, text="I  Records")

        self.tab_class = ClassEnrollmentTab(self.notebook)
        self.notebook.add(self.tab_class, text="II  Classes")

        self.tab_grading = ScoreGradingTab(self.notebook)
        self.notebook.add(self.tab_grading, text="III  Grades")

        self.tab_reports = ReportsTab(self.notebook)
        self.notebook.add(self.tab_reports, text="IV  Reports")

        self.tab_audit = AuditLogTab(self.notebook)
        self.notebook.add(self.tab_audit, text="V  Audit Log")

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
        elif selected_index == 4:
            self.tab_audit.load_data()


if __name__ == "__main__":
    app = StudentGradeManagementApp()
    app.mainloop()
