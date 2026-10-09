"""ReportLab-based PDF rendering for performance reports.

Each report is composed of sections; every section renders a table of the
performance analysis with a chart placed below it. Charts use ReportLab's
native ``graphics.charts`` so no external system libraries are required.
"""

import io
from datetime import date
from decimal import Decimal
from typing import Any

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 18 * mm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN

_PRIMARY = colors.HexColor("#1f6f8b")
_HEADER_BG = colors.HexColor("#1f6f8b")
_ROW_ALT = colors.HexColor("#eef5f8")
_GRID = colors.HexColor("#b8c9d1")


def _styles() -> dict[str, Any]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontSize=20,
            textColor=_PRIMARY,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#555555"),
            spaceAfter=12,
            alignment=1,
        ),
        "heading": ParagraphStyle(
            "ReportHeading",
            parent=base["Heading2"],
            fontSize=13,
            textColor=_PRIMARY,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "body": base["Normal"],
    }


def _fmt(value: Any) -> str:
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, date):
        return value.strftime("%b %Y")
    if value is None:
        return "-"
    return str(value)


def _make_table(header: list[str], rows: list[list[Any]]) -> Table:
    data: list[list[Any]] = [
        [Paragraph(f"<b>{cell}</b>", _styles()["body"]) for cell in header]
    ]
    for row in rows:
        data.append([_fmt(cell) for cell in row])
    table = Table(data, hAlign="LEFT", repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, _GRID),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ROW_ALT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    table.setStyle(TableStyle(style))
    return table


def _bar_chart(
    categories: list[str], values: list[float], width: float, height: float
) -> Drawing:
    drawing = Drawing(width, height)
    chart = VerticalBarChart()
    chart.x = 40
    chart.y = 30
    chart.height = int(height - 55)
    chart.width = int(width - 70)
    chart.data = [values] if values else [[0]]
    chart.categoryAxis.categoryNames = categories if categories else ["-"]
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 100
    chart.valueAxis.valueStep = 20
    chart.bars[0].fillColor = _PRIMARY
    chart.bars[0].strokeColor = _PRIMARY
    drawing.add(chart)
    drawing.add(
        String(width / 2, 6, "Average percentage (%)", fontSize=8, textAnchor="middle")
    )
    return drawing


def _line_chart(
    categories: list[str], values: list[float], width: float, height: float
) -> Drawing:
    from reportlab.graphics.charts.linecharts import HorizontalLineChart

    drawing = Drawing(width, height)
    chart = HorizontalLineChart()
    chart.x = 40
    chart.y = 30
    chart.height = int(height - 55)
    chart.width = int(width - 70)
    chart.data = [values] if values else [[0]]
    chart.categoryAxis.categoryNames = categories if categories else ["-"]
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 100
    chart.valueAxis.valueStep = 20
    chart.lines[0].strokeColor = _PRIMARY
    chart.lines[0].strokeWidth = 2
    drawing.add(chart)
    drawing.add(
        String(width / 2, 6, "Average percentage (%)", fontSize=8, textAnchor="middle")
    )
    return drawing


def _chart_flowable(
    labels: list[str],
    values: list[Decimal],
    kind: str,
) -> Drawing | None:
    if not labels:
        return None
    chart_width = min(CONTENT_WIDTH, 480)
    chart_height = 190
    float_values = [float(v) for v in values]
    if kind == "line":
        return _line_chart(labels, float_values, chart_width, chart_height)
    return _bar_chart(labels, float_values, chart_width, chart_height)


def section(
    heading: str,
    header: list[str],
    rows: list[list[Any]],
    *,
    chart_labels: list[str] | None = None,
    chart_values: list[Decimal] | None = None,
    chart_kind: str = "bar",
) -> list:
    """Build a titled table with an optional chart beneath it."""
    flow: list[Any] = [Paragraph(heading, _styles()["heading"])]
    if rows:
        flow.append(_make_table(header, rows))
    else:
        flow.append(Paragraph("No data available for this period.", _styles()["body"]))
    if chart_labels and chart_values:
        image = _chart_flowable(chart_labels, chart_values, chart_kind)
        if image is not None:
            flow.append(Spacer(1, 8))
            flow.append(image)
    return flow


def _build_document(flow: list[Any], buffer: io.BytesIO) -> None:
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="Performance Report",
    )
    doc.build(flow)


