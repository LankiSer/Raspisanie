"""Schedule generation router."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_active_user_or_demo
from app.models.scheduling import LessonInstance, LessonStatus
from app.models.educational import Enrollment, Group, Teacher, Course, CourseAssignment
from app.models.facilities import Room, TimeTableSlot
from app.models.user import User

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
    term_id: int
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
                            # Choose one enrollment for this block (rotate between them)
                            if group_enrollments_list:
                                enrollment_index = block_count % len(group_enrollments_list)
                                enrollment = group_enrollments_list[enrollment_index]
                                
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
        # Generate preview first
        preview_result = await _preview_generation_internal(request, db, current_user)
        
        if not preview_result.success:
            return {
                "message": "Generation failed",
                "result": preview_result
            }
        
        # Clear existing lessons for the date range (if any exist)
        from sqlalchemy import delete, select
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
        
        # Create lessons from proposals and save to database
        created_lessons = []
        for proposal in preview_result.proposals:
            lesson = LessonInstance(
                org_id=current_user.org_id,
                term_id=request.term_id,
                date=proposal.date,
                slot_id=proposal.slot_id,
                room_id=proposal.room_id,
                enrollment_id=proposal.enrollment_id,
                status=LessonStatus.CONFIRMED,
                created_by=current_user.user_id
            )
            db.add(lesson)
            created_lessons.append(lesson)
        
        # Commit all lessons to database
        await db.commit()
        
        # Refresh lessons to get their IDs
        for lesson in created_lessons:
            await db.refresh(lesson)
        
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
        
    except Exception as e:
        await db.rollback()
        print(f"Generation error: {str(e)}")
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