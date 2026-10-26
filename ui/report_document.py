from xml.sax.saxutils import escape

from ui.theme import PDF_HEADER


def report_text(data):
    widths = [len(column) for column in data["columns"]]
    for row in data["rows"]:
        widths = [max(width, len(str(value))) for width, value in zip(widths, row)]
    lines = [data["title"], *data["header"], ""]
    for row in [data["columns"], *data["rows"]]:
        lines.append("  ".join(str(value).ljust(width) for value, width in zip(row, widths)))
    return "\n".join([*lines, "", *data["summary"]])


def export_pdf(data, path):
    # import here so the rest of the app can open before dependencies are installed
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    doc = SimpleDocTemplate(str(path), pagesize=landscape(A4),
                            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    cell_style = styles["BodyText"]
    cell_style.fontSize = 9
    cell_style.leading = 12
    story = [Paragraph(escape(data["title"]), styles["Title"])]
    for line in data["header"]:
        story.append(Paragraph(escape(line), styles["Normal"]))
    story.append(Spacer(1, 16))
    cells = [[Paragraph(escape(str(value)), cell_style) for value in row]
             for row in [data["columns"], *data["rows"]]]
    if len(data["columns"]) == 6:
        ratios = [0.05, 0.14, 0.38, 0.22, 0.08, 0.13]
    elif len(data["columns"]) == 5:
        ratios = [0.06, 0.46, 0.20, 0.14, 0.14]
    else:
        ratios = [0.08, 0.62, 0.30]
    table = Table(cells, colWidths=[doc.width * ratio for ratio in ratios], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PDF_HEADER)),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([table, Spacer(1, 16)])
    for line in data["summary"]:
        story.append(Paragraph(escape(line), styles["Normal"]))
    doc.build(story)