def _title_block(title: str, subtitle: str) -> list[Any]:
    styles = _styles()
    return [
        Paragraph(title, styles["title"]),
        Paragraph(subtitle, styles["subtitle"]),
    ]


def _period_text(start: date, end: date) -> str:
    if start == end:
        return start.strftime("%B %Y")
    return f"{start.strftime('%B %Y')} - {end.strftime('%B %Y')}"


def build_ministry_report(db: Session, start: date, end: date) -> bytes:
    """Single PDF: Ministry overview, provinces, zones and schools."""
    from src.services import report_analytics as ra

    overview = ra.ministry_overview(db, start, end)
    flow = _title_block(
        "Ministry Performance Report",
        f"Period: {_period_text(start, end)}",
    )

    summary = overview["summary"]
    flow.append(
        _make_table(
            ["Total Students", "Total Marks", "Overall Average (%)"],
            [
                [
                    summary["total_students"],
                    summary["total_marks"],
                    summary["overall_average_percentage"],
                ]
            ],
        )
    )

    provinces = overview["provinces"]
    flow += section(
        "Performance by Province",
        ["Province", "Average (%)"],
        [[p["province_name"], p["average_percentage"]] for p in provinces],
        chart_labels=[str(p["province_name"]) for p in provinces],
        chart_values=[p["average_percentage"] for p in provinces],
        chart_kind="bar",
    )

    # Per-zone breakdown across every province, and per-school breakdown.
    from src.models.province import Province

    prov_rows = list(db.scalars(select(Province)).all())
    zone_table: list[list[Any]] = []
    zone_labels: list[str] = []
    zone_values: list[Decimal] = []
    for prov in prov_rows:
        pz = ra.province_summary(db, prov.prov_id, start, end)
        for z in pz["zones"]:
            zone_table.append(
                [prov.Province_name, z["zone_name"], z["average_percentage"]]
            )
            zone_labels.append(str(z["zone_name"]))
            zone_values.append(z["average_percentage"])

    zone_section: list[Any] = [
        Paragraph("Performance by Zone", _styles()["heading"])
    ]
    if zone_table:
        zone_section.append(
            _make_table(["Province", "Zone", "Average (%)"], zone_table)
        )
    else:
        zone_section.append(
            Paragraph("No zone data available.", _styles()["body"])
        )
    flow.append(PageBreak())
    flow += zone_section

    school = ra.school_summary(db, start, end)
    schools = school["schools"]
    flow += section(
        "Performance by School",
        ["School", "Average (%)"],
        [[s["school"], s["average_percentage"]] for s in schools],
        chart_labels=[str(s["school"]) for s in schools],
        chart_values=[s["average_percentage"] for s in schools],
        chart_kind="bar",
    )

    buffer = io.BytesIO()
    _build_document(flow, buffer)
    return buffer.getvalue()


def build_zone_report(
    db: Session,
    zone_id,
    zone_name: str | None,
    start: date,
    end: date,
) -> bytes:
    """Zone-wide performance + teacher performance within the zone."""
    from src.services import report_analytics as ra

    z = ra.zone_summary(db, zone_id, start, end)
    title = "Zonal Performance Report"
    if zone_name:
        title += f" - {zone_name}"
    flow = _title_block(title, f"Period: {_period_text(start, end)}")

    summary = z["summary"]
    flow.append(
        _make_table(
            ["Total Students", "Total Marks", "Overall Average (%)"],
            [
                [
                    summary["total_students"],
                    summary["total_marks"],
                    summary["overall_average_percentage"],
                ]
            ],
        )
    )

    subjects = z["subjects"]
    flow += section(
        "Performance by Subject",
        ["Subject", "Average (%)"],
        [[s["subject"], s["average_percentage"]] for s in subjects],
        chart_labels=[str(s["subject"]) for s in subjects],
        chart_values=[s["average_percentage"] for s in subjects],
        chart_kind="bar",
    )

    schools = z["schools"]
    flow += section(
        "Performance by School",
        ["School", "Average (%)"],
        [[s["school"], s["average_percentage"]] for s in schools],
        chart_labels=[str(s["school"]) for s in schools],
        chart_values=[s["average_percentage"] for s in schools],
        chart_kind="bar",
    )

    trend = z["monthly_trend"]
    flow += section(
        "Monthly Performance Trend",
        ["Month", "Average (%)"],
        [[t["month"], t["average_percentage"]] for t in trend],
        chart_labels=[t["month"].strftime("%b %Y") for t in trend],
        chart_values=[t["average_percentage"] for t in trend],
        chart_kind="line",
    )

    flow.append(PageBreak())
    teachers = ra.teacher_performance(db, start, end, zone_id=zone_id)
    rows = teachers["teachers"]
    flow += section(
        "Teacher Performance in Zone",
        ["Teacher", "Subject", "Students", "Marks", "Average (%)"],
        [
            [
                t["teacher_name"],
                t["subject"],
                t["student_count"],
                t["total_marks"],
                t["average_percentage"],
            ]
            for t in rows
        ],
        chart_labels=[str(t["teacher_name"]) for t in rows],
        chart_values=[t["average_percentage"] for t in rows],
        chart_kind="bar",
    )

    buffer = io.BytesIO()
    _build_document(flow, buffer)
    return buffer.getvalue()


