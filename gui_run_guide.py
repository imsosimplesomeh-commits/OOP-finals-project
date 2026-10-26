# gui_run_guide.py - runs every case in TEST_RUN_GUIDE.md through the real main.py window
# Usage:  python gui_run_guide.py
# It fills the entries, picks the dropdowns and presses the buttons of the real widgets.
# Pop-ups are answered automatically (Yes to every question) and their text is checked.
# It always uses the database Modelo_CSPC103_gui_test, so the demo database is never touched.

import json
import os
import sys

# choose the test database BEFORE importing db.py, because db.py reads the name when it loads
TEST_DB = "Modelo_CSPC103_gui_test"
os.environ["PGDATABASE"] = TEST_DB

import tkinter as tk
from tkinter import ttk, messagebox

import db

if db.DB_CONFIG["dbname"] != TEST_DB:
    sys.exit("Stop: this script empties its database and must only run on " + TEST_DB)

import main

# ---------------------------------------------------------------
# pop-ups: record every dialog and answer it without blocking
# ---------------------------------------------------------------
popups = []  # (kind, title, message)


def _recorder(kind, answer=None):
    def dialog(title=None, message=None, **options):
        popups.append((kind, title, str(message)))
        return answer
    return dialog


messagebox.showinfo = _recorder("info", "ok")
messagebox.showwarning = _recorder("warning", "ok")
messagebox.showerror = _recorder("error", "ok")
messagebox.askyesno = _recorder("ask", True)

results = []  # (test case, passed, detail)
app = None


def check(case, passed, detail=""):
    results.append((case, passed, detail))
    print(("PASS  " if passed else "FAIL  ") + case + ("  " + detail if detail and not passed else ""))


# ---------------------------------------------------------------
# widget helpers
# ---------------------------------------------------------------
def pump():
    for _ in range(3):
        app.update_idletasks()
        app.update()


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def press(container, text):
    # click the one button with this caption inside the container; returns the pop-ups it raised
    buttons = [w for w in descendants(container) if isinstance(w, ttk.Button) and w.cget("text") == text]
    if len(buttons) != 1:
        raise RuntimeError(f"expected one '{text}' button, found {len(buttons)}")
    start = len(popups)
    buttons[0].invoke()
    pump()
    return popups[start:]


def fill(entry, value):
    entry.delete(0, "end")
    entry.insert(0, value)


def pick(combo, value):
    # choose a dropdown item; value may be the full text or a unique part of it
    values = list(combo.cget("values"))
    matches = [v for v in values if v == value] or [v for v in values if value in v]
    if len(matches) != 1:
        raise RuntimeError(f"cannot pick '{value}' from {values}")
    combo.set(matches[0])
    combo.event_generate("<<ComboboxSelected>>")
    pump()
    return matches[0]


def rows(tree):
    return [(item, tree.item(item, "values")) for item in tree.get_children()]


def click_row(tree, match):
    # select the first row whose values satisfy match(values), like a mouse click
    for item, values in rows(tree):
        if match(values):
            tree.selection_set(())
            pump()
            tree.selection_set(item)
            tree.focus(item)
            pump()
            return values
    raise RuntimeError(f"no matching row in {[v for _, v in rows(tree)]}")


def goto_tab(index):
    app.notebook.select(index)
    pump()


def messages(found):
    return " | ".join(f"{kind}:{text}" for kind, _, text in found) or "(no pop-up)"


def said(found, text, kind=None):
    return any(text in message and (kind is None or k == kind) for k, _, message in found)


def expect(case, found, text, kind=None):
    check(case, said(found, text, kind), f"expected '{text}', got {messages(found)}")


# ---------------------------------------------------------------
# shortcuts to the real views
# ---------------------------------------------------------------
def students():
    goto_tab(0)
    app.tab_mgmt.sub_notebook.select(0)
    pump()
    return app.tab_mgmt.student_view


def teachers():
    goto_tab(0)
    app.tab_mgmt.sub_notebook.select(1)
    pump()
    return app.tab_mgmt.teacher_view


def subjects():
    goto_tab(0)
    app.tab_mgmt.sub_notebook.select(2)
    pump()
    return app.tab_mgmt.subject_view


def classes():
    goto_tab(1)
    return app.tab_class


def grades():
    goto_tab(2)
    return app.tab_grading


