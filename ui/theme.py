from tkinter import ttk, font, messagebox


VOID = "#110e0b"
PANEL = "#221c16"
LINE = "#6e5634"
NAVY = "#203339"
HOVER = "#342b20"
ROW_ALT = "#27211b"
BRASS = "#b89658"
PARCHMENT = "#ece2d0"
MUTED = "#9c8d74"
CRIMSON = "#a36565"


def apply_theme(root):
    # Clam shows the same borders and colors on Windows.
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(background=VOID)

    font.nametofont("TkDefaultFont").configure(family="Georgia", size=9)
    font.nametofont("TkTextFont").configure(family="Consolas", size=10)
    root.option_add("*TCombobox*Listbox.background", PANEL)
    root.option_add("*TCombobox*Listbox.foreground", PARCHMENT)
    root.option_add("*TCombobox*Listbox.selectBackground", BRASS)
    root.option_add("*TCombobox*Listbox.selectForeground", VOID)
    root.option_add("*TCombobox*Listbox.font", "{Consolas} 9")

    style.configure(".", background=PANEL, foreground=PARCHMENT,
                    font=("Georgia", 9), bordercolor=LINE,
                    lightcolor=LINE, darkcolor=LINE, focuscolor=BRASS)
    style.configure("TFrame", background=PANEL)
    style.configure("Page.TFrame", background=VOID)
    style.configure("Banner.TFrame", background=VOID, bordercolor=VOID,
                    lightcolor=VOID, darkcolor=VOID, borderwidth=0, relief="flat")
    style.configure("TLabel", background=PANEL, foreground=PARCHMENT)
    style.configure("Page.TLabel", background=VOID, foreground=PARCHMENT)
    style.configure("Title.TLabel", background=VOID, foreground=BRASS,
                    font=("Georgia", 22, "bold"))
    style.configure("Subtitle.TLabel", background=VOID, foreground=MUTED,
                    font=("Georgia", 9))
    style.configure("Heading.TLabel", background=VOID, foreground=BRASS,
                    font=("Georgia", 10, "bold"))
    style.configure("Status.TLabel", background=VOID, foreground=MUTED,
                    font=("Georgia", 9))
    style.configure("Success.Status.TLabel", foreground="#9caf8a")
    style.configure("Error.Status.TLabel", foreground="#c88a85")
    style.configure("TLabelframe", background=PANEL, bordercolor=BRASS,
                    lightcolor=BRASS, darkcolor=BRASS, relief="solid",
                    borderwidth=1, padding=8)
    style.configure("TLabelframe.Label", background=PANEL, foreground=BRASS,
                    font=("Georgia", 10, "bold"))
    style.configure("Form.TFrame", background=PANEL, bordercolor=BRASS,
                    lightcolor=BRASS, darkcolor=BRASS, borderwidth=1,
                    relief="solid", padding=(8, 28, 8, 8))
    style.configure("FormTitle.TLabel", background=PANEL, foreground=BRASS,
                    font=("Georgia", 10, "bold"))

    style.configure("Section.TLabelframe", borderwidth=0, relief="flat",
                    bordercolor=PANEL, lightcolor=PANEL, darkcolor=PANEL)
    style.configure("Message.TLabel", background=VOID, foreground=MUTED,
                    font=("Georgia", 9), padding=(8, 8))
    style.configure("Success.Message.TLabel", foreground="#b9dfa5",
                    font=("Georgia", 9, "bold"))
    style.configure("Error.Message.TLabel", foreground="#e8aaa4",
                    font=("Georgia", 9, "bold"))

    style.layout("TNotebook", [("Notebook.padding", {"sticky": "nswe"})])
    style.configure("TNotebook", background=VOID, borderwidth=0, padding=0,
                    tabmargins=(0, 0, 0, 8))
    tab_layout = [
        ("Treeheading.cell", {"sticky": "nswe"}),
        ("Treeheading.border", {"side": "bottom", "sticky": "ew"}),
        ("Notebook.padding", {"sticky": "nswe", "children": [
            ("Notebook.label", {"sticky": "w"})
        ]})
    ]
    style.layout("TNotebook.Tab", tab_layout)
    style.configure("TNotebook.Tab", background=PANEL, foreground=MUTED,
                    borderwidth=1, relief="solid",
                    padding=(16, 12), font=("Georgia", 10, "bold"), width=14, anchor="w")
    style.map("TNotebook.Tab",
              background=[("selected", NAVY), ("active", PANEL)],
              foreground=[("selected", BRASS), ("active", PARCHMENT)],
              bordercolor=[("selected", BRASS), ("!selected", PANEL)],
              lightcolor=[("selected", BRASS), ("!selected", PANEL)],
              darkcolor=[("selected", BRASS), ("!selected", PANEL)],
              padding=[("selected", (16, 12)), ("!selected", (16, 12))],
              expand=[("selected", (0, 0, 0, 0)), ("!selected", (0, 0, 0, 0))])
    # Keep the existing notebook events while placing navigation on the left.
    style.configure("Sidebar.TNotebook", background=VOID, tabposition="wn",
                    tabmargins=(0, 0, 8, 0))
    style.layout("Sidebar.TNotebook.Tab", tab_layout)
    style.configure("Sidebar.TNotebook.Tab", background=VOID)
    style.map("Sidebar.TNotebook.Tab",
              background=[("selected", NAVY), ("active", PANEL), ("!selected", VOID)],
              bordercolor=[("selected", NAVY), ("active", PANEL), ("!selected", VOID)],
              lightcolor=[("selected", NAVY), ("active", PANEL), ("!selected", VOID)],
              darkcolor=[("selected", NAVY), ("active", PANEL), ("!selected", VOID)])
    root.bind("<<NotebookTabChanged>>", highlight_sidebar, add="+")

    style.configure("TButton", background=PANEL, foreground=PARCHMENT,
                    font=("Georgia", 9, "bold"), padding=(10, 6),
                    bordercolor=BRASS, lightcolor=BRASS, darkcolor=LINE,
                    relief="raised", borderwidth=1)
    style.map("TButton",
              background=[("disabled", PANEL), ("pressed", BRASS), ("active", HOVER)],
              foreground=[("disabled", MUTED), ("pressed", VOID)],
              bordercolor=[("focus", PARCHMENT), ("active", BRASS)])
    style.configure("Delete.TButton", bordercolor=CRIMSON,
                    lightcolor=CRIMSON, darkcolor=CRIMSON)
    style.map("Delete.TButton",
              bordercolor=[("focus", CRIMSON), ("active", CRIMSON)],
              background=[("disabled", PANEL), ("pressed", CRIMSON), ("active", HOVER)])

    for name in ("TEntry", "TCombobox"):
        style.configure(name, fieldbackground=VOID, background=PANEL,
                        foreground=PARCHMENT, insertcolor=PARCHMENT,
                        font=("Consolas", 10), padding=(8, 4), bordercolor=LINE,
                        lightcolor=LINE, darkcolor=LINE,
                        selectbackground=BRASS, selectforeground=VOID,
                        arrowcolor=BRASS)
        style.map(name,
                  fieldbackground=[("disabled", PANEL), ("readonly", VOID)],
                  foreground=[("disabled", MUTED), ("readonly", PARCHMENT)],
                  selectbackground=[("!disabled", BRASS)],
                  selectforeground=[("!disabled", VOID)],
                  bordercolor=[("focus", BRASS), ("active", BRASS)],
                  arrowcolor=[("disabled", MUTED), ("active", PARCHMENT)])

    style.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                    foreground=PARCHMENT, font=("Consolas", 9), rowheight=28,
                    bordercolor=PANEL, borderwidth=0, lightcolor=PANEL, darkcolor=PANEL,
                    relief="flat")
    style.map("Treeview", background=[("selected", BRASS)],
              foreground=[("selected", VOID)])
    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    style.layout("Treeview.Heading", [
        ("Treeheading.cell", {"sticky": "nswe"}),
        ("Treeheading.padding", {"sticky": "nswe", "children": [
            ("Treeheading.image", {"side": "right", "sticky": ""}),
            ("Treeheading.text", {"sticky": "we"})
        ]})
    ])
    style.configure("Treeview.Heading", background=PANEL, foreground=BRASS,
                    font=("Georgia", 9, "bold"), padding=(8, 8),
                    bordercolor=PANEL, lightcolor=PANEL, darkcolor=PANEL,
                    borderwidth=0, relief="flat")
    style.map("Treeview.Heading", background=[("active", HOVER)],
              foreground=[("active", PARCHMENT)])

    for name in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        style.configure(name, background=HOVER, troughcolor=VOID,
                        arrowcolor=BRASS, bordercolor=LINE, relief="flat", width=14)
        style.map(name, background=[("pressed", BRASS), ("active", LINE)])
    style.configure("TSeparator", background=BRASS)