def build_teacher_report(
    db: Session,
    teacher_id,
    teacher_name: str | None,
    zone_id,
    start: date,
    end: date,
) -> bytes:
    """Teacher's own performance + their assigned students' performance."""
    from src.services import report_analytics as ra

    title = "Teacher Performance Report"
    if teacher_name:
        title += f" - {teacher_name}"
    flow = _title_block(title, f"Period: {_period_text(start, end)}")

    own = ra.teacher_performance(db, start, end, teacher_id=teacher_id)
    own_rows = own["teachers"]
    flow += section(
        "My Performance",
        ["Teacher", "Subject", "Students", "Marks", "Average (%)"],
        [
            [
                t["teacher_name"],
                t["subject"],
                t["student_count"],
                t["total_marks"],
                t["average_percentage"],
            ]
            for t in own_rows
        ],
    )

    # Assigned students performance.
    assigned = ra._assigned_student_ids(db, teacher_id)
    student_rows = ra.fetch_marks(db, start, end, teacher_id=teacher_id)
    per_student: dict = {}
    for r in student_rows:
        if r["student_id"] not in assigned:
            continue
        per_student.setdefault(r["student_id"], []).append(r["percentage"])

    from src.models.student import Student as StudentModel

    table_rows: list[list[Any]] = []
    labels: list[str] = []
    values: list[Decimal] = []
    for sid, percentages in per_student.items():
        student = db.get(StudentModel, sid)
        name = student.Name if student else str(sid)
        avg = ra._avg(percentages)
        table_rows.append([name, len(percentages), avg])
        labels.append(name)
        values.append(avg)
    table_rows.sort(key=lambda row: str(row[0]))

    flow.append(PageBreak())
    flow += section(
        "Assigned Students Performance",
        ["Student", "Marks", "Average (%)"],
        table_rows,
        chart_labels=labels,
        chart_values=values,
        chart_kind="bar",
    )

    buffer = io.BytesIO()
    _build_document(flow, buffer)
    return buffer.getvalue()


def build_student_report(
    db: Session, student_id, start: date, end: date
) -> bytes:
    """A student's own subject and marks performance."""
    from src.services import report_analytics as ra

    s = ra.student_performance(db, student_id, start, end)
    title = "My Performance Report"
    if s["student_name"]:
        title += f" - {s['student_name']}"
    flow = _title_block(title, f"Period: {_period_text(start, end)}")

    if s["grade"]:
        grade_text = s["grade"]
        if s["stream"]:
            grade_text += f" ({s['stream']})"
        flow.append(
            _make_table(
                ["Grade", "School", "Marks", "Overall Average (%)"],
                [
                    [
                        grade_text,
                        s["school"],
                        s["summary"]["total_marks"],
                        s["summary"]["overall_average_percentage"],
                    ]
                ],
            )
        )

    subjects = s["subjects"]
    flow += section(
        "Performance by Subject",
        ["Subject", "Average (%)"],
        [[sub["subject"], sub["average_percentage"]] for sub in subjects],
        chart_labels=[str(sub["subject"]) for sub in subjects],
        chart_values=[sub["average_percentage"] for sub in subjects],
        chart_kind="bar",
    )

    trend = s["monthly_trend"]
    flow += section(
        "Monthly Performance Trend",
        ["Month", "Average (%)"],
        [[t["month"], t["average_percentage"]] for t in trend],
        chart_labels=[t["month"].strftime("%b %Y") for t in trend],
        chart_values=[t["average_percentage"] for t in trend],
        chart_kind="line",
    )

    buffer = io.BytesIO()
    _build_document(flow, buffer)
    return buffer.getvalue()



