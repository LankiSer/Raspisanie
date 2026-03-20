"""Schedule generation router."""

import asyncio
import logging
import random
import time
import uuid
from datetime import date, timedelta, time as dt_time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user_or_demo
from app.core.database import AsyncSessionLocal, get_db
from app.models.academic import AcademicYear, Term
from app.models.educational import (
    Course, CourseAssignment, Enrollment, Group, Teacher,
)
from app.models.facilities import Room, TeacherAvailability, TimeTableSlot
from app.models.scheduling import LessonInstance, LessonStatus
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

# ── In-process job store (preview + run) ─────────────────────────────────────
# Suitable for single-worker deployments; swap for Redis for multi-worker.
_jobs: Dict[str, Dict[str, Any]] = {}
_JOB_TTL_SECONDS = 3600  # clean up after 1 h


def _new_job() -> tuple[str, dict]:
    job_id = str(uuid.uuid4())
    job: Dict[str, Any] = {"status": "running", "result": None, "error": None, "created_at": time.monotonic()}
    _jobs[job_id] = job
    return job_id, job


def _purge_old_jobs() -> None:
    cutoff = time.monotonic() - _JOB_TTL_SECONDS
    stale = [jid for jid, j in _jobs.items() if j.get("created_at", 0) < cutoff]
    for jid in stale:
        _jobs.pop(jid, None)


class _FakeUser:
    """Minimal user-like object carrying org_id and user_id for background tasks."""
    def __init__(self, org_id: int, user_id: int):
        self.org_id  = org_id
        self.user_id = user_id


async def _run_bg_preview(job_id: str, request: "GenerationRequest", org_id: int) -> None:
    """Background coroutine: compute preview and store result."""
    try:
        async with AsyncSessionLocal() as db:
            result = await _preview_generation_internal(request, db, _FakeUser(org_id, 0))
        _jobs[job_id].update(
            status="done",
            result=result.model_dump() if hasattr(result, "model_dump") else dict(result),
        )
    except Exception as exc:
        logger.exception("Preview job %s failed: %s", job_id, exc)
        _jobs[job_id].update(status="error", error=str(exc))


async def _run_bg_save(job_id: str, request: "GenerationRequest", org_id: int, user_id: int) -> None:
    """Background coroutine: generate + save lessons, store result."""
    from sqlalchemy import select, delete as sa_delete

    try:
        async with AsyncSessionLocal() as db:
            fake_user = _FakeUser(org_id, user_id)

            # ── Find or create term ───────────────────────────────────────
            term = None
            if request.term_id:
                r = await db.execute(
                    select(Term).where(Term.term_id == request.term_id, Term.org_id == org_id).limit(1)
                )
                term = r.scalars().first()

            if not term:
                for clauses in [
                    [Term.start_date <= request.from_date, Term.end_date >= request.to_date],
                    [Term.start_date <= request.from_date, Term.end_date >= request.from_date],
                    [Term.start_date <= request.to_date,   Term.end_date >= request.to_date],
                    [Term.start_date <= request.to_date,   Term.end_date >= request.from_date],
                ]:
                    r = await db.execute(
                        select(Term).where(Term.org_id == org_id, *clauses)
                        .order_by(Term.start_date.desc()).limit(1)
                    )
                    term = r.scalars().first()
                    if term:
                        break

            if not term:
                # Auto-create academic year + term
                r = await db.execute(
                    select(AcademicYear).where(
                        AcademicYear.org_id == org_id,
                        AcademicYear.start_date <= request.from_date,
                        AcademicYear.end_date   >= request.to_date,
                    ).order_by(AcademicYear.start_date.desc()).limit(1)
                )
                academic_year = r.scalars().first()

                if not academic_year:
                    ys = request.from_date.year
                    ye = request.to_date.year
                    ay_name = f"{ys}-{ye}" if ys != ye else f"{ys}-{ys + 1}"
                    ay_start = date(ys, 9, 1) if request.from_date.month >= 9 else date(ys - 1, 9, 1)
                    ay_end   = date(ys + 1, 6, 30) if request.from_date.month >= 9 else date(ys, 6, 30)
                    academic_year = AcademicYear(org_id=org_id, name=ay_name, start_date=ay_start, end_date=ay_end)
                    db.add(academic_year)
                    await db.flush()

                term = Term(
                    org_id=org_id,
                    academic_year_id=academic_year.id,
                    name=f"Семестр {request.from_date} — {request.to_date}",
                    start_date=request.from_date,
                    end_date=request.to_date,
                )
                db.add(term)
                await db.flush()

            # Stretch term to cover the full requested range
            if term.start_date > request.from_date or term.end_date < request.to_date:
                term.start_date = min(term.start_date, request.from_date)
                term.end_date   = max(term.end_date,   request.to_date)
                await db.flush()

            # ── Generate proposals ────────────────────────────────────────
            preview_result = await _preview_generation_internal(request, db, fake_user)
            if not preview_result.success or not preview_result.proposals:
                _jobs[job_id].update(status="error", error="Генерация не дала результатов. Проверьте данные (группы, аудитории, слоты, записи).")
                return

            # Stretch term again after we know the actual proposal dates
            if preview_result.proposals:
                p_dates = [p.date for p in preview_result.proposals]
                term.start_date = min(term.start_date, min(p_dates))
                term.end_date   = max(term.end_date,   max(p_dates))
                await db.flush()

            # ── Clear existing lessons for date range ─────────────────────
            await db.execute(
                sa_delete(LessonInstance).where(
                    LessonInstance.org_id == org_id,
                    LessonInstance.date   >= request.from_date,
                    LessonInstance.date   <= request.to_date,
                )
            )

            # ── Save new lessons ──────────────────────────────────────────
            for proposal in preview_result.proposals:
                db.add(LessonInstance(
                    org_id=org_id,
                    term_id=term.term_id,
                    date=proposal.date,
                    slot_id=proposal.slot_id,
                    room_id=proposal.room_id,
                    enrollment_id=proposal.enrollment_id,
                    status=LessonStatus.CONFIRMED,
                    created_by=user_id,
                ))

            await db.commit()

            created = len(preview_result.proposals)
            logger.info("Run job %s done: %d lessons saved (term_id=%s)", job_id, created, term.term_id)
            _jobs[job_id].update(
                status="done",
                result={
                    "success": True,
                    "message": f"Генерация завершена! Создано {created} занятий.",
                    "created_lessons":   created,
                    "total_blocks":      len(preview_result.blocks),
                    "total_proposals":   len(preview_result.proposals),
                    "stats":             preview_result.stats,
                },
            )

    except Exception as exc:
        logger.exception("Run job %s failed: %s", job_id, exc)
        _jobs[job_id].update(status="error", error=str(exc))

