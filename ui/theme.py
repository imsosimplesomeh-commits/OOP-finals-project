from tkinter import ttk, font


VOID = "#1B1713"
PANEL = "#27211B"
LINE = "#75603B"
NAVY = "#203349"
HOVER = "#3B3024"
ROW_ALT = "#30281F"
BRASS = "#C5A268"
PARCHMENT = "#E8DCC2"
MUTED = "#BFB096"


def apply_theme(root):
    # clam lets the same colors show on windows too
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(background=VOID)

    font.nametofont("TkDefaultFont").configure(family="Consolas", size=9)
    font.nametofont("TkTextFont").configure(family="Consolas", size=9)
    root.option_add("*TCombobox*Listbox.background", PANEL)
    root.option_add("*TCombobox*Listbox.foreground", PARCHMENT)
    root.option_add("*TCombobox*Listbox.selectBackground", BRASS)
    root.option_add("*TCombobox*Listbox.selectForeground", VOID)
    root.option_add("*TCombobox*Listbox.font", "{Consolas} 9")

    style.configure(".", background=PANEL, foreground=PARCHMENT,
                    font=("Consolas", 9), bordercolor=LINE,
                    lightcolor=LINE, darkcolor=LINE, focuscolor=BRASS)
    style.configure("TFrame", background=PANEL)
    style.configure("Header.TFrame", background=VOID)
    style.configure("TLabel", background=PANEL, foreground=PARCHMENT)
    style.configure("Title.TLabel", background=VOID, foreground=BRASS,
                    font=("Georgia", 17, "bold"))
    style.configure("Subtitle.TLabel", background=VOID, foreground=MUTED,
                    font=("Georgia", 9, "italic"))
    style.configure("Status.TLabel", foreground=MUTED, font=("Consolas", 9))
    style.configure("TLabelframe", bordercolor=BRASS, relief="solid",
                    borderwidth=1, padding=(4, 4))
    style.configure("TLabelframe.Label", background=PANEL, foreground=BRASS,
                    font=("Georgia", 10, "bold"))

    style.configure("TNotebook", background=VOID, borderwidth=0,
                    tabmargins=(0, 4, 0, 0))
    style.configure("TNotebook.Tab", background=PANEL, foreground=MUTED,
                    padding=(12, 7), font=("Georgia", 9, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", NAVY), ("active", HOVER)],
              foreground=[("selected", PARCHMENT), ("active", PARCHMENT)],
              bordercolor=[("selected", BRASS)])

    style.configure("TButton", background=PANEL, foreground=PARCHMENT,
                    font=("Georgia", 9, "bold"), padding=(9, 5),
                    bordercolor=BRASS, lightcolor=BRASS, darkcolor=BRASS,
                    relief="solid", borderwidth=1)
    style.map("TButton",
              background=[("disabled", PANEL), ("pressed", BRASS),
                          ("active", HOVER)],
              foreground=[("disabled", MUTED), ("pressed", VOID)],
              bordercolor=[("focus", PARCHMENT), ("active", BRASS)])

    for name in ("TEntry", "TCombobox"):
        style.configure(name, fieldbackground=VOID, foreground=PARCHMENT,
                        insertcolor=PARCHMENT, padding=4, bordercolor=LINE,
                        selectbackground=BRASS, selectforeground=VOID,
                        arrowcolor=BRASS)
        style.map(name,
                  fieldbackground=[("disabled", PANEL), ("readonly", VOID)],
                  foreground=[("disabled", MUTED), ("readonly", PARCHMENT)],
                  selectbackground=[("!disabled", BRASS)],
                  selectforeground=[("!disabled", VOID)],
                  bordercolor=[("focus", BRASS), ("active", BRASS)],
                  arrowcolor=[("disabled", MUTED), ("active", PARCHMENT)])

    style.configure("Treeview", background=VOID, fieldbackground=VOID,
                    foreground=PARCHMENT, font=("Consolas", 9),
                    rowheight=27, bordercolor=LINE, borderwidth=1,
                    lightcolor=LINE, darkcolor=LINE)
    style.map("Treeview", background=[("selected", BRASS)],
              foreground=[("selected", VOID)])
    style.configure("Treeview.Heading", background=NAVY, foreground=PARCHMENT,
                    font=("Georgia", 9, "bold"), padding=(6, 6),
                    bordercolor=LINE, relief="flat")
    style.map("Treeview.Heading", background=[("active", NAVY)],
              foreground=[("active", PARCHMENT)])

    for name in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        style.configure(name, background=HOVER, troughcolor=VOID,
                        arrowcolor=PARCHMENT, bordercolor=LINE,
                        relief="flat", width=14)
        style.map(name, background=[("pressed", BRASS), ("active", HOVER)])
    style.configure("TSeparator", background=BRASS)


def style_table(tree):
    tree.tag_configure("even", background=VOID)
    tree.tag_configure("odd", background=ROW_ALT)
