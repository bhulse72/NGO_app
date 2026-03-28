from flask import Blueprint, request, jsonify, render_template, send_file
from app.services.sheets_service import load_all_contacts, load_all_clients
from datetime import datetime, timedelta
import io
import csv
from collections import defaultdict

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def filter_by_period(items, period, date_attr):
    now = datetime.now()
    if period == "week":
        cutoff = now - timedelta(weeks=1)
    elif period == "month":
        cutoff = now - timedelta(days=30)
    elif period == "year":
        cutoff = now - timedelta(days=365)
    else:
        return items
    return [i for i in items if getattr(i, date_attr) and getattr(i, date_attr) >= cutoff]


@reports_bp.route("/sources", methods=["GET"])
def sources_report():
    period = request.args.get("period", "month")
    contacts = load_all_contacts()
    clients = load_all_clients()

    filtered_contacts = filter_by_period(contacts, period, "referral_date")
    filtered_clients = filter_by_period(clients, period, "referral_date")

    # Group by source
    contact_by_source = defaultdict(list)
    for c in filtered_contacts:
        contact_by_source[c.referral_source or "Unknown"].append(c)

    client_by_source = defaultdict(list)
    for c in filtered_clients:
        client_by_source[c.referral_source or "Unknown"].append(c)

    all_sources = sorted(set(list(contact_by_source.keys()) + list(client_by_source.keys())))

    # Build summary rows
    rows = []
    for source in all_sources:
        rows.append({
            "source": source,
            "contacts": len(contact_by_source.get(source, [])),
            "clients": len(client_by_source.get(source, [])),
        })

    if request.args.get("format") == "pdf":
        return generate_sources_pdf(rows, period)

    return render_template("reports/sources.html", rows=rows, period=period, total_contacts=len(filtered_contacts), total_clients=len(filtered_clients))

@reports_bp.route("/hours", methods=["GET"])
def hours_report():
    from app.services.sheets_service import load_all_social_workers
    period = request.args.get("period", "month")
    workers = load_all_social_workers()

    # Filter logs by period
    all_logs = []
    for worker in workers:
        filtered = filter_by_period(worker.time_logs, period, "date")
        for log in filtered:
            all_logs.append({
                "worker_id": log.worker_id,
                "worker_name": worker.name,
                "hours": log.hours,
                "categories": log.categories,
                "description": log.description,
                "date": log.date
            })

   # Aggregate by category
    category_totals = defaultdict(float)
    for log in all_logs:
        for cat in log["categories"]:
            category_totals[cat] += log["hours"]

    # Aggregate by worker
    worker_totals = defaultdict(float)
    for log in all_logs:
        worker_totals[log["worker_name"]] += log["hours"]

    total_hours = sum(category_totals.values())

    if request.args.get("format") == "pdf":
        return generate_hours_pdf(category_totals, worker_totals, total_hours, period)

    return render_template(
        "reports/hours.html",
        category_totals=dict(sorted(category_totals.items(), key=lambda x: x[1], reverse=True)),
        worker_totals=dict(sorted(worker_totals.items(), key=lambda x: x[1], reverse=True)),
        total_hours=total_hours,
        period=period,
        log_count=len(all_logs)
    )


def generate_hours_pdf(category_totals, worker_totals, total_hours, period):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=18, spaceAfter=4)
    sub_style = ParagraphStyle("sub", parent=styles["Normal"], fontSize=10, textColor=colors.gray, spaceAfter=20)
    elements.append(Paragraph("Hours by Category", title_style))
    elements.append(Paragraph(f"Period: {period.capitalize()} · Generated {datetime.now().strftime('%B %d, %Y')}", sub_style))
    elements.append(Spacer(1, 0.2*inch))

    # Category table
    elements.append(Paragraph("By Category", styles["Heading2"]))
    elements.append(Spacer(1, 0.1*inch))
    cat_data = [["Category", "Hours", "% of Total"]]
    for cat, hrs in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        pct = f"{(hrs / total_hours * 100):.1f}%" if total_hours else "0%"
        cat_data.append([cat, f"{hrs:.1f}h", pct])
    cat_data.append(["TOTAL", f"{total_hours:.1f}h", "100%"])

    cat_table = Table(cat_data, colWidths=[3.5*inch, 1.5*inch, 1.5*inch])
    cat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f5f2ee")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e07b39")),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e0d8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e0d8")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(cat_table)
    elements.append(Spacer(1, 0.3*inch))

    # Worker table
    elements.append(Paragraph("By Worker", styles["Heading2"]))
    elements.append(Spacer(1, 0.1*inch))
    worker_data = [["Worker", "Hours"]]
    for worker, hrs in sorted(worker_totals.items(), key=lambda x: x[1], reverse=True):
        worker_data.append([worker, f"{hrs:.1f}h"])

    worker_table = Table(worker_data, colWidths=[4*inch, 2.5*inch])
    worker_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f2ee")]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e0d8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e0d8")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(worker_table)

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=f"hours_report_{period}.pdf")

def generate_sources_pdf(rows, period):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=18, spaceAfter=4)
    sub_style = ParagraphStyle("sub", parent=styles["Normal"], fontSize=10, textColor=colors.gray, spaceAfter=20)
    elements.append(Paragraph("Contacts & Clients by Source", title_style))
    elements.append(Paragraph(f"Period: {period.capitalize()} · Generated {datetime.now().strftime('%B %d, %Y')}", sub_style))
    elements.append(Spacer(1, 0.2*inch))

    # Table
    table_data = [["Source", "Contacts", "Clients", "Total"]]
    for row in rows:
        table_data.append([
            row["source"],
            str(row["contacts"]),
            str(row["clients"]),
            str(row["contacts"] + row["clients"])
        ])

    # Totals row
    table_data.append([
        "TOTAL",
        str(sum(r["contacts"] for r in rows)),
        str(sum(r["clients"] for r in rows)),
        str(sum(r["contacts"] + r["clients"] for r in rows))
    ])

    table = Table(table_data, colWidths=[3*inch, 1.2*inch, 1.2*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f5f2ee")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e07b39")),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e0d8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e0d8")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=f"sources_report_{period}.pdf")