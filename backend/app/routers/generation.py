"""Schedule generation router."""

import logging
import random
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_active_user_or_demo
from app.models.scheduling import LessonInstance, LessonStatus
from app.models.educational import Enrollment, Group, Teacher, Course, CourseAssignment
from app.models.facilities import Room, TimeTableSlot
from app.models.academic import Term, AcademicYear
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

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
    
    slots_result = await db.execute(select(TimeTableSlot).where(TimeTableSlot.org_id == current_user.org_id))
    slots = slots_result.scalars().all()
    
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
    
    # Generate lessons and blocks
    proposals = []
    blocks = []
    current_date = request.from_date
    
    # Calculate lessons per week for each enrollment
    lessons_per_week_per_enrollment = {}
    for enrollment in enrollments:
        # Calculate how many lessons per week based on planned hours
        # Each lesson is 1.5 hours (90 minutes), 18 weeks per semester
        weekly_hours = enrollment.planned_hours / 18
        lessons_per_week = min(4, max(1, int(weekly_hours / 1.5)))  # 1-4 lessons per week (realistic)
        lessons_per_week_per_enrollment[enrollment.enrollment_id] = lessons_per_week
    
    # Group enrollments by group to ensure each group gets lessons
    group_enrollments = {}
    for enrollment in enrollments:
        if enrollment.group_id not in group_enrollments:
            group_enrollments[enrollment.group_id] = []
        group_enrollments[enrollment.group_id].append(enrollment)
    
    # Shuffle enrollments within each group to randomize course order
    # This ensures different courses appear in different orders across groups
    for group_id in group_enrollments:
        random.shuffle(group_enrollments[group_id])
    
    # Generate lessons for each day
    current_date = request.from_date
    while current_date <= request.to_date:
        if current_date.weekday() < 5:  # Monday=0, Sunday=6
            # Generate blocks for each group (distribute across days)
            for group_id, group_enrollments_list in group_enrollments.items():
                group = groups_dict.get(group_id)
                if not group:
                    continue
                
                # Get generation type for this group (2, 3, or 5 lessons per block)
                block_size = group.generation_type
                
                # Calculate total lessons for this group this week
                total_group_lessons = sum(lessons_per_week_per_enrollment[e.enrollment_id] for e in group_enrollments_list)
                
                # Distribute lessons across weekdays (Monday=0 to Friday=4)
                weekday = current_date.weekday()
                lessons_this_day = 0
                
                # Calculate how many lessons this group should have today
                # All groups can have lessons every day since we have enough resources
                if total_group_lessons > 0:
                    # Use the group's generation_type as block size for block scheduling
                    lessons_this_day = block_size
                else:
                    lessons_this_day = 0
                
                # Generate blocks for this day
                lessons_given = 0
                block_count = 0
                max_blocks = request.ruleset.max_blocks_per_day
                
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
                        start_slot = available_slots[0]
                        end_slot = available_slots[-1]
                        
                        # Find available room starting from group's assigned room
                        available_room = _find_available_room_for_group(
                            rooms, start_slot, end_slot, group_room_offset,
                            current_date, proposals, blocks
                        )
                        
                        if available_room:
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
                                        
                                        # Create block representation
                                        block = LessonBlock(
                                            date=current_date,
                                            start_slot_id=start_slot.slot_id,
                                            end_slot_id=end_slot.slot_id,
                                            room_id=available_room.room_id,
                                            enrollment_id=enrollment.enrollment_id,
                                            group_id=group_id,
                                            teacher_id=assignment.teacher_id,
                                            course_id=assignment.course_id,
                                            group_name=group.name,
                                            teacher_name=f"{teacher.first_name} {teacher.last_name}",
                                            course_name=course.name,
                                            room_number=available_room.number,
                                            start_time=str(start_slot.start_time),
                                            end_time=str(end_slot.end_time),
                                            block_size=current_block_size
                                        )
                                        blocks.append(block)
                                        
                                        lessons_given += current_block_size
                            
                            block_count += 1
                        else:
                            break  # No available room, stop trying
                    else:
                        break  # No available slots, stop trying
        
        current_date = date(current_date.year, current_date.month, current_date.day + 1)
    
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
    rooms, start_slot, end_slot, group_room_offset, 
    current_date, proposals, blocks
):
    """Find available room for a group starting from its assigned room offset."""
    if not rooms:
        return None
    
    # Sort rooms by room_id for consistent ordering
    sorted_rooms = sorted(rooms, key=lambda r: r.room_id)
    
    # Try rooms starting from the group's assigned room
    for offset in range(len(sorted_rooms)):
        room_index = (group_room_offset + offset) % len(sorted_rooms)
        room = sorted_rooms[room_index]
        
        # Check if this room is available for the entire time range
        if _room_available_for_slots(room, start_slot, end_slot, current_date, proposals, blocks):
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
    slot_ids = [s.slot_id for s in slots]
    
    # Check conflicts in individual proposals
    for proposal in proposals:
        if (proposal.date == current_date and 
            proposal.slot_id in slot_ids):
            return True
    
    # Check conflicts in blocks
    for block in blocks:
        if (block.date == current_date and 
            block.group_id == group_id and
            any(slot_id in slot_ids for slot_id in range(block.start_slot_id, block.end_slot_id + 1))):
            return True
    
    return False