# Simple request/response models for demo
class GenerationRuleset(BaseModel):
    respect_availability: bool = True
    max_lessons_per_day_group: int = 6
    max_lessons_per_day_teacher: int = 8
    room_capacity_check: bool = True
    enable_block_scheduling: bool = True
    max_blocks_per_day: int = 2
    min_gap_between_blocks: int = 1

class GenerationRequest(BaseModel):
    term_id: Optional[int] = None  # Optional - will auto-create if not provided
    from_date: date
    to_date: date
    ruleset: GenerationRuleset = GenerationRuleset()

class GeneratedLesson(BaseModel):
    date: date
    slot_id: int
    room_id: int
    enrollment_id: int
    group_id: int  # Add group_id for conflict checking
    group_name: str
    teacher_name: str
    course_name: str
    room_number: str
    start_time: str
    end_time: str

class LessonBlock(BaseModel):
    date: date
    start_slot_id: int
    end_slot_id: int
    slot_ids: List[int] = Field(default_factory=list)  # все slot_id блока
    room_id: int
    enrollment_id: int
    group_id: int
    teacher_id: int
    course_id: int
    group_name: str
    teacher_name: str
    course_name: str
    room_number: str
    start_time: str
    end_time: str
    block_size: int

class GenerationResult(BaseModel):
    proposals: List[GeneratedLesson]
    blocks: List[LessonBlock] = []
    stats: Dict[str, Any]
    conflicts: List[str] = []
    success: bool = True


def _dedupe_and_filter_slots(slots: list) -> list:
    """Убрать дубликаты по (start,end) и слоты вне учебного дня (мусор в БД)."""
    if not slots:
        return []
    out: list = []
    seen: set = set()
    for s in sorted(slots, key=lambda x: (x.start_time, x.end_time, x.slot_id)):
        try:
            st = s.start_time
            et = s.end_time
        except Exception:
            continue
        if st < dt_time(6, 0) or st > dt_time(23, 0):
            continue
        key = (st, et)
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def _weekdays_left_same_iso_week(day: date, range_end: date) -> int:
    """Сколько рабочих дней (пн–пт) осталось в той же ISO-неделе, начиная с day."""
    y, w, _ = day.isocalendar()
    cnt = 0
    cur = day
    while cur <= range_end:
        if cur.weekday() < 5 and cur.isocalendar()[:2] == (y, w):
            cnt += 1
        cur += timedelta(days=1)
    return max(1, cnt)


def _count_weekdays_in_range(from_d: date, to_d: date) -> int:
    n = 0
    cur = from_d
    while cur <= to_d:
        if cur.weekday() < 5:
            n += 1
        cur += timedelta(days=1)
    return max(1, n)


def _compute_lessons_per_week(enrollments: list) -> Dict[int, int]:
    out: Dict[int, int] = {}
    for enrollment in enrollments:
        unit = getattr(enrollment, "unit", "per_semester") or "per_semester"
        if unit == "per_week":
            weekly_hours = float(enrollment.planned_hours)
        else:
            weekly_hours = float(enrollment.planned_hours) / 18.0
        lpw = min(6, max(1, round(weekly_hours / 1.5)))
        out[enrollment.enrollment_id] = lpw
    return out


