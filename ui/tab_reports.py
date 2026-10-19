# tab_reports.py - Tab for generating and exporting academic reports

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

from services.class_service import ClassService
from services.student_service import StudentService
from services import ReportService
from ui.report_document import report_text, export_pdf
from ui.theme import VOID, LINE, BRASS, PARCHMENT, style_table


class ReportsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.class_service = ClassService()
        self.student_service = StudentService()
        self.report_service = ReportService()

        self.class_map = {}
        self.student_map = {}
        self.current_report_data = None

        self._build_ui()
        self.load_dropdowns()

    def _build_ui(self):
        self._build_filters()

        self.nb_views = ttk.Notebook(self)
        self.nb_views.pack(fill="both", expand=True, padx=10, pady=6)

        self._build_document_view()
        self._build_table_view()

    def _build_filters(self):
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

        buttons = ttk.Frame(ctrl_frame)
        buttons.pack(fill="x", padx=6, pady=(0, 4))
        ttk.Button(buttons, text="Generate Report", command=self.generate_report).pack(side="left", padx=4)
        ttk.Button(buttons, text="Export / Save to File", command=self.export_report).pack(side="left", padx=4)
        ttk.Button(buttons, text="Export PDF", command=self.export_pdf).pack(side="left", padx=4)

    def _build_document_view(self):
        self.doc_frame = ttk.Frame(self.nb_views)
        self.nb_views.add(self.doc_frame, text="Document View")

        self.txt_preview = tk.Text(
            self.doc_frame, wrap="none", font=("Consolas", 10),
            bg=VOID, fg=PARCHMENT, insertbackground=PARCHMENT,
            selectbackground=BRASS, selectforeground=VOID,
            relief="flat", borderwidth=0, padx=14, pady=12,
            highlightthickness=1, highlightbackground=LINE, highlightcolor=BRASS,
        )
        scroll_y = ttk.Scrollbar(self.doc_frame, orient="vertical", command=self.txt_preview.yview)
        scroll_x = ttk.Scrollbar(self.doc_frame, orient="horizontal", command=self.txt_preview.xview)
        self.txt_preview.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.txt_preview.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

    def _build_table_view(self):
        self.grid_frame = ttk.Frame(self.nb_views)
        self.nb_views.add(self.grid_frame, text="Data Table View")

        self.tree = ttk.Treeview(self.grid_frame, show="headings")
        style_table(self.tree)
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
            self.student_map = {f"{s.full_name} ({s.student_id})": s.student_id for s in students}

            self.on_report_type_change(None)
        except Exception:
            messagebox.showerror("Database Error", "Could not load report choices. Check the database connection.")

    def on_report_type_change(self, event):
        rtype = self.cb_report_type.get()

        if rtype in ["Class List", "Grade Sheet"]:
            self.lbl_filter.config(text="Class Offering:")
            choices = self.class_map
        else:
            self.lbl_filter.config(text="Student:")
            choices = self.student_map
        self.cb_filter["values"] = list(choices.keys())
        if choices:
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
            elif rtype == "Grade Sheet":
                offering_id = self.class_map.get(filter_val)
                data = self.report_service.generate_grade_sheet_report(offering_id)
            elif rtype == "Student Grade Report":
                student_id = self.student_map.get(filter_val)
                data = self.report_service.generate_student_grade_report(student_id)
            else:
                return
            self._display_report(data)
        except ValueError as error:
            messagebox.showwarning("Report", str(error))
        except Exception:
            messagebox.showerror("Report", "Could not generate the report. Check the database connection.")

    def _display_report(self, data):
        self.current_report_data = data
        self.txt_preview.delete("1.0", "end")
        self.txt_preview.insert("1.0", report_text(data))
        cols = [str(i) for i in range(len(data["columns"]))]
        self._setup_tree(cols, data["columns"])
        for index, row in enumerate(data["rows"]):
            self.tree.insert("", "end", tags=("even" if index % 2 == 0 else "odd",), values=row)

    def export_pdf(self):
        if not self.current_report_data:
            messagebox.showwarning("Empty", "Generate a report first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF File", "*.pdf")],
            title="Export Academic Report as PDF",
        )
        if not path:
            return
        try:
            export_pdf(self.current_report_data, path)
            messagebox.showinfo("Export Successful", f"Report saved to:\n{path}")
        except ImportError:
            messagebox.showerror("Export PDF", "Install the dependencies with: python -m pip install -r requirements.txt")
        except Exception:
            messagebox.showerror("Export PDF", "Could not save the PDF. Check the file location and close any open copy.")

    def _setup_tree(self, cols, headings):
        for r in self.tree.get_children():
            self.tree.delete(r)
        self.tree["columns"] = cols
        for col, head in zip(cols, headings):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=110, stretch=True)

    def export_report(self):
        content = report_text(self.current_report_data) if self.current_report_data else ""
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
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([data["title"]])
            for line in data["header"]:
                writer.writerow([line])
            writer.writerow(data["columns"])
            writer.writerows(data["rows"])
            for line in data["summary"]:
                writer.writerow([line])