def reports():
    goto_tab(3)
    return app.tab_reports


def form_student(view, number, first, last, program, year):
    press(view, "Clear")
    fill(view.entries["student_id"], number)
    fill(view.entries["first_name"], first)
    fill(view.entries["last_name"], last)
    fill(view.entries["program"], program)
    fill(view.entries["year_level"], year)


def form_teacher(view, tid, first, last, dept):
    press(view, "Clear")
    fill(view.entries["teacher_id"], tid)
    fill(view.entries["first_name"], first)
    fill(view.entries["last_name"], last)
    fill(view.entries["department"], dept)


def form_subject(view, code, name, units, description=""):
    press(view, "Clear")
    fill(view.entries["subject_code"], code)
    fill(view.entries["subject_name"], name)
    fill(view.entries["units"], units)
    fill(view.entries["description"], description)


def select_class(tab, code):
    tab.cb_teacher_filter.set("All teachers")
    tab.load_classes()
    return click_row(tab.tree_classes, lambda v: v[1] == code)


def save_weights(tab, period, weights):
    # weights = {component name: text typed in its box}
    pick(tab.cb_weight_period, period)
    names = {str(v[0]): v[2] for _, v in rows(tab.tree_comps) if v[0]}
    for component_id, entry in tab.weight_entries.items():
        fill(entry, weights.get(names[str(component_id)], ""))
    return press(tab, "Save Weights")


def weight_boxes(tab):
    names = {str(v[0]): v[2] for _, v in rows(tab.tree_comps) if v[0]}
    return {names[str(cid)]: entry.get() for cid, entry in tab.weight_entries.items()}


COMPONENTS = ["Midterm Quiz", "Midterm Laboratory/Project", "Midterm Examination",
              "Final Quiz", "Final Laboratory/Project", "Final Examination"]


def pick_component(tab, name):
    return pick(tab.cb_comp, f"] {name} (")


def save_score(tab, student, component, score):
    pick(tab.cb_student, student)
    pick_component(tab, component)
    fill(tab.entry_raw_score, score)
    return press(tab, "Save Score")


def grade_rows(tab):
    # student name -> (midterm %, midterm GP, finals %, finals GP, overall %, overall GP, remarks, status)
    return {v[1]: tuple(v[2:]) for _, v in rows(tab.tree_grades)}


def score_rows(tab):
    return {v[2]: v[4] for _, v in rows(tab.tree_student_scores)}


def run_report(tab, kind, choice):
    pick(tab.cb_report_type, kind)
    pick(tab.cb_filter, choice)
    found = press(tab, "View Report")
    return found, tab.txt_preview.get("1.0", "end"), tab.current_report_data


def report_row(data, name):
    for row in data["rows"]:
        if any(name in str(value) for value in row):
            return [str(value) for value in row]
    return []


