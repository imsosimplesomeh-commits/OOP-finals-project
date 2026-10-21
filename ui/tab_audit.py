# tab_audit.py - read-only view of the audit_log table (GR-04)

from tkinter import ttk, messagebox

from repositories import AuditRepository
from ui.theme import style_table, add_message_bar, show_message


class AuditLogTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Page.TFrame")
        self.audit_repo = AuditRepository()
        self.message_label = add_message_bar(self)
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        header = ttk.Frame(self, style="Page.TFrame")
        header.pack(fill="x", padx=8, pady=8)
        ttk.Label(header, text="Audit Log", style="Heading.TLabel").pack(side="left")
        ttk.Button(header, text="Refresh", command=self.load_data).pack(side="right", padx=8)

        table_frame = ttk.Frame(self, style="Page.TFrame")
        table_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        cols = ("log_id", "table_name", "record_id", "action", "old_value", "new_value", "changed_by", "changed_at")
        headings = ("ID", "Table", "Record", "Action", "Old Value", "New Value", "Changed By", "Changed At")
        widths = (50, 170, 70, 70, 260, 260, 100, 150)
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=16)
        style_table(self.tree)
        for col, text, width in zip(cols, headings, widths):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, stretch=col in ("old_value", "new_value"))
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            # newest change first, so the latest edit is at the top
            logs = list(reversed(self.audit_repo.find_all()))
            for index, log in enumerate(logs):
                self.tree.insert("", "end", tags=("even" if index % 2 == 0 else "odd",), values=(
                    log.log_id, log.table_name, log.record_id, log.action,
                    log.old_value or "", log.new_value or "", log.changed_by,
                    log.changed_at.strftime("%Y-%m-%d %H:%M:%S") if log.changed_at else "",
                ))
            self.message_label.configure(text=f"{len(logs)} audit entries.", style="Message.TLabel")
        except Exception:
            show_message(self, messagebox.showerror, "Database Error", "Could not load the audit log. Check the database connection.")