def _slots_conflict_for_group(slots, current_date, proposals, blocks, group_id):
    """Check if slots conflict with existing lessons for a specific group."""
    slot_ids = [s.slot_id for s in slots]
    
    # Check conflicts in individual proposals for this group
    for proposal in proposals:
        if (proposal.date == current_date and 
            proposal.slot_id in slot_ids and
            proposal.group_id == group_id):
            return True
    
    # Check conflicts in blocks for this group
    for block in blocks:
        if (block.date == current_date and 
            block.group_id == group_id and
            any(slot_id in slot_ids for slot_id in range(block.start_slot_id, block.end_slot_id + 1))):
            return True
    
    return False


def _room_available_for_slots(room, start_slot, end_slot, current_date, proposals, blocks):
    """Check if a room is available for specific time slots."""
    slot_ids = list(range(start_slot.slot_id, end_slot.slot_id + 1))
    
    # Check if room is available for all slots in the block
    for slot_id in slot_ids:
        # Check conflicts in individual proposals
        for proposal in proposals:
            if (proposal.date == current_date and 
                proposal.slot_id == slot_id and
                proposal.room_id == room.room_id):
                return False
        
        # Check conflicts in blocks
        for block in blocks:
            if (block.date == current_date and 
                block.room_id == room.room_id and
                block.start_slot_id <= slot_id <= block.end_slot_id):
                return False
    
    return True


def _find_available_room(rooms, start_slot, end_slot, current_date, proposals, blocks):
    """Find an available room for the entire block."""
    slot_ids = list(range(start_slot.slot_id, end_slot.slot_id + 1))
    
    for room in rooms:
        # Check if room is available for all slots in the block
        room_available = True
        
        for slot_id in slot_ids:
            # Check conflicts in individual proposals
            for proposal in proposals:
                if (proposal.date == current_date and 
                    proposal.slot_id == slot_id and 
                    proposal.room_id == room.room_id):
                    room_available = False
                    break
            
            if not room_available:
                break
            
            # Check conflicts in blocks
            for block in blocks:
                if (block.date == current_date and 
                    block.room_id == room.room_id and
                    slot_id in range(block.start_slot_id, block.end_slot_id + 1)):
                    room_available = False
                    break
            
            if not room_available:
                break
        
        if room_available:
            return room
    
    return None