def _build_avail_by_teacher(rows: List[TeacherAvailability]) -> Dict[int, List[TeacherAvailability]]:
    m: Dict[int, List[TeacherAvailability]] = {}
    for a in rows:
        m.setdefault(a.teacher_id, []).append(a)
    return m


def _teacher_already_booked(
    teacher_id: int,
    day: date,
    slot_ids: set,
    proposals: list,
    enrollments_list: list,
    assignments_dict: dict,
) -> bool:
    """Преподаватель уже ведёт другую пару в эти слоты в этот день."""
    enr_by_id = {e.enrollment_id: e for e in enrollments_list}
    for p in proposals:
        if p.date != day or p.slot_id not in slot_ids:
            continue
        enr = enr_by_id.get(p.enrollment_id)
        if not enr:
            continue
        asgn = assignments_dict.get(enr.assignment_id)
        if asgn and asgn.teacher_id == teacher_id:
            return True
    return False


def _teacher_slots_allowed(
    teacher_id: int,
    day: date,
    slot_objs: list,
    avail_by_teacher: Dict[int, List[TeacherAvailability]],
    respect: bool,
) -> bool:
    """Пара(ы) попадают в окна доступности преподавателя (пн–вс = 1–7)."""
    if not respect:
        return True
    rows = avail_by_teacher.get(teacher_id, [])
    if not rows:
        return True
    wd = day.weekday() + 1  # SQL model: 1=Monday .. 7=Sunday
    for slot in slot_objs:
        st, et = slot.start_time, slot.end_time
        for a in rows:
            if a.weekday != wd or a.is_available:
                continue
            if not (et <= a.start_time or st >= a.end_time):
                return False
        positive = [a for a in rows if a.weekday == wd and a.is_available]
        if positive:
            if not any(a.start_time <= st and a.end_time >= et for a in positive):
                return False
    return True