# ---------------------------------------------------------------
# Part A. Master records and enrollment
# ---------------------------------------------------------------
def part_a():
    v = students()
    found = []
    for data in [("2026-0001", "Juan", "Dela Cruz", "BSCS", "2"),
                 ("2026-0002", "Pedro", "Reyes", "BSCS", "2"),
                 ("2026-0003", "Ana", "Garcia", "BSIT", "2")]:
        form_student(v, *data)
        found += press(v, "Add")
    check("ST-01", sum(said([f], "Student saved.") for f in found) == 3 and len(rows(v.tree)) == 3,
          f"{messages(found)}; rows={len(rows(v.tree))}")

    form_student(v, "2026-0001", "Juan", "Dela Cruz", "BSCS", "2")
    expect("ST-02", press(v, "Add"), "That student number already exists.")

    form_student(v, "2026-0005", "", "Blank", "BSCS", "2")
    first = press(v, "Add")
    form_student(v, "", "No", "Number", "BSCS", "2")
    second = press(v, "Add")
    check("ST-03", said(first, "First name is required.") and said(second, "Student number is required."),
          f"{messages(first)} / {messages(second)}")

    press(v, "Clear")
    fill(v.search_entry, "Reyes")
    press(v, "Search")
    click_row(v.tree, lambda r: r[0] == "2026-0002")
    form = (v.entries["student_id"].get(), v.entries["first_name"].get(), v.entries["last_name"].get())
    check("ST-04", len(rows(v.tree)) == 1 and form == ("2026-0002", "Pedro", "Reyes"),
          f"rows={[r for _, r in rows(v.tree)]}, form={form}")

    press(v, "View All")
    click_row(v.tree, lambda r: r[0] == "2026-0003")
    keys = ("student_id", "first_name", "last_name", "program", "year_level", "status")
    before = tuple(v.entries[k].get() for k in keys)
    fill(v.entries["program"], "BSCS")
    found = press(v, "Update")
    press(v, "View All")
    click_row(v.tree, lambda r: r[0] == "2026-0003")
    form = tuple(v.entries[k].get() for k in keys)
    check("ST-05", said(found, "Student saved.") and before[3] == "BSIT"
          and form == before[:3] + ("BSCS",) + before[4:], f"{messages(found)}; before={before}; after={form}")

    form_student(v, "2026-0099", "Lea", "Ramos", "BSIT", "1")
    press(v, "Add")
    click_row(v.tree, lambda r: r[0] == "2026-0099")
    found = press(v, "Delete")
    check("ST-06", said(found, "Delete this student?", "ask") and said(found, "Student deleted.")
          and not any(r[0] == "2026-0099" for _, r in rows(v.tree)), messages(found))

    t = teachers()
    form_teacher(t, "T-1001", "Maria", "Santos", "Computer Studies Department")
    expect("TE-01", press(t, "Add"), "Teacher saved.")

    form_teacher(t, "T-1001", "Maria", "Santos", "Computer Studies Department")
    first = press(t, "Add")
    form_teacher(t, "T-1009", "", "Nobody", "Computer Studies Department")
    second = press(t, "Add")
    check("TE-02", said(first, "That teacher ID already exists.") and said(second, "First name is required."),
          f"{messages(first)} / {messages(second)}")

    press(t, "View")
    click_row(t.tree, lambda r: r[0] == "T-1001")
    form = tuple(t.entries[k].get() for k in ("teacher_id", "first_name", "last_name", "department"))
    check("TE-03", form == ("T-1001", "Maria", "Santos", "Computer Studies Department"), f"form={form}")

    fill(t.entries["department"], "Information Technology Department")
    found = press(t, "Update")
    shown = [r for _, r in rows(t.tree) if r[0] == "T-1001"]
    check("TE-04", said(found, "Teacher saved.") and shown and shown[0][4] == "Information Technology Department",
          f"{messages(found)}; row={shown}")

    s = subjects()
    form_subject(s, "CSPC 103", "Object Oriented Programming", "3")
    expect("SU-01", press(s, "Add"), "Subject saved.")

    form_subject(s, "CSPC 103", "Object Oriented Programming", "3")
    dup = press(s, "Add")
    form_subject(s, "ZERO 1", "Zero units", "0")
    zero = press(s, "Add")
    form_subject(s, "NEG 1", "Negative units", "-2")
    neg = press(s, "Add")
    check("SU-02", said(dup, "That subject code already exists.")
          and said(zero, "Units must be a positive whole number.")
          and said(neg, "Units must be a positive whole number."),
          f"{messages(dup)} / {messages(zero)} / {messages(neg)}")

    press(s, "View")
    shown = [r for _, r in rows(s.tree) if r[1] == "CSPC 103"]
    check("SU-03", len(shown) == 1 and shown[0][2] == "Object Oriented Programming" and shown[0][3] == "3",
          f"rows={[r for _, r in rows(s.tree)]}")

    click_row(s.tree, lambda r: r[1] == "CSPC 103")
    description = "Object-oriented analysis, design and programming in Java"
    fill(s.entries["description"], description)
    found = press(s, "Update")
    shown = [r for _, r in rows(s.tree) if r[1] == "CSPC 103"]
    check("SU-04", said(found, "Subject saved.") and shown and shown[0][4] == description,
          f"{messages(found)}; row={shown}")

    form_subject(s, "TMP 101", "Temporary", "1")
    added = press(s, "Add")
    click_row(s.tree, lambda r: r[1] == "TMP 101")
    found = press(s, "Delete")
    check("SU-05 (part 1)", said(added, "Subject saved.") and said(found, "Subject deleted.")
          and not any(r[1] == "TMP 101" for _, r in rows(s.tree)), f"{messages(added)} / {messages(found)}")

    c = classes()
    press(c, "Clear")
    fill(c.entry_code, "CSPC103-A")
    pick(c.cb_subject, "CSPC 103")
    pick(c.cb_teacher, "Santos")
    fill(c.entry_section, "A")
    fill(c.entry_schedule, "MWF 9:00-10:00")
    fill(c.entry_room, "CS-201")
    fill(c.entry_sy, "2026-2027")
    pick(c.cb_semester, "1st")
    expect("CL-01", press(c, "Add Class"), "Class saved.")

    t = teachers()
    press(t, "View")
    click_row(t.tree, lambda r: r[0] == "T-1001")
    expect("TE-05", press(t, "Delete"), "Cannot delete this teacher because class CSPC103-A depends on it.")

    s = subjects()
    click_row(s.tree, lambda r: r[1] == "CSPC 103")
    found = press(s, "Delete")
    check("SU-05 (part 2)", said(found, "CSPC103-A", "warning") and not said(found, "Subject deleted."), messages(found))

    c = classes()
    out = []
    for missing in ("teacher", "subject", "school year"):
        press(c, "Clear")
        fill(c.entry_code, "CSPC103-B")
        if missing != "subject":
            pick(c.cb_subject, "CSPC 103")
        if missing != "teacher":
            pick(c.cb_teacher, "Santos")
        fill(c.entry_section, "B")
        fill(c.entry_sy, "" if missing == "school year" else "2026-2027")
        out.append(press(c, "Add Class"))
    fill(c.entry_sy, "2026-2027")
    press(c, "Clear")
    check("CL-02", all(said(f, "is required.", "warning") for f in out)
          and said(out[0], "Teacher") and said(out[1], "Subject") and said(out[2], "School year"),
          " / ".join(messages(f) for f in out))

    pick(c.cb_teacher_filter, "Santos")
    shown = [r for _, r in rows(c.tree_classes)]
    ok = (len(shown) == 1 and shown[0][1] == "CSPC103-A" and shown[0][2] == "Object Oriented Programming"
          and shown[0][4] == "A" and shown[0][5] == "MWF 9:00-10:00" and shown[0][6] == "CS-201"
          and shown[0][7] == "1st 2026-2027")
    pick(c.cb_teacher_filter, "All teachers")
    check("CL-03", ok and len(rows(c.tree_classes)) == 1, f"filtered={shown}")

    select_class(c, "CSPC103-A")
    fill(c.entry_room, "CS-202")
    fill(c.entry_schedule, "TTh 1:00-2:30")
    found = press(c, "Update Class")
    press(c, "Clear")
    select_class(c, "CSPC103-A")
    check("CL-04", said(found, "Class saved.") and c.entry_room.get() == "CS-202"
          and c.entry_schedule.get() == "TTh 1:00-2:30", f"{messages(found)}; room={c.entry_room.get()}, schedule={c.entry_schedule.get()}")

    select_class(c, "CSPC103-A")
    found = []
    for number in ("2026-0001", "2026-0002", "2026-0003"):
        pick(c.cb_enroll_student, number)
        found += press(c, "Enroll Student")
    check("EN-01", sum(said([f], "Successfully enrolled") for f in found) == 3, messages(found))

    v = students()
    press(v, "View All")
    click_row(v.tree, lambda r: r[0] == "2026-0001")
    expect("ST-07", press(v, "Delete"), "Cannot delete this student because enrollments depend on it.")

    c = classes()
    select_class(c, "CSPC103-A")
    expect("CL-05", press(c, "Delete Class"), "Cannot delete this class because enrollments depend on it.")

    select_class(c, "CSPC103-A")
    pick(c.cb_enroll_student, "2026-0001")
    expect("EN-02", press(c, "Enroll Student"), "is already enrolled in CSPC103-A.")

    c.cb_enroll_student.set("2026-9999")
    expect("EN-03", press(c, "Enroll Student"), "Student with ID '2026-9999' does not exist.")

    select_class(c, "CSPC103-A")
    shown = {r[1]: r[5] for _, r in rows(c.tree_enrollments)}
    check("EN-04", set(shown) == {"2026-0001", "2026-0002", "2026-0003"} and all(shown.values()), f"rows={shown}")

    click_row(c.tree_enrollments, lambda r: r[1] == "2026-0002")
    dropped = press(c, "Drop Selected")
    status_after_drop = [r[5] for _, r in rows(c.tree_enrollments) if r[1] == "2026-0002"]
    click_row(c.tree_enrollments, lambda r: r[1] == "2026-0002")
    restored = press(c, "Restore")
    status_after_restore = [r[5] for _, r in rows(c.tree_enrollments) if r[1] == "2026-0002"]
    check("EN-05", said(dropped, "Enrollment status set to Dropped.") and said(restored, "Enrollment status set to Enrolled.")
          and status_after_drop == ["Dropped"] and status_after_restore == ["Enrolled"],
          f"{messages(dropped)} / {messages(restored)}; {status_after_drop} {status_after_restore}")

    v = students()
    form_student(v, "2026-0098", "Carlo", "Mendoza", "BSIT", "1")
    added = press(v, "Add")
    c = classes()
    select_class(c, "CSPC103-A")
    pick(c.cb_enroll_student, "2026-0098")
    enrolled = press(c, "Enroll Student")
    click_row(c.tree_enrollments, lambda r: r[1] == "2026-0098")
    found = press(c, "Remove")
    check("EN-06 (part 1)", said(added, "Student saved.") and said(enrolled, "Successfully enrolled")
          and said(found, "Enrollment removed.") and not any(r[1] == "2026-0098" for _, r in rows(c.tree_enrollments)),
          f"{messages(added)} / {messages(enrolled)} / {messages(found)}")


