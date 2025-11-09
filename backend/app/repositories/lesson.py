"""Lesson repository."""

from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from .base import BaseRepository
from ..models.scheduling import LessonInstance, LessonStatus
from ..models.educational import Enrollment, CourseAssignment, Group, Teacher, Course
from ..models.facilities import Room, TimeTableSlot


class LessonRepository(BaseRepository[LessonInstance]):
    """Lesson repository."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, LessonInstance)
    
    async def get_by_id(self, lesson_id: int) -> Optional[LessonInstance]:
        """Get lesson by ID with all related data."""
        result = await self.db.execute(
            select(LessonInstance)
            .options(
                joinedload(LessonInstance.enrollment)
                .joinedload(Enrollment.assignment)
                .joinedload(CourseAssignment.course),
                joinedload(LessonInstance.enrollment)
                .joinedload(Enrollment.assignment)
                .joinedload(CourseAssignment.teacher),
                joinedload(LessonInstance.enrollment)
                .joinedload(Enrollment.group),
                joinedload(LessonInstance.room),
                joinedload(LessonInstance.time_slot),
                joinedload(LessonInstance.term)
            )
            .where(LessonInstance.lesson_id == lesson_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_date_range(
        self,
        org_id: int,
        start_date: date,
        end_date: date,
        group_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        room_id: Optional[int] = None
    ) -> List[LessonInstance]:
        """Get lessons by date range with optional filters."""
        query = (
            select(LessonInstance)
            .options(
                joinedload(LessonInstance.enrollment)
                .joinedload(Enrollment.assignment)
                .joinedload(CourseAssignment.course),
                joinedload(LessonInstance.enrollment)
                .joinedload(Enrollment.assignment)
                .joinedload(CourseAssignment.teacher),
                joinedload(LessonInstance.enrollment)
                .joinedload(Enrollment.group),
                joinedload(LessonInstance.room),
                joinedload(LessonInstance.time_slot)
            )
            .where(
                and_(
                    LessonInstance.org_id == org_id,
                    LessonInstance.date >= start_date,
                    LessonInstance.date <= end_date
                )
            )
        )
        
        # Add filters
        if group_id:
            query = query.join(Enrollment).where(Enrollment.group_id == group_id)
        
        if teacher_id:
            query = query.join(Enrollment).join(CourseAssignment).where(
                CourseAssignment.teacher_id == teacher_id
            )
        
        if room_id:
            query = query.where(LessonInstance.room_id == room_id)
        
        # Order by date and time slot
        query = query.order_by(
            LessonInstance.date,
            LessonInstance.slot_id
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_day(
        self,
        org_id: int,
        date: date,
        group_id: Optional[int] = None,
        teacher_id: Optional[int] = None
    ) -> List[LessonInstance]:
        """Get lessons for a specific day."""
        return await self.get_by_date_range(
            org_id, date, date, group_id, teacher_id
        )
    
    async def check_conflicts(
        self,
        org_id: int,
        date: date,
        slot_id: int,
        enrollment_id: int,
        room_id: Optional[int] = None,
        exclude_lesson_id: Optional[int] = None
    ) -> List[str]:
        """Check for scheduling conflicts."""
        conflicts = []
        
        # Base query
        base_query = select(LessonInstance).where(
            and_(
                LessonInstance.org_id == org_id,
                LessonInstance.date == date,
                LessonInstance.slot_id == slot_id,
                LessonInstance.status.in_([
                    LessonStatus.PLANNED,
                    LessonStatus.CONFIRMED
                ])
            )
        )
        
        if exclude_lesson_id:
            base_query = base_query.where(
                LessonInstance.lesson_id != exclude_lesson_id
            )
        
        # Check room conflict
        if room_id:
            room_conflict = await self.db.execute(
                base_query.where(LessonInstance.room_id == room_id)
            )
            if room_conflict.scalar_one_or_none():
                conflicts.append("Room is already booked for this time slot")
        
        # Check teacher conflict
        enrollment_result = await self.db.execute(
            select(Enrollment)
            .join(CourseAssignment)
            .where(Enrollment.enrollment_id == enrollment_id)
        )
        enrollment = enrollment_result.scalar_one_or_none()
        
        if enrollment:
            teacher_conflict = await self.db.execute(
                base_query
                .join(Enrollment)
                .join(CourseAssignment)
                .where(CourseAssignment.teacher_id == enrollment.assignment.teacher_id)
            )
            if teacher_conflict.scalar_one_or_none():
                conflicts.append("Teacher has another lesson at this time")
            
            # Check group conflict
            group_conflict = await self.db.execute(
                base_query
                .join(Enrollment)
                .where(Enrollment.group_id == enrollment.group_id)
            )
            if group_conflict.scalar_one_or_none():
                conflicts.append("Group has another lesson at this time")
        
        return conflicts
    
    async def get_teacher_workload(
        self,
        org_id: int,
        teacher_id: int,
        start_date: date,
        end_date: date
    ) -> dict:
        """Get teacher workload statistics."""
        result = await self.db.execute(
            select(LessonInstance)
            .join(Enrollment)
            .join(CourseAssignment)
            .where(
                and_(
                    LessonInstance.org_id == org_id,
                    CourseAssignment.teacher_id == teacher_id,
                    LessonInstance.date >= start_date,
                    LessonInstance.date <= end_date,
                    LessonInstance.status.in_([
                        LessonStatus.PLANNED,
                        LessonStatus.CONFIRMED,
                        LessonStatus.COMPLETED
                    ])
                )
            )
        )
        lessons = result.scalars().all()
        
        return {
            "total_lessons": len(lessons),
            "by_status": {
                status.value: len([l for l in lessons if l.status == status])
                for status in LessonStatus
            },
            "by_date": {}  # Can be extended with daily breakdown
        }
    
    async def get_group_workload(
        self,
        org_id: int,
        group_id: int,
        start_date: date,
        end_date: date
    ) -> dict:
        """Get group workload statistics."""
        result = await self.db.execute(
            select(LessonInstance)
            .join(Enrollment)
            .where(
                and_(
                    LessonInstance.org_id == org_id,
                    Enrollment.group_id == group_id,
                    LessonInstance.date >= start_date,
                    LessonInstance.date <= end_date,
                    LessonInstance.status.in_([
                        LessonStatus.PLANNED,
                        LessonStatus.CONFIRMED,
                        LessonStatus.COMPLETED
                    ])
                )
            )
        )
        lessons = result.scalars().all()
        
        return {
            "total_lessons": len(lessons),
            "by_status": {
                status.value: len([l for l in lessons if l.status == status])
                for status in LessonStatus
            }
        }
