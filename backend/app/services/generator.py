"""Schedule generation service using OR-Tools CP-SAT."""

import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from ortools.sat.python import cp_model
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models.educational import Enrollment, CourseAssignment, Group, Teacher
from ..models.facilities import TimeTableSlot, Room, TeacherAvailability, Holiday
from ..models.scheduling import LessonInstance, LessonStatus
from ..schemas.generation import GenerationRuleSet, GeneratedLesson, GenerationResult

logger = logging.getLogger(__name__)


@dataclass
class SchedulingData:
    """Container for all scheduling data."""
    enrollments: List[Enrollment]
    time_slots: List[TimeTableSlot]
    rooms: List[Room]
    dates: List[date]
    teacher_availabilities: Dict[int, List[TeacherAvailability]]
    holidays: List[date]
    existing_lessons: List[LessonInstance]


class ScheduleGenerator:
    """Schedule generator using OR-Tools CP-SAT solver."""
    
    def __init__(self, db: AsyncSession, org_id: int):
        self.db = db
        self.org_id = org_id
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
    
    async def generate_preview(
        self,
        term_id: int,
        start_date: date,
        end_date: date,
        ruleset: GenerationRuleSet
    ) -> GenerationResult:
        """Generate schedule preview without persisting to database."""
        
        try:
            # Load scheduling data
            data = await self._load_scheduling_data(term_id, start_date, end_date)
            
            # Build CP-SAT model
            variables = self._build_model(data, ruleset)
            
            # Solve
            status = self.solver.Solve(self.model)
            
            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                proposals = self._extract_solution(variables, data)
                stats = self._calculate_stats(proposals, data)
                
                return GenerationResult(
                    proposals=proposals,
                    stats=stats,
                    success=True
                )
            else:
                return GenerationResult(
                    proposals=[],
                    stats={"solver_status": "infeasible"},
                    conflicts=["No feasible solution found with current constraints"],
                    success=False
                )
                
        except Exception as e:
            logger.error(f"Schedule generation failed: {e}")
            return GenerationResult(
                proposals=[],
                stats={"error": str(e)},
                conflicts=[f"Generation error: {str(e)}"],
                success=False
            )
    
    async def _load_scheduling_data(
        self,
        term_id: int,
        start_date: date,
        end_date: date
    ) -> SchedulingData:
        """Load all data needed for scheduling."""
        
        # Get enrollments for the term
        enrollments_result = await self.db.execute(
            select(Enrollment)
            .join(CourseAssignment)
            .join(Group)
            .join(Teacher)
            .where(Enrollment.org_id == self.org_id)
        )
        enrollments = enrollments_result.scalars().all()
        
        # Get time slots
        slots_result = await self.db.execute(
            select(TimeTableSlot)
            .where(TimeTableSlot.org_id == self.org_id)
            .order_by(TimeTableSlot.start_time)
        )
        time_slots = slots_result.scalars().all()
        
        # Get rooms
        rooms_result = await self.db.execute(
            select(Room)
            .where(and_(Room.org_id == self.org_id, Room.is_active == True))
            .order_by(Room.capacity.desc())
        )
        rooms = rooms_result.scalars().all()
        
        # Generate date range (weekdays only)
        dates = []
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday=0, Sunday=6
                dates.append(current_date)
            current_date += timedelta(days=1)
        
        # Get teacher availabilities
        availabilities_result = await self.db.execute(
            select(TeacherAvailability)
            .where(TeacherAvailability.org_id == self.org_id)
        )
        availabilities = availabilities_result.scalars().all()
        
        teacher_availabilities = {}
        for avail in availabilities:
            if avail.teacher_id not in teacher_availabilities:
                teacher_availabilities[avail.teacher_id] = []
            teacher_availabilities[avail.teacher_id].append(avail)
        
        # Get holidays
        holidays_result = await self.db.execute(
            select(Holiday)
            .where(
                and_(
                    Holiday.org_id == self.org_id,
                    Holiday.date >= start_date,
                    Holiday.date <= end_date
                )
            )
        )
        holidays = [h.date for h in holidays_result.scalars().all()]
        
        # Get existing lessons
        existing_result = await self.db.execute(
            select(LessonInstance)
            .where(
                and_(
                    LessonInstance.org_id == self.org_id,
                    LessonInstance.date >= start_date,
                    LessonInstance.date <= end_date,
                    LessonInstance.status.in_([
                        LessonStatus.PLANNED,
                        LessonStatus.CONFIRMED
                    ])
                )
            )
        )
        existing_lessons = existing_result.scalars().all()
        
        return SchedulingData(
            enrollments=enrollments,
            time_slots=time_slots,
            rooms=rooms,
            dates=dates,
            teacher_availabilities=teacher_availabilities,
            holidays=holidays,
            existing_lessons=existing_lessons
        )
    
    def _build_model(
        self,
        data: SchedulingData,
        ruleset: GenerationRuleSet
    ) -> Dict:
        """Build the CP-SAT model with constraints."""
        
        variables = {}
        
        # Create variables: lesson[enrollment_id, date_idx, slot_idx, room_idx]
        for i, enrollment in enumerate(data.enrollments):
            for d, date_val in enumerate(data.dates):
                for s, slot in enumerate(data.time_slots):
                    for r, room in enumerate(data.rooms):
                        var_name = f"lesson_{enrollment.enrollment_id}_{d}_{s}_{r}"
                        variables[var_name] = self.model.NewBoolVar(var_name)
        
        # Add hard constraints
        self._add_hard_constraints(variables, data, ruleset)
        
        # Add soft constraints to objective
        self._add_soft_constraints(variables, data, ruleset)
        
        return variables
    
    def _add_hard_constraints(
        self,
        variables: Dict,
        data: SchedulingData,
        ruleset: GenerationRuleSet
    ):
        """Add hard constraints to the model."""
        
        # 1. Room capacity constraint
        if ruleset.room_capacity_check:
            for i, enrollment in enumerate(data.enrollments):
                for r, room in enumerate(data.rooms):
                    if enrollment.group.size > room.capacity:
                        # This enrollment cannot use this room
                        for d in range(len(data.dates)):
                            for s in range(len(data.time_slots)):
                                var_name = f"lesson_{enrollment.enrollment_id}_{d}_{s}_{r}"
                                if var_name in variables:
                                    self.model.Add(variables[var_name] == 0)
        
        # 2. Room uniqueness - only one lesson per room per time slot
        for d in range(len(data.dates)):
            for s in range(len(data.time_slots)):
                for r in range(len(data.rooms)):
                    room_vars = []
                    for enrollment in data.enrollments:
                        var_name = f"lesson_{enrollment.enrollment_id}_{d}_{s}_{r}"
                        if var_name in variables:
                            room_vars.append(variables[var_name])
                    
                    if room_vars:
                        self.model.Add(sum(room_vars) <= 1)
        
        # 3. Teacher uniqueness - only one lesson per teacher per time slot
        teacher_lessons = {}
        for i, enrollment in enumerate(data.enrollments):
            teacher_id = enrollment.assignment.teacher_id
            if teacher_id not in teacher_lessons:
                teacher_lessons[teacher_id] = []
            
            for d in range(len(data.dates)):
                for s in range(len(data.time_slots)):
                    for r in range(len(data.rooms)):
                        var_name = f"lesson_{enrollment.enrollment_id}_{d}_{s}_{r}"
                        if var_name in variables:
                            teacher_lessons[teacher_id].append((d, s, variables[var_name]))
        
        for teacher_id, lessons in teacher_lessons.items():
            for d in range(len(data.dates)):
                for s in range(len(data.time_slots)):
                    slot_vars = [var for day, slot, var in lessons if day == d and slot == s]
                    if slot_vars:
                        self.model.Add(sum(slot_vars) <= 1)
        
        # 4. Group uniqueness - only one lesson per group per time slot
        group_lessons = {}
        for i, enrollment in enumerate(data.enrollments):
            group_id = enrollment.group_id
            if group_id not in group_lessons:
                group_lessons[group_id] = []
            
            for d in range(len(data.dates)):
                for s in range(len(data.time_slots)):
                    for r in range(len(data.rooms)):
                        var_name = f"lesson_{enrollment.enrollment_id}_{d}_{s}_{r}"
                        if var_name in variables:
                            group_lessons[group_id].append((d, s, variables[var_name]))
        
        for group_id, lessons in group_lessons.items():
            for d in range(len(data.dates)):
                for s in range(len(data.time_slots)):
                    slot_vars = [var for day, slot, var in lessons if day == d and slot == s]
                    if slot_vars:
                        self.model.Add(sum(slot_vars) <= 1)
        
        # 5. Teacher availability constraints
        if ruleset.respect_availability:
            for i, enrollment in enumerate(data.enrollments):
                teacher_id = enrollment.assignment.teacher_id
                if teacher_id in data.teacher_availabilities:
                    for d, date_val in enumerate(data.dates):
                        weekday = date_val.weekday() + 1  # CP-SAT uses 1-based weekdays
                        
                        for s, slot in enumerate(data.time_slots):
                            # Check if teacher is available at this time
                            available = False
                            for avail in data.teacher_availabilities[teacher_id]:
                                if (avail.weekday == weekday and 
                                    avail.start_time <= slot.start_time and
                                    avail.end_time >= slot.end_time and
                                    avail.is_available):
                                    available = True
                                    break
                            
                            if not available:
                                # Teacher not available - prevent scheduling
                                for r in range(len(data.rooms)):
                                    var_name = f"lesson_{enrollment.enrollment_id}_{d}_{s}_{r}"
                                    if var_name in variables:
                                        self.model.Add(variables[var_name] == 0)
        
        # 6. Holiday constraints
        for d, date_val in enumerate(data.dates):
            if date_val in data.holidays:
                # No lessons on holidays
                for enrollment in data.enrollments:
                    for s in range(len(data.time_slots)):
                        for r in range(len(data.rooms)):
                            var_name = f"lesson_{enrollment.enrollment_id}_{d}_{s}_{r}"
                            if var_name in variables:
                                self.model.Add(variables[var_name] == 0)
        
        # 7. Max lessons per day constraints
        if ruleset.max_lessons_per_day_group > 0:
            for group_id in group_lessons:
                for d in range(len(data.dates)):
                    day_vars = [var for day, slot, var in group_lessons[group_id] if day == d]
                    if day_vars:
                        self.model.Add(sum(day_vars) <= ruleset.max_lessons_per_day_group)
        
        if ruleset.max_lessons_per_day_teacher > 0:
            for teacher_id in teacher_lessons:
                for d in range(len(data.dates)):
                    day_vars = [var for day, slot, var in teacher_lessons[teacher_id] if day == d]
                    if day_vars:
                        self.model.Add(sum(day_vars) <= ruleset.max_lessons_per_day_teacher)
    
    def _add_soft_constraints(
        self,
        variables: Dict,
        data: SchedulingData,
        ruleset: GenerationRuleSet
    ):
        """Add soft constraints to the objective function."""
        
        objective_terms = []
        
        # Maximize scheduled lessons (primary objective)
        for var in variables.values():
            objective_terms.append(var * 100)  # High weight for scheduling lessons
        
        # Add other soft constraint penalties here
        # (simplified for brevity - can be extended with gap minimization, etc.)
        
        if objective_terms:
            self.model.Maximize(sum(objective_terms))
    
    def _extract_solution(
        self,
        variables: Dict,
        data: SchedulingData
    ) -> List[GeneratedLesson]:
        """Extract solution from solved model."""
        
        proposals = []
        
        for var_name, var in variables.items():
            if self.solver.Value(var) == 1:
                # Parse variable name: lesson_{enrollment_id}_{d}_{s}_{r}
                parts = var_name.split('_')
                enrollment_id = int(parts[1])
                date_idx = int(parts[2])
                slot_idx = int(parts[3])
                room_idx = int(parts[4])
                
                proposals.append(GeneratedLesson(
                    date=data.dates[date_idx],
                    slot_id=data.time_slots[slot_idx].slot_id,
                    room_id=data.rooms[room_idx].room_id,
                    enrollment_id=enrollment_id,
                    score=1.0  # Could be calculated based on soft constraints
                ))
        
        return proposals
    
    def _calculate_stats(
        self,
        proposals: List[GeneratedLesson],
        data: SchedulingData
    ) -> Dict:
        """Calculate generation statistics."""
        
        return {
            "total_proposals": len(proposals),
            "solver_time": self.solver.WallTime(),
            "enrollments_count": len(data.enrollments),
            "dates_count": len(data.dates),
            "time_slots_count": len(data.time_slots),
            "rooms_count": len(data.rooms)
        }