async def _preview_generation_internal(
    request: GenerationRequest,
    db: AsyncSession,
    current_user: User
):
    """Generate schedule preview using real data with block scheduling (internal function)."""
    
    from sqlalchemy import select
    
    # Load real data from database
    groups_result = await db.execute(select(Group).where(Group.org_id == current_user.org_id))
    groups = groups_result.scalars().all()
    
    teachers_result = await db.execute(select(Teacher).where(Teacher.org_id == current_user.org_id))
    teachers = teachers_result.scalars().all()
    
    rooms_result = await db.execute(select(Room).where(Room.org_id == current_user.org_id))
    rooms = rooms_result.scalars().all()
    
    slots_result = await db.execute(
        select(TimeTableSlot)
        .where(TimeTableSlot.org_id == current_user.org_id)
        .order_by(TimeTableSlot.start_time)
    )
    slots = _dedupe_and_filter_slots(list(slots_result.scalars().all()))
    if not slots:
        return GenerationResult(
            proposals=[], blocks=[], stats={}, conflicts=["Нет корректных временных слотов (06:00–23:00)"], success=False
        )

    enrollments_result = await db.execute(select(Enrollment).where(Enrollment.org_id == current_user.org_id))
    enrollments = enrollments_result.scalars().all()
    
    # Create lookup dictionaries
    groups_dict = {g.group_id: g for g in groups}
    teachers_dict = {t.teacher_id: t for t in teachers}
    rooms_dict = {r.room_id: r for r in rooms}
    slots_dict = {s.slot_id: s for s in slots}
    
    # Load course assignments for enrollments
    assignment_ids = [e.assignment_id for e in enrollments]
    assignments_result = await db.execute(
        select(CourseAssignment).where(CourseAssignment.assignment_id.in_(assignment_ids))
    )
    assignments = assignments_result.scalars().all()
    assignments_dict = {a.assignment_id: a for a in assignments}
    
    # Load courses
    course_ids = [a.course_id for a in assignments]
    courses_result = await db.execute(select(Course).where(Course.course_id.in_(course_ids)))
    courses = courses_result.scalars().all()
    courses_dict = {c.course_id: c for c in courses}

    av_res = await db.execute(
        select(TeacherAvailability).where(TeacherAvailability.org_id == current_user.org_id)
    )
    avail_by_teacher = _build_avail_by_teacher(list(av_res.scalars().all()))

    lessons_per_week_per_enrollment = _compute_lessons_per_week(list(enrollments))
    group_enrollments: Dict[int, List] = {}
    for enrollment in enrollments:
        group_enrollments.setdefault(enrollment.group_id, []).append(enrollment)
    weekly_target = {
        gid: sum(lessons_per_week_per_enrollment[e.enrollment_id] for e in elist)
        for gid, elist in group_enrollments.items()
    }
    n_wd = _count_weekdays_in_range(request.from_date, request.to_date)
    weeks_equiv = max(1.0, n_wd / 5.0)
    target_floor = max(15, int(sum(weekly_target.values()) * weeks_equiv * 0.3))
    
    # ---------------------------------------------------------------
    # OR-Tools CP-SAT (если результат слишком «пустой» — берём эвристику)
    # ---------------------------------------------------------------
    import asyncio

    def _build_dates(from_d, to_d):
        dates_out = []
        cur = from_d
        while cur <= to_d:
            if cur.weekday() < 5:
                dates_out.append(cur)
            cur += timedelta(days=1)
        return dates_out

    dates_for_ortools = _build_dates(request.from_date, request.to_date)

    loop = asyncio.get_event_loop()
    ortools_proposals = await loop.run_in_executor(
        None,
        _ortools_generate,
        list(groups), list(teachers_dict.values()), list(rooms), list(slots),
        list(enrollments), assignments_dict, courses_dict,
        dates_for_ortools, request.ruleset, 25.0, avail_by_teacher,
    )

    if ortools_proposals and len(ortools_proposals) < target_floor:
        logger.info(
            "OR-Tools дал мало занятий (%s < %s), переключаемся на эвристику",
            len(ortools_proposals), target_floor,
        )
        ortools_proposals = []

    if ortools_proposals:
        logger.info("OR-Tools generated %s lessons", len(ortools_proposals))
        stats = {
            "total_lessons": len(ortools_proposals),
            "total_blocks": 0,
            "groups_count": len(groups),
            "teachers_count": len(teachers),
            "rooms_count": len(rooms),
            "time_slots_count": len(slots),
            "enrollments_count": len(enrollments),
            "date_range": f"{request.from_date} - {request.to_date}",
            "generation_method": "OR-Tools CP-SAT",
            "block_scheduling_enabled": False,
        }
        return GenerationResult(proposals=ortools_proposals, blocks=[], stats=stats, success=True)

    # ---------------------------------------------------------------
    # Heuristic fallback
    # ---------------------------------------------------------------
    logger.info("Falling back to heuristic block scheduler")
    
    # Generate lessons and blocks
    proposals = []
    blocks = []
    
    # Shuffle enrollments within each group to randomize course order
    # This ensures different courses appear in different orders across groups
    for group_id in group_enrollments:
        random.shuffle(group_enrollments[group_id])

    # Сколько уже поставлено в текущей ISO-неделе: (год, номер_недели, group_id) → int
    placed_iso_week: Dict[tuple, int] = {}
    
    # Generate lessons for each day
    # Ensure from_date and to_date are valid date objects
    if not isinstance(request.from_date, date):
        raise ValueError(f"from_date must be a date object, got {type(request.from_date)}")
    if not isinstance(request.to_date, date):
        raise ValueError(f"to_date must be a date object, got {type(request.to_date)}")
    
    current_date = request.from_date
    logger.debug(f"Starting date iteration from {current_date} to {request.to_date}")
    while current_date <= request.to_date:
        if current_date.weekday() < 5:  # Monday=0, Sunday=6
            # Generate blocks for each group (distribute across days)
            for group_id, group_enrollments_list in group_enrollments.items():
                group = groups_dict.get(group_id)
                if not group:
                    continue
                
                # Get generation type for this group (2, 3, or 5 lessons per block)
                block_size = max(1, int(group.generation_type or 2))
                max_blocks = request.ruleset.max_blocks_per_day
                
                total_group_lessons = weekly_target.get(group_id, 0)
                iso = current_date.isocalendar()
                wk_key = (iso[0], iso[1], group_id)
                already = placed_iso_week.get(wk_key, 0)
                remaining_week = max(0, total_group_lessons - already)
                days_left = _weekdays_left_same_iso_week(current_date, request.to_date)

                if remaining_week <= 0:
                    lessons_this_day = 0
                else:
                    # Равномерно добираем оставшиеся пары по рабочим дням недели
                    per_day = max(1, (remaining_week + days_left - 1) // days_left)
                    cap = block_size * max_blocks
                    lessons_this_day = min(cap, per_day, remaining_week)
                
                # Generate blocks for this day
                lessons_given = 0
                block_count = 0
                
                # Distribute groups across time slots and rooms to avoid conflicts
                # Each group gets a different starting slot and room
                group_slot_offset = (group_id - 1) % len(slots)  # 0-4 for groups 1-5
                group_room_offset = (group_id - 1) % len(rooms)  # 0-4 for groups 1-5
                
                while lessons_given < lessons_this_day and block_count < max_blocks:
                    # Calculate how many lessons in this block
                    remaining_lessons = lessons_this_day - lessons_given
                    current_block_size = min(block_size, remaining_lessons)
                    
                    if current_block_size == 0:
                        break
                    
                    # Find consecutive time slots starting from group's assigned slot
                    available_slots = _find_consecutive_slots_for_group(
                        slots, current_block_size, group_slot_offset,
                        group_id, current_date, 
                        proposals, blocks, 
                        groups_dict, teachers_dict, 
                        assignments_dict, courses_dict
                    )
                    
                    if available_slots:
                        # Find available room starting from group's assigned room
                        available_room = _find_available_room_for_group(
                            rooms, available_slots, group_room_offset,
                            current_date, proposals, blocks
                        )
                        
                        if available_room:
                            if not group_enrollments_list:
                                block_count += 1
                                continue
                            # Choose one enrollment for this block with smart randomization
                            # Goal: avoid same course in consecutive blocks
                            if group_enrollments_list:
                                # Get the last course used for this group today (if any)
                                last_course_id = None
                                if proposals:
                                    # Find last proposal for this group on this date
                                    group_proposals_today = [
                                        p for p in proposals 
                                        if p.group_id == group_id and p.date == current_date
                                    ]
                                    if group_proposals_today:
                                        last_proposal = group_proposals_today[-1]
                                        last_enrollment_id = last_proposal.enrollment_id
                                        last_enrollment = next(
                                            (e for e in group_enrollments_list if e.enrollment_id == last_enrollment_id),
                                            None
                                        )
                                        if last_enrollment and last_enrollment.assignment_id:
                                            last_assignment = assignments_dict.get(last_enrollment.assignment_id)
                                            if last_assignment and hasattr(last_assignment, 'course_id'):
                                                last_course_id = last_assignment.course_id
                                
                                # Try to select a different course than the last one
                                available_enrollments = group_enrollments_list.copy()
                                if last_course_id and len(available_enrollments) > 1:
                                    # Remove enrollments with the same course as last one
                                    available_enrollments = [
                                        e for e in available_enrollments
                                        if e.assignment_id and assignments_dict.get(e.assignment_id) and 
                                           assignments_dict[e.assignment_id].course_id != last_course_id
                                    ]
                                    # If we removed all, use original list
                                    if not available_enrollments:
                                        available_enrollments = group_enrollments_list
                                
                                # Use day and block_count for variety, plus randomization
                                day_variation = current_date.day % len(available_enrollments) if len(available_enrollments) > 0 else 0
                                base_index = (block_count + day_variation) % len(available_enrollments)
                                
                                # Add randomization (70% chance to use base, 30% to use different)
                                if random.random() < 0.7 or len(available_enrollments) == 1:
                                    enrollment_index = base_index
                                else:
                                    # Choose a different enrollment
                                    other_indices = [i for i in range(len(available_enrollments)) if i != base_index]
                                    enrollment_index = random.choice(other_indices) if other_indices else base_index
                                
                                enrollment = available_enrollments[enrollment_index]
                                
                                assignment = assignments_dict.get(enrollment.assignment_id)
                                if assignment:
                                    teacher = teachers_dict.get(assignment.teacher_id)
                                    course = courses_dict.get(assignment.course_id)
                                    
                                    if teacher and course:
                                        if not _teacher_slots_allowed(
                                            assignment.teacher_id,
                                            current_date,
                                            available_slots,
                                            avail_by_teacher,
                                            request.ruleset.respect_availability,
                                        ):
                                            block_count += 1
                                            continue
                                        sid_set = {s.slot_id for s in available_slots}
                                        if _teacher_already_booked(
                                            assignment.teacher_id,
                                            current_date,
                                            sid_set,
                                            proposals,
                                            list(enrollments),
                                            assignments_dict,
                                        ):
                                            block_count += 1
                                            continue
                                        # Create individual lessons for the block
                                        for i, slot in enumerate(available_slots):
                                            proposal = GeneratedLesson(
                                                date=current_date,
                                                slot_id=slot.slot_id,
                                                room_id=available_room.room_id,
                                                enrollment_id=enrollment.enrollment_id,
                                                group_id=group.group_id,
                                                group_name=group.name,
                                                teacher_name=f"{teacher.first_name} {teacher.last_name}",
                                                course_name=course.name,
                                                room_number=available_room.number,
                                                start_time=str(slot.start_time),
                                                end_time=str(slot.end_time)
                                            )
                                            proposals.append(proposal)
                                        
                                        # Create block representation using first/last slots of the block
                                        block_start_slot = available_slots[0]
                                        block_end_slot = available_slots[-1]
                                        block = LessonBlock(
                                            date=current_date,
                                            start_slot_id=block_start_slot.slot_id,
                                            end_slot_id=block_end_slot.slot_id,
                                            slot_ids=[s.slot_id for s in available_slots],
                                            room_id=available_room.room_id,
                                            enrollment_id=enrollment.enrollment_id,
                                            group_id=group_id,
                                            teacher_id=assignment.teacher_id,
                                            course_id=assignment.course_id,
                                            group_name=group.name,
                                            teacher_name=f"{teacher.first_name} {teacher.last_name}",
                                            course_name=course.name,
                                            room_number=available_room.number,
                                            start_time=str(block_start_slot.start_time),
                                            end_time=str(block_end_slot.end_time),
                                            block_size=current_block_size
                                        )
                                        blocks.append(block)
                                        
                                        lessons_given += current_block_size
                            
                            block_count += 1
                        else:
                            break  # No available room, stop trying
                    else:
                        break  # No available slots, stop trying

                if lessons_given:
                    placed_iso_week[wk_key] = placed_iso_week.get(wk_key, 0) + lessons_given
        
        # Use timedelta to safely add one day (handles month/year boundaries correctly)
        try:
            logger.debug(f"Incrementing date from {current_date} (type: {type(current_date)})")
            current_date = current_date + timedelta(days=1)
            logger.debug(f"New date: {current_date}")
        except (ValueError, TypeError) as e:
            logger.error(f"Error incrementing date from {current_date} (type: {type(current_date)}): {e}")
            raise ValueError(f"Error incrementing date from {current_date}: {e}") from e
    
    # Calculate stats
    stats = {
        "total_lessons": len(proposals),
        "total_blocks": len(blocks),
        "groups_count": len(groups),
        "teachers_count": len(teachers),
        "rooms_count": len(rooms),
        "time_slots_count": len(slots),
        "enrollments_count": len(enrollments),
        "date_range": f"{request.from_date} - {request.to_date}",
        "generation_time": "0.5s",
        "block_scheduling_enabled": request.ruleset.enable_block_scheduling
    }
    
    return GenerationResult(
        proposals=proposals,
        blocks=blocks,
        stats=stats,
        success=True
    )


def _find_consecutive_slots(
    slots, block_size, group_id, current_date, 
    proposals, blocks, groups_dict, teachers_dict, 
    assignments_dict, courses_dict
):
    """Find consecutive time slots for a block."""
    if not slots or block_size <= 0:
        return []
    
    # Sort slots by start time
    sorted_slots = sorted(slots, key=lambda s: s.start_time)
    
    for i in range(len(sorted_slots) - block_size + 1):
        candidate_slots = sorted_slots[i:i + block_size]
        
        # Check if slots are consecutive
        if _are_consecutive_slots(candidate_slots):
            # Check if any of these slots are already taken
            if not _slots_conflict(candidate_slots, current_date, proposals, blocks, group_id):
                return candidate_slots
    
    return []


def _find_consecutive_slots_from_offset(
    slots, block_size, start_offset, group_id, current_date, 
    proposals, blocks, groups_dict, teachers_dict, 
    assignments_dict, courses_dict
):
    """Find consecutive time slots starting from a specific offset."""
    if not slots or block_size <= 0:
        return []
    
    # Sort slots by start time
    sorted_slots = sorted(slots, key=lambda s: s.start_time)
    
    # Start from the offset and wrap around if needed
    for offset in range(len(sorted_slots)):
        actual_start = (start_offset + offset) % len(sorted_slots)
        
        # Check if we can fit the block starting from this position
        if actual_start + block_size <= len(sorted_slots):
            candidate_slots = sorted_slots[actual_start:actual_start + block_size]
        else:
            # Wrap around - take from start_offset to end, then from beginning
            candidate_slots = sorted_slots[actual_start:] + sorted_slots[:block_size - (len(sorted_slots) - actual_start)]
        
        # Check if slots are consecutive
        if _are_consecutive_slots(candidate_slots):
            # Check if any of these slots are already taken
            if not _slots_conflict(candidate_slots, current_date, proposals, blocks, group_id):
                return candidate_slots
    
    return []

def _find_consecutive_slots_for_group(
    slots, block_size, group_slot_offset, group_id, current_date, 
    proposals, blocks, groups_dict, teachers_dict, 
    assignments_dict, courses_dict
):
    """Find consecutive time slots for a specific group starting from its assigned offset."""
    if not slots or block_size <= 0:
        return []
    
    # Sort slots by start time
    sorted_slots = sorted(slots, key=lambda s: s.start_time)
    
    # Try to find consecutive slots starting from the group's assigned offset
    for offset in range(len(sorted_slots)):
        actual_start = (group_slot_offset + offset) % len(sorted_slots)
        
        # Check if we can fit the block starting from this position
        if actual_start + block_size <= len(sorted_slots):
            candidate_slots = sorted_slots[actual_start:actual_start + block_size]
        else:
            # If we can't fit at the end, try wrapping around
            continue
        
        # Check if slots are consecutive
        if _are_consecutive_slots(candidate_slots):
            # Check if any of these slots are already taken by this group
            if not _slots_conflict_for_group(candidate_slots, current_date, proposals, blocks, group_id):
                return candidate_slots
    
    return []

def _find_available_room_for_group(
    rooms, actual_slots, group_room_offset,
    current_date, proposals, blocks
):
    """Find available room for a group starting from its assigned room offset."""
    if not rooms:
        return None
    
    sorted_rooms = sorted(rooms, key=lambda r: r.room_id)
    
    for offset in range(len(sorted_rooms)):
        room_index = (group_room_offset + offset) % len(sorted_rooms)
        room = sorted_rooms[room_index]
        
        if _room_available_for_slots(room, actual_slots, current_date, proposals):
            return room
    
    return None


def _are_consecutive_slots(slots):
    """Check if slots are consecutive in time (allowing for breaks)."""
    if len(slots) < 2:
        return True
    
    # Sort slots by start time to ensure proper order
    sorted_slots = sorted(slots, key=lambda s: s.start_time)
    
    for i in range(1, len(sorted_slots)):
        # Check if current slot starts after previous ends (allowing for breaks)
        prev_end = sorted_slots[i-1].end_time
        curr_start = sorted_slots[i].start_time
        if curr_start <= prev_end:
            return False
    
    return True


def _slots_conflict(slots, current_date, proposals, blocks, group_id):
    """Check if slots conflict with existing lessons."""
    want = {s.slot_id for s in slots}

    for proposal in proposals:
        if proposal.date == current_date and proposal.slot_id in want:
            return True

    for block in blocks:
        if block.date != current_date or block.group_id != group_id:
            continue
        occupied = set(block.slot_ids) if block.slot_ids else {block.start_slot_id, block.end_slot_id}
        if want & occupied:
            return True

    return False


def _slots_conflict_for_group(slots, current_date, proposals, blocks, group_id):
    """Check if slots conflict with existing lessons for a specific group.
    
    Uses actual slot IDs (not a sequential range) for correct conflict detection.
    """
    slot_ids = {s.slot_id for s in slots}

    for proposal in proposals:
        if (proposal.date == current_date
                and proposal.slot_id in slot_ids
                and proposal.group_id == group_id):
            return True
    
    return False


def _room_available_for_slots(room, actual_slots, current_date, proposals):
    """Check if a room is available for the given time slots.

    Uses explicit slot IDs from actual_slots instead of a range to correctly
    handle non-sequential database IDs.
    """
    slot_ids = {s.slot_id for s in actual_slots}
    for proposal in proposals:
        if (
            proposal.date == current_date
            and proposal.slot_id in slot_ids
            and proposal.room_id == room.room_id
        ):
            return False
    return True


def _find_available_room(rooms, block_slots, current_date, proposals, blocks):
    """Find an available room for the entire block (by explicit slot rows, not ID ranges)."""
    if not rooms or not block_slots:
        return None
    slot_ids = {s.slot_id for s in block_slots}

    for room in rooms:
        if not _room_available_for_slots(room, block_slots, current_date, proposals):
            continue
        conflict = False
        for block in blocks:
            if block.date != current_date or block.room_id != room.room_id:
                continue
            occupied = (
                set(block.slot_ids)
                if block.slot_ids
                else {block.start_slot_id, block.end_slot_id}
            )
            if slot_ids & occupied:
                conflict = True
                break
        if not conflict:
            return room

    return None

def _ortools_generate(
    groups_list, teachers_dict, rooms_list, slots_list,
    enrollments_list, assignments_dict, courses_dict,
    dates_list, ruleset, max_seconds: float = 20.0,
    avail_by_teacher: Optional[Dict[int, List[TeacherAvailability]]] = None,
) -> List[GeneratedLesson]:
    """CP-SAT based generation.  Returns a list of GeneratedLesson proposals.

    Uses pre-loaded plain Python objects so async SQLAlchemy lazy loading
    is never triggered.  Falls back to empty list on any error so the
    caller can use the heuristic instead.
    """
    try:
        from ortools.sat.python import cp_model  # type: ignore

        avail_by_teacher = avail_by_teacher or {}

        model = cp_model.CpModel()
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_seconds

        # Index helpers
        date_idx = {d: i for i, d in enumerate(dates_list)}
        slot_idx = {s.slot_id: i for i, s in enumerate(slots_list)}
        room_idx = {r.room_id: i for i, r in enumerate(rooms_list)}
        enr_idx  = {e.enrollment_id: i for i, e in enumerate(enrollments_list)}

        # Build group_id → group map for capacity checks
        groups_dict = {g.group_id: g for g in groups_list}

        # Create boolean variables: x[enr, d, s, r]
        x = {}
        for e in enrollments_list:
            ei = enr_idx[e.enrollment_id]
            grp = groups_dict.get(e.group_id)
            asgn = assignments_dict.get(e.assignment_id)
            if not grp or not asgn:
                continue
            for di in range(len(dates_list)):
                d = dates_list[di]
                for si, slot in enumerate(slots_list):
                    if not _teacher_slots_allowed(
                        asgn.teacher_id, d, [slot], avail_by_teacher, ruleset.respect_availability
                    ):
                        continue
                    for ri, room in enumerate(rooms_list):
                        # Room capacity check
                        if ruleset.room_capacity_check and grp.size > room.capacity:
                            continue
                        vname = f"x_{ei}_{di}_{si}_{ri}"
                        x[(ei, di, si, ri)] = model.NewBoolVar(vname)

        # Constraint: one lesson per room per (date, slot)
        for di in range(len(dates_list)):
            for si in range(len(slots_list)):
                for ri in range(len(rooms_list)):
                    room_vars = [x[k] for k in x if k[1] == di and k[2] == si and k[3] == ri]
                    if room_vars:
                        model.Add(sum(room_vars) <= 1)

        # Constraint: one lesson per teacher per (date, slot)
        teacher_var_map: Dict = {}
        for e in enrollments_list:
            asgn = assignments_dict.get(e.assignment_id)
            if not asgn:
                continue
            tid = asgn.teacher_id
            ei = enr_idx[e.enrollment_id]
            for di in range(len(dates_list)):
                for si in range(len(slots_list)):
                    for ri in range(len(rooms_list)):
                        key = (ei, di, si, ri)
                        if key in x:
                            teacher_var_map.setdefault((tid, di, si), []).append(x[key])
        for vars_list in teacher_var_map.values():
            if vars_list:
                model.Add(sum(vars_list) <= 1)

        # Constraint: one lesson per group per (date, slot)
        group_var_map: Dict = {}
        for e in enrollments_list:
            ei = enr_idx[e.enrollment_id]
            gid = e.group_id
            for di in range(len(dates_list)):
                for si in range(len(slots_list)):
                    for ri in range(len(rooms_list)):
                        key = (ei, di, si, ri)
                        if key in x:
                            group_var_map.setdefault((gid, di, si), []).append(x[key])
        for vars_list in group_var_map.values():
            if vars_list:
                model.Add(sum(vars_list) <= 1)

        # Constraint: max lessons per day per group
        if ruleset.max_lessons_per_day_group > 0:
            for gid in {e.group_id for e in enrollments_list}:
                for di in range(len(dates_list)):
                    day_vars = [x[k] for k in x if k[1] == di
                                and any(e.group_id == gid and enr_idx[e.enrollment_id] == k[0]
                                        for e in enrollments_list)]
                    if day_vars:
                        model.Add(sum(day_vars) <= ruleset.max_lessons_per_day_group)

        # Objective: maximise scheduled lessons
        model.Maximize(sum(x.values()))

        status = solver.Solve(model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return []

        proposals: List[GeneratedLesson] = []
        for (ei, di, si, ri), var in x.items():
            if solver.Value(var) == 1:
                enr = enrollments_list[ei]
                slot = slots_list[si]
                room = rooms_list[ri]
                asgn = assignments_dict.get(enr.assignment_id)
                grp  = groups_dict.get(enr.group_id)
                if not asgn or not grp:
                    continue
                teacher = teachers_dict.get(asgn.teacher_id)
                course  = courses_dict.get(asgn.course_id)
                if not teacher or not course:
                    continue
                proposals.append(GeneratedLesson(
                    date=dates_list[di],
                    slot_id=slot.slot_id,
                    room_id=room.room_id,
                    enrollment_id=enr.enrollment_id,
                    group_id=grp.group_id,
                    group_name=grp.name,
                    teacher_name=f"{teacher.first_name} {teacher.last_name}",
                    course_name=course.name,
                    room_number=room.number,
                    start_time=str(slot.start_time),
                    end_time=str(slot.end_time),
                ))
        return proposals
    except Exception as exc:
        logger.warning(f"OR-Tools generation failed, using heuristic fallback: {exc}")
        return []


@router.post("/preview")
async def preview_generation(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user_or_demo),
):
    """Start async schedule preview. Returns {job_id}; poll /preview-status/{job_id}."""
    _purge_old_jobs()
    job_id, _ = _new_job()
    background_tasks.add_task(_run_bg_preview, job_id, request, current_user.org_id)
    return {"job_id": job_id}


@router.get("/preview-status/{job_id}")
async def get_preview_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user_or_demo),
):
    """Poll for the result of a preview job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    return {"status": job["status"], "result": job["result"], "error": job["error"]}


@router.post("/run")
async def run_generation(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user_or_demo),
):
    """Start async generation+save. Returns {job_id}; poll /run-status/{job_id}."""
    _purge_old_jobs()
    job_id, _ = _new_job()
    background_tasks.add_task(_run_bg_save, job_id, request, current_user.org_id, current_user.user_id)
    return {"job_id": job_id}


@router.get("/run-status/{job_id}")
async def get_run_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user_or_demo),
):
    """Poll for the result of a run-generation job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    return {"status": job["status"], "result": job["result"], "error": job["error"]}


