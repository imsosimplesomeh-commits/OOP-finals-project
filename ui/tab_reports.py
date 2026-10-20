# tab_reports.py - Tab for generating and exporting academic reports

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv

from services.class_service import ClassService
from services.student_service import StudentService
from services import ReportService
from ui.report_document import report_text, export_pdf
from ui.theme import style_table, add_message_bar, show_message, form_panel


class ReportsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Page.TFrame")
        self.class_service = ClassService()
        self.student_service = StudentService()
        self.report_service = ReportService()

        self.class_map = {}
        self.student_map = {}
        self.current_report_data = None

        self._build_ui()
        self.load_dropdowns()

    def _build_ui(self):
        self.message_label = add_message_bar(self)
        self._build_filters()

        self.nb_views = ttk.Notebook(self)
        self.nb_views.pack(fill="both", expand=True, padx=8, pady=8)

        self._build_document_view()
        self._build_table_view()

    def _build_filters(self):
        ctrl_frame = form_panel(self, text="Reports")
        ctrl_frame.pack(fill="x", padx=8, pady=8)

        f1 = ttk.Frame(ctrl_frame)
        f1.pack(fill="x", padx=8, pady=8)
        f1.columnconfigure(1, weight=1)
        f1.columnconfigure(3, weight=2)

        ttk.Label(f1, text="Report Type:").grid(row=0, column=0, padx=8, sticky="w")
        self.cb_report_type = ttk.Combobox(
            f1, values=["Class List", "Grade Sheet", "Student Grade Report"],
            width=22, state="readonly"
        )
        self.cb_report_type.set("Class List")
        self.cb_report_type.grid(row=0, column=1, padx=8, sticky="ew")
        self.cb_report_type.bind("<<ComboboxSelected>>", self.on_report_type_change)

        self.lbl_filter = ttk.Label(f1, text="Class Offering:")
        self.lbl_filter.grid(row=0, column=2, padx=8, sticky="w")
        self.cb_filter = ttk.Combobox(f1, width=32, state="readonly")
        self.cb_filter.grid(row=0, column=3, padx=8, sticky="ew")

        buttons = ttk.Frame(ctrl_frame)
        buttons.pack(fill="x", padx=8, pady=(0, 8))
        for column in range(3):
            buttons.columnconfigure(column, weight=1, uniform="actions")
        ttk.Button(
            buttons, text="View Report",
            command=self.generate_report
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ttk.Button(
            buttons, text="Save Report",
            command=self.export_report
        ).grid(row=0, column=1, padx=(0, 8), sticky="ew")
        ttk.Button(
            buttons, text="Export PDF",
            command=self.export_pdf
        ).grid(row=0, column=2, padx=(0, 8), sticky="ew")

    def _build_document_view(self):
        self.doc_frame = ttk.Frame(self.nb_views, style="Page.TFrame")
        self.nb_views.add(self.doc_frame, text="Document View")

        # Text has no ttk equivalent; use the shared table colors.
        style = ttk.Style(self)
        self.txt_preview = tk.Text(
            self.doc_frame, wrap="none", font=("Consolas", 10),
            bg=style.lookup("Treeview", "background"),
            fg=style.lookup("Treeview", "foreground"),
            insertbackground=style.lookup("Treeview", "foreground"),
            selectbackground=style.lookup("Treeview", "background", ("selected",)),
            selectforeground=style.lookup("Treeview", "foreground", ("selected",)),
            relief="flat", borderwidth=0, padx=14, pady=12,
            highlightthickness=0,
            highlightbackground=style.lookup("TEntry", "bordercolor"),
            highlightcolor=style.lookup("TEntry", "bordercolor", ("focus",)),
        )
        scroll_y = ttk.Scrollbar(self.doc_frame, orient="vertical", command=self.txt_preview.yview)
        scroll_x = ttk.Scrollbar(self.doc_frame, orient="horizontal", command=self.txt_preview.xview)
        self.txt_preview.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.doc_frame.rowconfigure(0, weight=1)
        self.doc_frame.columnconfigure(0, weight=1)
        self.txt_preview.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

    def _build_table_view(self):
        self.grid_frame = ttk.Frame(self.nb_views, style="Page.TFrame")
        self.nb_views.add(self.grid_frame, text="Table View")

        self.tree = ttk.Treeview(self.grid_frame, show="headings")
        style_table(self.tree)
        t_scroll_y = ttk.Scrollbar(self.grid_frame, orient="vertical", command=self.tree.yview)
        t_scroll_x = ttk.Scrollbar(self.grid_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=t_scroll_y.set, xscrollcommand=t_scroll_x.set)

        self.grid_frame.rowconfigure(0, weight=1)
        self.grid_frame.columnconfigure(0, weight=1)
        self.tree.grid(row=0, column=0, sticky="nsew")
        t_scroll_y.grid(row=0, column=1, sticky="ns")
        t_scroll_x.grid(row=1, column=0, sticky="ew")

    def load_dropdowns(self):
        try:
            classes = self.class_service.find_all()
            self.class_map = {f"{c.class_code} - {c.subject_name or c.subject_code} ({c.section or 'N/A'})": c.class_id for c in classes}

            students = self.student_service.find_all()
            self.student_map = {f"{s.full_name} ({s.student_id})": s.student_id for s in students}

            self.on_report_type_change(None)
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not load report choices. Check the database connection.")

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
            show_message(self, messagebox.showwarning, "Validation", "Please select a target class or student.")
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
            show_message(self, messagebox.showwarning, "Report", str(error))
        except Exception:
            show_message(self, messagebox.showerror, "Report", "Could not generate the report. Check the database connection.")

    def _display_report(self, data):
        self.current_report_data = data
        self.txt_preview.delete("1.0", "end")
        self.txt_preview.insert("1.0", report_text(data))
        cols = [str(i) for i in range(len(data["columns"]))]
        self._setup_tree(cols, data["columns"])
        for index, row in enumerate(data["rows"]):
            self.tree.insert("", "end", tags=("even" if index % 2 == 0 else "odd",), values=row)
        self.message_label.configure(text="Report ready.", style="Success.Message.TLabel")

    def export_pdf(self):
        if not self.current_report_data:
            show_message(self, messagebox.showwarning, "Empty", "Generate a report first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF File", "*.pdf")],
            title="Export Academic Report as PDF",
        )
        if not path:
            return
        try:
            export_pdf(self.current_report_data, path)
            show_message(self, messagebox.showinfo, "Export Successful", f"Report saved to:\n{path}")
        except ImportError:
            show_message(self, messagebox.showerror, "Export PDF", "Install the dependencies with: python -m pip install -r requirements.txt")
        except Exception:
            show_message(self, messagebox.showerror, "Export PDF", "Could not save the PDF. Check the file location and close any open copy.")

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
            show_message(self, messagebox.showwarning, "Empty", "Generate a report first.")
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
            show_message(self, messagebox.showinfo, "Export Successful", f"Report saved to:\n{file_path}")
        except Exception as e:
            show_message(self, messagebox.showerror, "Error", f"Failed to save file: {e}")

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