# ---------------------------------------------------------------
# Part B. Grading, reports, persistence
# ---------------------------------------------------------------
SCORES = {
    "Juan": ["40", "90", "57", "45", "85", "80"],
    "Pedro": ["20", "60", "55", "30", "70", "65"],
    "Ana": ["50", "100", "100", "48", "95", "92"],
}


def part_b():
    c = classes()
    found = []
    for name, order in (("Midterm", "1"), ("Finals", "2")):
        fill(c.entry_period_name, name)
        fill(c.entry_period_order, order)
        found += press(c, "Add Period")
    check("GP-01", sum(said([f], "Grading period added.") for f in found) == 2, messages(found))

    found = []
    for name, period, category, max_score in (
            ("Midterm Quiz", "Midterm", "Quiz", "50"), ("Midterm Laboratory/Project", "Midterm", "Laboratory", "100"),
            ("Midterm Examination", "Midterm", "Exam", "100"), ("Final Quiz", "Finals", "Quiz", "50"),
            ("Final Laboratory/Project", "Finals", "Laboratory", "100"), ("Final Examination", "Finals", "Exam", "100")):
        pick(c.cb_period, period)
        pick(c.cb_comp_weight, category)
        fill(c.entry_comp_name, name)
        fill(c.entry_comp_max, max_score)
        found += press(c, "Add Component")
    comp_rows = [r for _, r in rows(c.tree_comps) if r[0]]
    check("GC-01", sum(said([f], "Component added.") for f in found) == 6 and len(comp_rows) == 6
          and [r[2] for r in comp_rows] == COMPONENTS and all(r[5] == "-" for r in comp_rows),
          f"{messages(found)}; rows={comp_rows}")

    select_class(c, "CSPC103-A")
    mid = save_weights(c, "Midterm", {"Midterm Quiz": "20", "Midterm Laboratory/Project": "30", "Midterm Examination": "50"})
    fin = save_weights(c, "Finals", {"Final Quiz": "20", "Final Laboratory/Project": "30", "Final Examination": "50"})
    table = {r[2]: r[5] for _, r in rows(c.tree_comps)}
    check("GW-01", said(mid, "Period weights saved.") and said(fin, "Period weights saved.")
          and [table[n] for n in COMPONENTS] == ["20.00", "30.00", "50.00"] * 2
          and table.get("Midterm total") == "100.00%" and table.get("Finals total") == "100.00%",
          f"{messages(mid)} / {messages(fin)}; table={table}")

    found = save_weights(c, "Midterm", {"Midterm Quiz": "20", "Midterm Laboratory/Project": "30", "Midterm Examination": "40"})
    boxes = weight_boxes(c)
    check("GW-02", said(found, "Weights total 90%, they must total 100%.")
          and boxes == {"Midterm Quiz": "20.00", "Midterm Laboratory/Project": "30.00", "Midterm Examination": "50.00"},
          f"{messages(found)}; boxes={boxes}")

    negative = save_weights(c, "Midterm", {"Midterm Quiz": "-20", "Midterm Laboratory/Project": "30", "Midterm Examination": "50"})
    blank = save_weights(c, "Midterm", {"Midterm Quiz": "", "Midterm Laboratory/Project": "30", "Midterm Examination": "50"})
    check("GW-03", said(negative, "Weight cannot be negative.") and said(blank, "Enter a number for weight."),
          f"{messages(negative)} / {messages(blank)}")

    select_class(c, "CSPC103-A")
    headings = [c.tree_comps.heading(col, "text") for col in ("period", "name", "max_score", "weight")]
    table = {r[2]: r for _, r in rows(c.tree_comps)}
    check("GC-02", headings == ["Period", "Component", "Max Score", "Weight (%)"]
          and "Midterm total" in table and "Finals total" in table and table["Midterm Quiz"][4] == "50",
          f"headings={headings}; rows={list(table.values())}")

    g = grades()
    pick(g.cb_class, "CSPC103-A")
    shown_label = pick_component(g, "Midterm Quiz")
    found = []
    for student, values in SCORES.items():
        for component, value in zip(COMPONENTS, values):
            found += save_score(g, student, component, value)
    check("SC-01", sum(said([f], "Score saved.") for f in found) == 18 and "Midterm Quiz (/50 - 20%)" in shown_label,
          f"{len(found)} pop-ups, saved={sum(said([f], 'Score saved.') for f in found)}, label={shown_label}; "
          + messages([f for f in found if not said([f], 'Score saved.')]))

    c = classes()
    select_class(c, "CSPC103-A")
    click_row(c.tree_comps, lambda r: r[2] == "Midterm Quiz")
    expect("GC-03", press(c, "Delete Component"), "Cannot delete Midterm Quiz because 3 score(s) depend on it.")

    select_class(c, "CSPC103-A")
    click_row(c.tree_enrollments, lambda r: r[1] == "2026-0001")
    expect("EN-06 (part 2)", press(c, "Remove"), "Cannot remove this enrollment because scores depend on it.")

    g = grades()
    pick(g.cb_class, "CSPC103-A")
    expect("SC-02", save_score(g, "Pedro", "Midterm Quiz", "55"), "Score 55 is above the maximum of 50.")
    expect("SC-03", save_score(g, "Pedro", "Final Examination", "-5"), "Score cannot be negative.")

    g.cb_student.set("2026-0098")
    pick_component(g, "Midterm Quiz")
    fill(g.entry_raw_score, "10")
    expect("SC-04", press(g, "Save Score"), "'2026-0098' is not enrolled in this class, so no score can be saved.")

    classes()
    g = grades()
    pick(g.cb_class, "CSPC103-A")
    problems = []
    for student, values in SCORES.items():
        pick(g.cb_student, student)
        shown = score_rows(g)
        wanted = {n: f"{float(x):.2f}" for n, x in zip(COMPONENTS, values)}
        if shown != wanted:
            problems.append(f"{student}: {shown}")
    check("SC-05", not problems, "; ".join(problems))

    pick(g.cb_student, "Juan")
    click_row(g.tree_student_scores, lambda r: r[2] == "Midterm Examination")
    picked = g.cb_comp.get()
    fill(g.entry_raw_score, "75")
    found = press(g, "Save Score")
    shown = score_rows(g)
    check("SC-06", said(found, "Score saved.") and "Midterm Examination" in picked and len(shown) == 6
          and shown.get("Midterm Examination") == "75.00", f"{messages(found)}; picked={picked}; rows={shown}")

    found = press(g, "Compute All")
    table = grade_rows(g)
    juan, pedro, ana = (next((v for k, v in table.items() if n in k), None) for n in ("Juan", "Pedro", "Ana"))
    ok = juan and pedro and ana
    check("GR-01", bool(ok) and [juan[:2], pedro[:2], ana[:2]] == [("80.50", "2.50"), ("53.50", "5.00"), ("100.00", "1.00")],
          f"{messages(found)}; table={table}")
    check("GR-02", bool(ok) and [juan[2:], pedro[2:], ana[2:]] == [
        ("83.50", "2.25", "82.30", "2.25", "Passed", "Complete"),
        ("65.50", "5.00", "60.70", "5.00", "Failed", "Complete"),
        ("93.70", "1.50", "96.22", "1.25", "Passed", "Complete")], f"table={table}")

    pick(g.cb_student, "Ana")
    click_row(g.tree_student_scores, lambda r: r[2] == "Final Quiz")
    deleted = press(g, "Delete")
    ana_after_delete = next((v for k, v in grade_rows(g).items() if "Ana" in k), None)
    readded = save_score(g, "Ana", "Final Quiz", "48")
    ana_after_save = next((v for k, v in grade_rows(g).items() if "Ana" in k), None)
    check("SC-07", said(deleted, "Delete this score?", "ask") and said(deleted, "Score deleted.") and said(readded, "Score saved.")
          and ana_after_delete is not None and ana_after_delete[2] == "Incomplete" and ana_after_delete[7] == "Midterm only"
          and ana_after_save is not None and ana_after_save[2] == "93.70" and ana_after_save[7] == "Complete",
          f"{messages(deleted)} / {messages(readded)}; after delete={ana_after_delete}; after save={ana_after_save}")

    c = classes()
    select_class(c, "CSPC103-A")
    saved = save_weights(c, "Midterm", {"Midterm Quiz": "30", "Midterm Laboratory/Project": "30", "Midterm Examination": "40"})
    g = grades()
    pick(g.cb_class, "CSPC103-A")
    computed = press(g, "Compute All")
    table = grade_rows(g)
    got = {n: next(((v[0], v[4]) for k, v in table.items() if n in k), None) for n in ("Juan", "Pedro", "Ana")}
    check("GR-03", said(saved, "Period weights saved.") and got == {
        "Juan": ("81.00", "82.50"), "Pedro": ("52.00", "60.10"), "Ana": ("100.00", "96.22")},
        f"{messages(saved)} / {messages(computed)}; got={got}")

    goto_tab(4)
    press(app.tab_audit, "Refresh")
    log = [r for _, r in rows(app.tab_audit.tree)]
    ids = [int(r[0]) for r in log]
    newest_first = ids == sorted(ids, reverse=True)

    def as_json(text):
        try:
            return json.loads(text) if text else {}
        except ValueError:
            return {}
    score_change = any(r[1] == "GRADE_COMPONENT_SCORE" and r[3] == "UPDATE"
                       and float(as_json(r[4]).get("score", -1)) == 57 and float(as_json(r[5]).get("score", -1)) == 75 for r in log)
    grade_update = any(r[1] == "GRADE" and r[3] == "UPDATE" for r in log)
    weight_update = any(r[1] == "GRADE_PERCENTAGE" and r[3] == "UPDATE" for r in log)
    who_when = all(r[6] and r[7] for r in log)
    check("GR-04", bool(log) and newest_first and score_change and grade_update and weight_update and who_when,
          f"entries={len(log)} newest_first={newest_first} score57to75={score_change} grade={grade_update} "
          f"weight={weight_update} who_when={who_when}; top={log[:3]}")

    r = reports()
    found, text, data = run_report(r, "Class List", "CSPC103-A")
    names = [row for row in (data or {}).get("rows", [])]
    order = [n for n in ("Dela Cruz", "Garcia", "Reyes") if any(n in " ".join(map(str, row)) for row in names)]
    positions = [text.find(n) for n in ("Dela Cruz", "Garcia", "Reyes")]
    check("RP-01", "Information Technology Department" in text and "TTh 1:00-2:30" in text and "CS-202" in text
          and order == ["Dela Cruz", "Garcia", "Reyes"] and len(names) == 3 and positions == sorted(positions) and -1 not in positions,
          f"{messages(found)}; text=\n{text}")

    found, text, data = run_report(r, "Grade Sheet", "CSPC103-A")
    rp02 = {}
    for n in ("Dela Cruz", "Garcia", "Reyes"):
        rp02[n] = report_row(data or {"rows": []}, n)
    wanted = {"Dela Cruz": ("2.50", "2.25"), "Garcia": ("1.00", "1.25"), "Reyes": ("5.00", "5.00")}
    ok = all(row and wanted[n][0] in row and wanted[n][1] in row and row.index(wanted[n][0]) < len(row) - 1
             for n, row in rp02.items())
    check("RP-02", ok, f"{messages(found)}; rows={rp02}")
    return rp02