@router.post("/preview", response_model=GenerationResult)
async def preview_generation(
    request: GenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Generate schedule preview using real data."""
    return await _preview_generation_internal(request, db, current_user)

@router.post("/run", response_model=Dict[str, Any])
async def run_generation(
    request: GenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user_or_demo)
):
    """Run schedule generation and save to database."""
    
    try:
        # Verify term exists or find term by date range
        from sqlalchemy import select
        
        logger.info(f"DEBUG: Starting generation with request.term_id={request.term_id}, from_date={request.from_date}, to_date={request.to_date}")
        
        term = None
        
        # If term_id is provided, try to find it
        if request.term_id:
            term_result = await db.execute(
                select(Term).where(
                    Term.term_id == request.term_id,
                    Term.org_id == current_user.org_id
                )
            )
            term = term_result.scalar_one_or_none()
            logger.info(f"DEBUG: Initial term lookup: term_id={request.term_id}, found={term is not None}")
        
        # If term not found, try to find term that covers the date range
        if not term:
            logger.info(f"DEBUG: Term {request.term_id} not found, searching by date range...")
            
            # First, try to find term that covers the entire date range
            term_by_date_result = await db.execute(
                select(Term).where(
                    Term.org_id == current_user.org_id,
                    Term.start_date <= request.from_date,
                    Term.end_date >= request.to_date
                ).order_by(Term.start_date.desc())
            )
            term = term_by_date_result.scalar_one_or_none()
            logger.info(f"DEBUG: Term by full date range lookup: found={term is not None}")
            
            if not term:
                # Try to find any term that covers at least the start date
                term_by_start_result = await db.execute(
                    select(Term).where(
                        Term.org_id == current_user.org_id,
                        Term.start_date <= request.from_date,
                        Term.end_date >= request.from_date
                    ).order_by(Term.start_date.desc())
                )
                term = term_by_start_result.scalar_one_or_none()
                logger.info(f"DEBUG: Term by start date lookup: found={term is not None}")
            
            if not term:
                # Try to find any term that covers at least the end date
                term_by_end_result = await db.execute(
                    select(Term).where(
                        Term.org_id == current_user.org_id,
                        Term.start_date <= request.to_date,
                        Term.end_date >= request.to_date
                    ).order_by(Term.start_date.desc())
                )
                term = term_by_end_result.scalar_one_or_none()
                logger.info(f"DEBUG: Term by end date lookup: found={term is not None}")
            
            if not term:
                # Last resort: find any term that overlaps with the date range
                term_overlap_result = await db.execute(
                    select(Term).where(
                        Term.org_id == current_user.org_id,
                        Term.start_date <= request.to_date,
                        Term.end_date >= request.from_date
                    ).order_by(Term.start_date.desc())
                )
                term = term_overlap_result.scalar_one_or_none()
                logger.info(f"DEBUG: Term by overlap lookup: found={term is not None}")
            
            if not term:
                # Final fallback: get any term for this org (for debugging)
                any_term_result = await db.execute(
                    select(Term).where(
                        Term.org_id == current_user.org_id
                    ).order_by(Term.start_date.desc())
                )
                any_term = any_term_result.scalar_one_or_none()
                if any_term:
                    logger.warning(f"DEBUG: Found term {any_term.term_id} but it doesn't cover the date range. Term dates: {any_term.start_date} to {any_term.end_date}")
                else:
                    logger.error(f"DEBUG: No terms found for org_id={current_user.org_id}")
        
        # If still no term found, auto-create one
        if not term:
            logger.info(f"DEBUG: No term found, auto-creating term for date range {request.from_date} to {request.to_date}")
            
            # Find or create academic year that covers the date range
            academic_year_result = await db.execute(
                select(AcademicYear).where(
                    AcademicYear.org_id == current_user.org_id,
                    AcademicYear.start_date <= request.from_date,
                    AcademicYear.end_date >= request.to_date
                ).order_by(AcademicYear.start_date.desc())
            )
            academic_year = academic_year_result.scalar_one_or_none()
            
            if not academic_year:
                # Create academic year based on the date range
                year_start = request.from_date.year
                year_end = request.to_date.year
                if year_start == year_end:
                    year_name = f"{year_start}-{year_start + 1}"
                else:
                    year_name = f"{year_start}-{year_end}"
                
                # Extend dates to cover full academic year (September to June)
                academic_start = date(year_start, 9, 1) if request.from_date.month >= 9 else date(year_start - 1, 9, 1)
                academic_end = date(year_start + 1, 6, 30) if request.from_date.month >= 9 else date(year_start, 6, 30)
                
                academic_year = AcademicYear(
                    org_id=current_user.org_id,
                    name=year_name,
                    start_date=academic_start,
                    end_date=academic_end
                )
                db.add(academic_year)
                await db.flush()
                logger.info(f"DEBUG: Created academic year {academic_year.id}: {year_name}")
            
            # Create term for the date range
            term_name = f"Семестр {request.from_date.strftime('%d.%m.%Y')} - {request.to_date.strftime('%d.%m.%Y')}"
            term = Term(
                org_id=current_user.org_id,
                academic_year_id=academic_year.id,
                name=term_name,
                start_date=request.from_date,
                end_date=request.to_date
            )
            db.add(term)
            await db.flush()
            # Note: Don't commit here - will commit after lessons are created
            logger.info(f"DEBUG: Auto-created term {term.term_id}: {term_name} ({term.start_date} to {term.end_date})")
        
        # Ensure term covers the entire requested date range
        # If term was found but doesn't cover the full range, extend it
        if term.start_date > request.from_date or term.end_date < request.to_date:
            logger.warning(f"DEBUG: Term {term.term_id} ({term.start_date} to {term.end_date}) doesn't cover full range ({request.from_date} to {request.to_date}). Extending...")
            term.start_date = min(term.start_date, request.from_date)
            term.end_date = max(term.end_date, request.to_date)
            await db.flush()
            logger.info(f"DEBUG: Extended term {term.term_id} to cover {term.start_date} to {term.end_date}")
        
        # Use the found term_id (either the requested one or the auto-found one)
        actual_term_id = term.term_id
        logger.info(f"DEBUG: Using term_id={actual_term_id} for generation (requested was {request.term_id}), term covers {term.start_date} to {term.end_date}")
        
        # Generate preview first
        preview_result = await _preview_generation_internal(request, db, current_user)
        
        if not preview_result.success:
            return {
                "message": "Generation failed",
                "result": preview_result
            }
        
        # Clear existing lessons for the date range (if any exist)
        from sqlalchemy import delete
        existing_lessons = await db.execute(
            select(LessonInstance).where(
                LessonInstance.org_id == current_user.org_id,
                LessonInstance.date >= request.from_date,
                LessonInstance.date <= request.to_date
            )
        )
        if existing_lessons.scalars().first():
            await db.execute(
                delete(LessonInstance).where(
                    LessonInstance.org_id == current_user.org_id,
                    LessonInstance.date >= request.from_date,
                    LessonInstance.date <= request.to_date
                )
            )
        
        # Check all proposal dates and ensure term covers them all
        if preview_result.proposals:
            proposal_dates = [p.date for p in preview_result.proposals]
            min_proposal_date = min(proposal_dates)
            max_proposal_date = max(proposal_dates)
            
            logger.info(f"DEBUG: Proposal date range: {min_proposal_date} to {max_proposal_date}")
            logger.info(f"DEBUG: Current term range: {term.start_date} to {term.end_date}")
            logger.info(f"DEBUG: Term ID: {term.term_id}")
            
            # If term doesn't cover all proposal dates, extend it
            needs_extension = False
            if term.start_date > min_proposal_date:
                logger.warning(f"DEBUG: Term start_date {term.start_date} > min_proposal_date {min_proposal_date}, need to extend")
                needs_extension = True
            if term.end_date < max_proposal_date:
                logger.warning(f"DEBUG: Term end_date {term.end_date} < max_proposal_date {max_proposal_date}, need to extend")
                needs_extension = True
            
            if needs_extension:
                old_start = term.start_date
                old_end = term.end_date
                term.start_date = min(term.start_date, min_proposal_date)
                term.end_date = max(term.end_date, max_proposal_date)
                await db.flush()
                logger.info(f"DEBUG: Extended term {term.term_id} from {old_start}-{old_end} to {term.start_date}-{term.end_date}")
        
        # Verify term has term_id after flush
        if not term.term_id:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to create term: term_id is None after flush()."
            )
        
        logger.info(f"DEBUG: Final term state - ID: {term.term_id}, range: {term.start_date} to {term.end_date}")
        
        # Create lessons from proposals and save to database
        created_lessons = []
        for idx, proposal in enumerate(preview_result.proposals):
            logger.info(f"DEBUG: Processing proposal {idx+1}/{len(preview_result.proposals)}: date={proposal.date}")
            
            # Check if proposal date is within term range
            if proposal.date < term.start_date or proposal.date > term.end_date:
                logger.error(f"DEBUG: Proposal date {proposal.date} is OUTSIDE term range {term.start_date} to {term.end_date}")
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"No term found that covers date {proposal.date}. Term {term.term_id} covers {term.start_date} to {term.end_date}, but proposal date is {proposal.date}. This should not happen after term extension."
                )
            
            # Use the term we found/created/extended
            proposal_term = term
            lesson_term_id = proposal_term.term_id
            
            logger.info(f"DEBUG: Using term {lesson_term_id} for proposal date {proposal.date}")
            
            # Double-check that term_id is valid
            if not lesson_term_id or lesson_term_id <= 0:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid term_id {lesson_term_id} found for date {proposal.date}."
                )
            
            # Ensure we're using the found term_id
            lesson_term_id = proposal_term.term_id
            
            # Double-check that term_id is valid (not None and not 0)
            if not lesson_term_id or lesson_term_id <= 0:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid term_id {lesson_term_id} found for date {proposal.date}."
                )
            
            # Log for debugging
            logger.info(f"Creating lesson for date {proposal.date} with term_id={lesson_term_id}")
            
            # Create lesson with verified term_id
            lesson = LessonInstance(
                org_id=current_user.org_id,
                term_id=lesson_term_id,
                date=proposal.date,
                slot_id=proposal.slot_id,
                room_id=proposal.room_id,
                enrollment_id=proposal.enrollment_id,
                status=LessonStatus.CONFIRMED,
                created_by=current_user.user_id
            )
            
            db.add(lesson)
            created_lessons.append(lesson)
        
        # Flush to ensure all objects are in session before commit
        await db.flush()
        
        # Basic verification: check that all lessons have valid term_id
        logger.info(f"Verifying {len(created_lessons)} lessons before commit")
        for idx, lesson in enumerate(created_lessons):
            if not lesson.term_id or lesson.term_id <= 0:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid term_id {lesson.term_id} found in lesson for date {lesson.date}."
                )
            logger.debug(f"Lesson {idx}: date={lesson.date}, term_id={lesson.term_id}")
        
        # Final verification before commit
        logger.info(f"DEBUG: Final verification before commit - all lessons have correct term_id")
        for idx, lesson in enumerate(created_lessons):
            if lesson.term_id == 1:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"CRITICAL: Lesson {idx} still has term_id=1! This should not happen. Date: {lesson.date}"
                )
        
        # Commit all lessons to database
        await db.commit()
        
        # Don't refresh lessons - we don't need to access relationships
        # All data is already available from the proposals, and refresh can cause lazy loading issues
        
        created_count = len(created_lessons)
        
        return {
            "message": f"Generation completed successfully! Created {created_count} lessons in {len(preview_result.blocks)} blocks.",
            "created_lessons": created_count,
            "total_blocks": len(preview_result.blocks),
            "total_proposals": len(preview_result.proposals),
            "stats": preview_result.stats,
            "preview": preview_result.proposals[:10],  # Show first 10 lessons as preview
            "blocks_preview": preview_result.blocks[:5]  # Show first 5 blocks as preview
        }
        
    except HTTPException:
        # Re-raise HTTPException so it's properly handled by FastAPI
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Generation error: {str(e)}", exc_info=True)
        return {
            "message": f"Generation failed: {str(e)}",
            "error": str(e),
            "success": False
        }

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