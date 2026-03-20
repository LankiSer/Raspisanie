"""Reports router — workload stats + PDF schedule export."""

import io
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import get_current_active_user_or_demo
from ..core.database import get_db
from ..models.educational import Enrollment, Group, Teacher, Course, CourseAssignment
from ..models.facilities import Room, TimeTableSlot
from ..models.scheduling import LessonInstance, LessonStatus
from ..models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helper: build flat lesson list ───────────────────────────────────────────

async def _get_lessons(
    db: AsyncSession,
    org_id: int,
    start_date: date,
    end_date: date,
    group_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
):
    """Return dicts with lesson + related data for the date range."""
    query = (
        select(
            LessonInstance.lesson_id,
            LessonInstance.date,
            LessonInstance.status,
            Group.group_id,
            Group.name.label("group_name"),
            func.concat(Teacher.first_name, " ", Teacher.last_name).label("teacher_name"),
            Course.name.label("course_name"),
            Room.number.label("room_number"),
            TimeTableSlot.start_time,
            TimeTableSlot.end_time,
        )
        .select_from(LessonInstance)
        .join(Enrollment, LessonInstance.enrollment_id == Enrollment.enrollment_id)
        .join(CourseAssignment, Enrollment.assignment_id == CourseAssignment.assignment_id)
        .join(Group, Enrollment.group_id == Group.group_id)
        .join(Teacher, CourseAssignment.teacher_id == Teacher.teacher_id)
        .join(Course, CourseAssignment.course_id == Course.course_id)
        .join(Room, LessonInstance.room_id == Room.room_id)
        .join(TimeTableSlot, LessonInstance.slot_id == TimeTableSlot.slot_id)
        .where(
            LessonInstance.org_id == org_id,
            LessonInstance.date >= start_date,
            LessonInstance.date <= end_date,
            LessonInstance.status != LessonStatus.CANCELLED,
        )
        .order_by(LessonInstance.date, TimeTableSlot.start_time)
    )
    if group_id:
        query = query.where(Group.group_id == group_id)
    if teacher_id:
        query = query.where(Teacher.teacher_id == teacher_id)

    result = await db.execute(query)
    return result.mappings().all()


# ── Workload reports (JSON) ───────────────────────────────────────────────────

@router.get("/workload/teacher")
async def get_teacher_workload(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo),
):
    """Count lessons per teacher in date range."""
    rows = await _get_lessons(db, current_user.org_id, start_date, end_date)
    counts: dict = {}
    for row in rows:
        key = row["teacher_name"]
        counts[key] = counts.get(key, 0) + 1
    workload = [{"teacher_name": k, "lesson_count": v} for k, v in sorted(counts.items())]
    return {"start_date": str(start_date), "end_date": str(end_date), "workload": workload}


@router.get("/workload/group")
async def get_group_workload(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo),
):
    """Count lessons per group in date range."""
    rows = await _get_lessons(db, current_user.org_id, start_date, end_date)
    counts: dict = {}
    for row in rows:
        key = row["group_name"]
        counts[key] = counts.get(key, 0) + 1
    workload = [{"group_name": k, "lesson_count": v} for k, v in sorted(counts.items())]
    return {"start_date": str(start_date), "end_date": str(end_date), "workload": workload}


@router.get("/conflicts")
async def get_conflicts(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo),
):
    """Detect room double-bookings (same room + slot + date, multiple lessons)."""
    from datetime import timedelta
    if start_date is None:
        start_date = date.today() - timedelta(days=30)
    if end_date is None:
        end_date = date.today()
    query = (
        select(
            LessonInstance.date,
            LessonInstance.slot_id,
            LessonInstance.room_id,
            func.count(LessonInstance.lesson_id).label("cnt"),
        )
        .where(
            LessonInstance.org_id == current_user.org_id,
            LessonInstance.date >= start_date,
            LessonInstance.date <= end_date,
            LessonInstance.status != LessonStatus.CANCELLED,
        )
        .group_by(LessonInstance.date, LessonInstance.slot_id, LessonInstance.room_id)
        .having(func.count(LessonInstance.lesson_id) > 1)
    )
    result = await db.execute(query)
    conflicts = [
        {"date": str(r.date), "slot_id": r.slot_id, "room_id": r.room_id, "count": r.cnt}
        for r in result.all()
    ]
    return {"start_date": str(start_date), "end_date": str(end_date), "conflicts": conflicts}


# ── PDF export ────────────────────────────────────────────────────────────────

