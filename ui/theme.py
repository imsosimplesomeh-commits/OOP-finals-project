import tkinter as tk
from tkinter import ttk, font, messagebox


# Light is the default because it is easier to read on a projector.
LIGHT = {
    "background": "#ffffff",     # window behind the panels
    "panel": "#f2f4f7",          # forms, tables and buttons
    "row_alt": "#e3e7ed",        # every second table row
    "field": "#ffffff",          # inside entries and combo boxes
    "line": "#6b7380",           # thin borders
    "hover": "#d9dfe8",          # button or heading under the mouse
    "text": "#111111",
    "muted": "#434a54",          # less important labels
    "accent": "#0b3d91",         # headings and frame borders
    "selected": "#0b3d91",       # selected rows and pressed buttons
    "selected_text": "#ffffff",
    "tab": "#d4e0f4",            # selected sidebar tab
    "danger": "#b00020",         # delete buttons
    "success": "#13652b",
    "error": "#b00020",
}

# Dark keeps the original brass-on-brown look.
DARK = {
    "background": "#110e0b",
    "panel": "#221c16",
    "row_alt": "#27211b",
    "field": "#110e0b",
    "line": "#6e5634",
    "hover": "#342b20",
    "text": "#ece2d0",
    "muted": "#9c8d74",
    "accent": "#b89658",
    "selected": "#b89658",
    "selected_text": "#110e0b",
    "tab": "#203339",
    "danger": "#b07070",
    "success": "#b9dfa5",
    "error": "#e8aaa4",
}

# The PDF is printed on white paper, so its header color never changes.
PDF_HEADER = "#eeeeee"

current = {"name": "light"}


def palette():
    return LIGHT if current["name"] == "light" else DARK


def apply_theme(root):
    # Clam shows the same borders and colors on Windows.
    style = ttk.Style(root)
    style.theme_use("clam")
    font.nametofont("TkDefaultFont").configure(family="Georgia", size=9)
    font.nametofont("TkTextFont").configure(family="Consolas", size=10)
    root.option_add("*TCombobox*Listbox.font", "{Consolas} 9")
    set_layouts(style)
    root.bind("<<NotebookTabChanged>>", highlight_sidebar, add="+")
    paint(root)


def toggle_theme(root):
    current["name"] = "dark" if current["name"] == "light" else "light"
    paint(root)