def setup_pathfit():
    t = teachers()
    form_teacher(t, "T-1002", "Jose", "Ramos", "Physical Education Department")
    out = [press(t, "Add")]
    s = subjects()
    form_subject(s, "PATHFIT 3", "Physical Activity Towards Health and Fitness 3", "2")
    out.append(press(s, "Add"))
    c = classes()
    press(c, "Clear")
    fill(c.entry_code, "PATHFIT3-A")
    pick(c.cb_subject, "PATHFIT 3")
    pick(c.cb_teacher, "Ramos")
    fill(c.entry_section, "A")
    fill(c.entry_schedule, "TTh 3:00-5:00")
    fill(c.entry_room, "Gym")
    fill(c.entry_sy, "2026-2027")
    pick(c.cb_semester, "1st")
    out.append(press(c, "Add Class"))
    select_class(c, "PATHFIT3-A")
    pick(c.cb_enroll_student, "2026-0001")
    out.append(press(c, "Enroll Student"))
    out.append(save_weights(c, "Midterm", {"Midterm Quiz": "20", "Midterm Laboratory/Project": "30", "Midterm Examination": "50"}))
    out.append(save_weights(c, "Finals", {"Final Quiz": "20", "Final Laboratory/Project": "30", "Final Examination": "50"}))
    g = grades()
    pick(g.cb_class, "PATHFIT3-A")
    for component, value in zip(COMPONENTS, ["45", "90", "90", "45", "90", "90"]):
        out.append(save_score(g, "Juan", component, value))
    out.append(press(g, "Compute All"))
    juan = next((v for k, v in grade_rows(g).items() if "Juan" in k), None)
    bad = [f for f in out if not f or any(kind != "info" for kind, _, _ in f)]
    check("Setup", not bad and juan is not None and juan[4] == "90.00" and juan[5] == "1.75" and juan[6] == "Passed",
          f"bad pop-ups={[messages(f) for f in bad]}; juan={juan}")