def style_table(tree):
    tree.tag_configure("even", background=PANEL)
    tree.tag_configure("odd", background=ROW_ALT)


def form_panel(parent, text):
    return ttk.LabelFrame(parent, text=text)


def compact_header(root):
    # The banner is created in main.py; only its spacing changes here.
    for widget in root.winfo_children():
        if isinstance(widget, ttk.Frame) and widget.cget("style") == "Banner.TFrame":
            widget.configure(padding=(16, 4))
            widget.pack_configure(pady=(8, 8))


def highlight_sidebar(event):
    notebook = event.widget
    if not isinstance(notebook, ttk.Notebook) or notebook.cget("style") != "Sidebar.TNotebook":
        return
    selected = notebook.select()
    for tab in notebook.tabs():
        text = notebook.tab(tab, "text").lstrip("▏ ")
        notebook.tab(tab, text=("▏ " if tab == selected else "  ") + text)


def add_message_bar(parent):
    label = ttk.Label(parent, text="Ready.", style="Message.TLabel", anchor="w")
    label.pack(side="bottom", fill="x", padx=8, pady=(0, 8))
    return label


def show_message(parent, dialog, title, message, **options):
    # Keep the original dialog and return value; mirror its first line below the table.
    style = "Success.Message.TLabel" if dialog == messagebox.showinfo else "Error.Message.TLabel"
    first_line = str(message).split("\n", 1)[0]
    parent.message_label.configure(text=f"{title}: {first_line}", style=style)
    return dialog(title, message, **options)