def paint(root):
    # ttk widgets follow the styles; plain tk widgets are recolored by hand.
    c = palette()
    root.configure(background=c["background"])
    root.option_add("*TCombobox*Listbox.background", c["field"])
    root.option_add("*TCombobox*Listbox.foreground", c["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", c["selected"])
    root.option_add("*TCombobox*Listbox.selectForeground", c["selected_text"])
    set_styles(ttk.Style(root), c)
    recolor_plain_widgets(root)


def set_layouts(style):
    style.layout("TNotebook", [("Notebook.padding", {"sticky": "nswe"})])
    tab_layout = [
        ("Treeheading.cell", {"sticky": "nswe"}),
        ("Treeheading.border", {"side": "bottom", "sticky": "ew"}),
        ("Notebook.padding", {"sticky": "nswe", "children": [
            ("Notebook.label", {"sticky": "w"})
        ]})
    ]
    style.layout("TNotebook.Tab", tab_layout)
    style.layout("Sidebar.TNotebook.Tab", tab_layout)
    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    style.layout("Treeview.Heading", [
        ("Treeheading.cell", {"sticky": "nswe"}),
        ("Treeheading.padding", {"sticky": "nswe", "children": [
            ("Treeheading.image", {"side": "right", "sticky": ""}),
            ("Treeheading.text", {"sticky": "we"})
        ]})
    ])


def set_styles(style, c):
    style.configure(".", background=c["panel"], foreground=c["text"],
                    font=("Georgia", 9), bordercolor=c["line"],
                    lightcolor=c["line"], darkcolor=c["line"], focuscolor=c["accent"])
    style.configure("TFrame", background=c["panel"])
    style.configure("Page.TFrame", background=c["background"])
    style.configure("Banner.TFrame", background=c["background"], bordercolor=c["background"],
                    lightcolor=c["background"], darkcolor=c["background"],
                    borderwidth=0, relief="flat")
    style.configure("TLabel", background=c["panel"], foreground=c["text"])
    style.configure("Page.TLabel", background=c["background"], foreground=c["text"])
    style.configure("Title.TLabel", background=c["background"], foreground=c["accent"],
                    font=("Georgia", 22, "bold"))
    style.configure("Subtitle.TLabel", background=c["background"], foreground=c["muted"],
                    font=("Georgia", 9))
    style.configure("Heading.TLabel", background=c["background"], foreground=c["accent"],
                    font=("Georgia", 10, "bold"))
    style.configure("Status.TLabel", background=c["background"], foreground=c["muted"],
                    font=("Georgia", 9))
    style.configure("Success.Status.TLabel", foreground=c["success"])
    style.configure("Error.Status.TLabel", foreground=c["error"])
    style.configure("TLabelframe", background=c["panel"], bordercolor=c["accent"],
                    lightcolor=c["accent"], darkcolor=c["accent"], relief="solid",
                    borderwidth=1, padding=8)
    style.configure("TLabelframe.Label", background=c["panel"], foreground=c["accent"],
                    font=("Georgia", 10, "bold"))
    style.configure("Form.TFrame", background=c["panel"], bordercolor=c["accent"],
                    lightcolor=c["accent"], darkcolor=c["accent"], borderwidth=1,
                    relief="solid", padding=(8, 28, 8, 8))
    style.configure("FormTitle.TLabel", background=c["panel"], foreground=c["accent"],
                    font=("Georgia", 10, "bold"))

    style.configure("Section.TLabelframe", borderwidth=0, relief="flat",
                    bordercolor=c["panel"], lightcolor=c["panel"], darkcolor=c["panel"])
    style.configure("Message.TLabel", background=c["background"], foreground=c["muted"],
                    font=("Georgia", 9), padding=(8, 8))
    style.configure("Success.Message.TLabel", foreground=c["success"],
                    font=("Georgia", 9, "bold"))
    style.configure("Error.Message.TLabel", foreground=c["error"],
                    font=("Georgia", 9, "bold"))

    style.configure("TNotebook", background=c["background"], borderwidth=0, padding=0,
                    tabmargins=(0, 0, 0, 8))
    style.configure("TNotebook.Tab", background=c["panel"], foreground=c["muted"],
                    borderwidth=1, relief="solid",
                    padding=(16, 12), font=("Georgia", 10, "bold"), width=14, anchor="w")
    style.map("TNotebook.Tab",
              background=[("selected", c["tab"]), ("active", c["panel"])],
              foreground=[("selected", c["accent"]), ("active", c["text"])],
              bordercolor=[("selected", c["accent"]), ("!selected", c["panel"])],
              lightcolor=[("selected", c["accent"]), ("!selected", c["panel"])],
              darkcolor=[("selected", c["accent"]), ("!selected", c["panel"])],
              padding=[("selected", (16, 12)), ("!selected", (16, 12))],
              expand=[("selected", (0, 0, 0, 0)), ("!selected", (0, 0, 0, 0))])
    # Keep the existing notebook events while placing navigation on the left.
    style.configure("Sidebar.TNotebook", background=c["background"], tabposition="wn",
                    tabmargins=(0, 0, 8, 0))
    style.configure("Sidebar.TNotebook.Tab", background=c["background"])
    sidebar_colors = [("selected", c["tab"]), ("active", c["panel"]), ("!selected", c["background"])]
    style.map("Sidebar.TNotebook.Tab", background=sidebar_colors, bordercolor=sidebar_colors,
              lightcolor=sidebar_colors, darkcolor=sidebar_colors)

    style.configure("TButton", background=c["panel"], foreground=c["text"],
                    font=("Georgia", 9, "bold"), padding=(10, 6),
                    bordercolor=c["accent"], lightcolor=c["accent"], darkcolor=c["line"],
                    relief="raised", borderwidth=1)
    style.map("TButton",
              background=[("disabled", c["panel"]), ("pressed", c["selected"]), ("active", c["hover"])],
              foreground=[("disabled", c["muted"]), ("pressed", c["selected_text"])],
              bordercolor=[("focus", c["text"]), ("active", c["accent"])])
    style.configure("Delete.TButton", bordercolor=c["danger"],
                    lightcolor=c["danger"], darkcolor=c["danger"])
    style.map("Delete.TButton",
              bordercolor=[("focus", c["danger"]), ("active", c["danger"])],
              background=[("disabled", c["panel"]), ("pressed", c["danger"]), ("active", c["hover"])])

    for name in ("TEntry", "TCombobox"):
        style.configure(name, fieldbackground=c["field"], background=c["panel"],
                        foreground=c["text"], insertcolor=c["text"],
                        font=("Consolas", 10), padding=(8, 4), bordercolor=c["line"],
                        lightcolor=c["line"], darkcolor=c["line"],
                        selectbackground=c["selected"], selectforeground=c["selected_text"],
                        arrowcolor=c["accent"])
        style.map(name,
                  fieldbackground=[("disabled", c["panel"]), ("readonly", c["field"])],
                  foreground=[("disabled", c["muted"]), ("readonly", c["text"])],
                  selectbackground=[("!disabled", c["selected"])],
                  selectforeground=[("!disabled", c["selected_text"])],
                  bordercolor=[("focus", c["accent"]), ("active", c["accent"])],
                  arrowcolor=[("disabled", c["muted"]), ("active", c["text"])])

    style.configure("Treeview", background=c["panel"], fieldbackground=c["panel"],
                    foreground=c["text"], font=("Consolas", 9), rowheight=28,
                    bordercolor=c["panel"], borderwidth=0, lightcolor=c["panel"],
                    darkcolor=c["panel"], relief="flat")
    style.map("Treeview", background=[("selected", c["selected"])],
              foreground=[("selected", c["selected_text"])])
    style.configure("Treeview.Heading", background=c["panel"], foreground=c["accent"],
                    font=("Georgia", 9, "bold"), padding=(8, 8),
                    bordercolor=c["panel"], lightcolor=c["panel"], darkcolor=c["panel"],
                    borderwidth=0, relief="flat")
    style.map("Treeview.Heading", background=[("active", c["hover"])],
              foreground=[("active", c["text"])])

    for name in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        style.configure(name, background=c["hover"], troughcolor=c["background"],
                        arrowcolor=c["accent"], bordercolor=c["line"], relief="flat", width=14)
        style.map(name, background=[("pressed", c["accent"]), ("active", c["line"])])
    style.configure("TSeparator", background=c["accent"])


def recolor_plain_widgets(widget):
    # Plain tk widgets and table row tags do not follow ttk styles.
    for child in widget.winfo_children():
        if isinstance(child, tk.Text):
            style_text(child)
        elif isinstance(child, tk.Canvas):
            child.configure(background=palette()["background"])
        elif isinstance(child, ttk.Treeview):
            style_table(child)
        elif isinstance(child, ttk.Combobox):
            style_dropdown_list(child)
        recolor_plain_widgets(child)


def style_text(text):
    c = palette()
    text.configure(background=c["panel"], foreground=c["text"], insertbackground=c["text"],
                   selectbackground=c["selected"], selectforeground=c["selected_text"])


def style_table(tree):
    tree.tag_configure("even", background=palette()["panel"])
    tree.tag_configure("odd", background=palette()["row_alt"])


def style_dropdown_list(combo):
    # A dropdown list that was already opened keeps its old colors, so set them here.
    c = palette()
    popdown = combo.tk.call("ttk::combobox::PopdownWindow", combo)
    combo.tk.call(f"{popdown}.f.l", "configure", "-background", c["field"],
                  "-foreground", c["text"], "-selectbackground", c["selected"],
                  "-selectforeground", c["selected_text"])


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