def part_reports_tail():
    r = reports()
    found, text, data = run_report(r, "Student Grade Report", "2026-0001")
    cspc = report_row(data or {"rows": []}, "CSPC 103")
    pathfit = report_row(data or {"rows": []}, "PATHFIT 3")
    check("RP-03", cspc and "3" in cspc and "2.25" in cspc and pathfit and "2" in pathfit and "1.75" in pathfit,
          f"{messages(found)}; CSPC={cspc}; PATHFIT={pathfit}")
    summary = " ".join((data or {}).get("summary", []))
    check("RP-04", "Total Units" in summary and "5" in summary and "No. of Subjects" in summary
          and "2" in summary and "Grade Weighted Average: 2.05" in summary, f"summary={summary!r}")

    v = students()
    form_student(v, "2026-0004", "Kevin", "O'Brien", "BSIT", "1")
    added = press(v, "Add")
    press(v, "Clear")
    fill(v.search_entry, "' OR '1'='1")
    searched = press(v, "Search")
    check("PS-02", said(added, "Student saved.") and not searched and len(rows(v.tree)) == 0,
          f"{messages(added)} / {messages(searched)}; rows={len(rows(v.tree))}")
    fill(v.search_entry, "")
    press(v, "View All")


def main_run():
    global app
    app = main.StudentGradeManagementApp()
    pump()
    if TEST_DB not in app.lbl_status.cget("text"):
        sys.exit("Stop: the window is not connected to " + TEST_DB)
    # Before you start: Reset Database, answer Yes
    found = press(app, "Reset Database")
    if not said(found, "All project tables are empty."):
        sys.exit("Stop: reset failed: " + messages(found))

    part_a()
    rp02 = part_b()
    setup_pathfit()
    part_reports_tail()

    # PS-01: close the app, open it again, check the Grade Sheet
    app.destroy()
    app = main.StudentGradeManagementApp()
    pump()
    r = reports()
    found, text, data = run_report(r, "Grade Sheet", "CSPC103-A")
    again = {n: report_row(data or {"rows": []}, n) for n in rp02}
    check("PS-01", again == rp02 and all(again.values()), f"before={rp02}; after={again}")
    app.destroy()

    failed = [case for case, passed, _ in results if not passed]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed" + (": " + ", ".join(failed) if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main_run())