def _build_pdf(lessons, title: str) -> bytes:
    """Build a PDF schedule table using ReportLab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        )
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os

        # Try to register a Cyrillic-capable font; fall back to Helvetica if not found
        font_name = "Helvetica"
        try:
            # Use DejaVu if available (common on Linux servers)
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont("DejaVu", font_path))
                font_name = "DejaVu"
        except Exception:
            pass

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=landscape(A4),
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "title", parent=styles["Heading1"],
            fontName=font_name, fontSize=14, spaceAfter=12
        )
        cell_style = ParagraphStyle(
            "cell", parent=styles["Normal"],
            fontName=font_name, fontSize=8, leading=10
        )

        gov_blue = colors.HexColor("#1f5abf")

        elements = [
            Paragraph(title, title_style),
            Spacer(1, 0.3 * cm),
        ]

        # Table headers
        headers = ["Дата", "Время", "Группа", "Предмет", "Преподаватель", "Аудитория"]
        data = [[Paragraph(h, cell_style) for h in headers]]

        for lesson in lessons:
            start = str(lesson.get("start_time", ""))[:5]
            end = str(lesson.get("end_time", ""))[:5]
            row = [
                Paragraph(str(lesson.get("date", "")), cell_style),
                Paragraph(f"{start}–{end}", cell_style),
                Paragraph(str(lesson.get("group_name", "")), cell_style),
                Paragraph(str(lesson.get("course_name", "")), cell_style),
                Paragraph(str(lesson.get("teacher_name", "")), cell_style),
                Paragraph(str(lesson.get("room_number", "")), cell_style),
            ]
            data.append(row)

        col_widths = [2.5 * cm, 2.5 * cm, 3.5 * cm, 7 * cm, 6 * cm, 2.5 * cm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), gov_blue),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), font_name),
            ("FONTSIZE",     (0, 0), (-1, 0), 8),
            ("FONTNAME",     (0, 1), (-1, -1), font_name),
            ("FONTSIZE",     (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4fb")]),
            ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",  (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))

        elements.append(table)
        doc.build(elements)
        return buf.getvalue()

    except ImportError:
        raise RuntimeError("reportlab не установлен. Выполните: pip install reportlab")


@router.get("/pdf/schedule")
async def export_schedule_pdf(
    start_date: date = Query(...),
    end_date: date = Query(...),
    group_id: Optional[int] = Query(None),
    teacher_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo),
):
    """Export schedule as PDF for a date range, optionally filtered by group or teacher."""
    rows = await _get_lessons(
        db, current_user.org_id, start_date, end_date, group_id, teacher_id
    )
    lessons = [dict(r) for r in rows]

    title = f"Расписание {start_date} — {end_date}"
    if group_id and lessons:
        title += f" | Группа: {lessons[0].get('group_name', group_id)}"
    if teacher_id and lessons:
        title += f" | Преподаватель: {lessons[0].get('teacher_name', teacher_id)}"

    try:
        pdf_bytes = _build_pdf(lessons, title)
    except RuntimeError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(exc))

    filename = f"schedule_{start_date}_{end_date}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Hours journal ─────────────────────────────────────────────────────────────

# Map lesson status → (sign, label)
_STATUS_MAP = {
    LessonStatus.PLANNED:   (1,  "Запланировано"),
    LessonStatus.CONFIRMED: (1,  "Подтверждено"),
    LessonStatus.COMPLETED: (1,  "Проведено"),
    LessonStatus.CANCELLED: (-1, "↩ Возврат (отмена)"),
    LessonStatus.SKIPPED:   (-1, "↩ Возврат (пропуск)"),
    LessonStatus.MOVED:     (0,  "↗ Перенесено"),
}
_HOURS_PER_LESSON = 1.5


@router.get("/hours-log")
async def get_hours_log(
    start_date: date = Query(...),
    end_date:   date = Query(...),
    group_id:    Optional[int] = Query(None),
    teacher_id:  Optional[int] = Query(None),
    enrollment_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo),
):
    """
    Return a detailed hours journal for the date range.

    Each row represents one lesson and shows:
    - how many academic hours were **charged** (positive statuses)
    - or **returned** (CANCELLED, SKIPPED)
    """
    query = (
        select(
            LessonInstance.lesson_id,
            LessonInstance.date,
            LessonInstance.status,
            LessonInstance.enrollment_id,
            Group.group_id,
            Group.name.label("group_name"),
            func.concat(Teacher.first_name, " ", Teacher.last_name).label("teacher_name"),
            Course.name.label("course_name"),
            Room.number.label("room_number"),
            TimeTableSlot.start_time,
            TimeTableSlot.end_time,
        )
        .select_from(LessonInstance)
        .join(Enrollment,      LessonInstance.enrollment_id == Enrollment.enrollment_id)
        .join(CourseAssignment, Enrollment.assignment_id == CourseAssignment.assignment_id)
        .join(Group,   Enrollment.group_id == Group.group_id)
        .join(Teacher, CourseAssignment.teacher_id == Teacher.teacher_id)
        .join(Course,  CourseAssignment.course_id == Course.course_id)
        .join(Room,    LessonInstance.room_id == Room.room_id)
        .join(TimeTableSlot, LessonInstance.slot_id == TimeTableSlot.slot_id)
        .where(
            LessonInstance.org_id == current_user.org_id,
            LessonInstance.date >= start_date,
            LessonInstance.date <= end_date,
        )
        .order_by(LessonInstance.date.desc(), TimeTableSlot.start_time.desc())
    )
    if group_id:
        query = query.where(Group.group_id == group_id)
    if teacher_id:
        query = query.where(Teacher.teacher_id == teacher_id)
    if enrollment_id:
        query = query.where(LessonInstance.enrollment_id == enrollment_id)

    result = await db.execute(query)
    rows = result.mappings().all()

    entries = []
    total_charged  = 0.0
    total_returned = 0.0

    for row in rows:
        status = row["status"]
        sign, label = _STATUS_MAP.get(status, (1, str(status)))
        hours = round(sign * _HOURS_PER_LESSON, 2)

        if sign > 0:
            total_charged  += _HOURS_PER_LESSON
        elif sign < 0:
            total_returned += _HOURS_PER_LESSON

        entries.append({
            "lesson_id":     row["lesson_id"],
            "date":          str(row["date"]),
            "group_name":    row["group_name"],
            "course_name":   row["course_name"],
            "teacher_name":  row["teacher_name"],
            "room_number":   row["room_number"],
            "start_time":    str(row["start_time"])[:5],
            "end_time":      str(row["end_time"])[:5],
            "status":        status.value if hasattr(status, "value") else str(status),
            "hours":         hours,
            "note":          label,
            "enrollment_id": row["enrollment_id"],
        })

    return {
        "start_date":     str(start_date),
        "end_date":       str(end_date),
        "entries":        entries,
        "total_charged":  round(total_charged,  2),
        "total_returned": round(total_returned, 2),
        "net_hours":      round(total_charged - total_returned, 2),
    }