@router.get("/stats")
async def get_generation_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Get generation statistics."""
    from sqlalchemy import select, func
    
    try:
        # Get counts from database
        groups_count = await db.execute(select(func.count(Group.group_id)).where(Group.org_id == current_user.org_id))
        teachers_count = await db.execute(select(func.count(Teacher.teacher_id)).where(Teacher.org_id == current_user.org_id))
        rooms_count = await db.execute(select(func.count(Room.room_id)).where(Room.org_id == current_user.org_id))
        slots_count = await db.execute(select(func.count(TimeTableSlot.slot_id)).where(TimeTableSlot.org_id == current_user.org_id))
        enrollments_count = await db.execute(select(func.count(Enrollment.enrollment_id)).where(Enrollment.org_id == current_user.org_id))
        
        return {
            "available_groups": groups_count.scalar() or 0,
            "available_teachers": teachers_count.scalar() or 0,
            "available_rooms": rooms_count.scalar() or 0,
            "available_time_slots": slots_count.scalar() or 0,
            "total_enrollments": enrollments_count.scalar() or 0,
            "system_status": "ready"
        }
    except Exception as e:
        return {
            "available_groups": 0,
            "available_teachers": 0,
            "available_rooms": 0,
            "available_time_slots": 0,
            "total_enrollments": 0,
            "system_status": "error",
            "error": str(e)
        }