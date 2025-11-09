"""Schedule generation schemas."""

from datetime import date
from typing import Optional, Dict, List, Any
from pydantic import BaseModel
from ..models.scheduling import GenerationScope


class SoftWeights(BaseModel):
    """Soft constraint weights for optimization."""
    minimize_gaps_group: float = 1.0
    minimize_gaps_teacher: float = 1.0
    balance_days: float = 1.0
    preferred_rooms: float = 0.5


class GenerationRuleSet(BaseModel):
    """Rule set for schedule generation."""
    # Hard constraints
    respect_availability: bool = True
    max_lessons_per_day_group: int = 6
    max_lessons_per_day_teacher: int = 8
    room_capacity_check: bool = True
    
    # Block scheduling constraints
    enable_block_scheduling: bool = True
    max_blocks_per_day: int = 2  # Maximum number of lesson blocks per day
    min_gap_between_blocks: int = 1  # Minimum gap in time slots between blocks
    
    # Soft constraints
    soft_weights: SoftWeights = SoftWeights()
    
    # Optional features (can be implemented later)
    even_odd_weeks: bool = False
    preferred_time_patterns: Dict[str, List[int]] = {}


class GenerationPreviewRequest(BaseModel):
    """Preview generation request schema."""
    org_id: int
    term_id: int
    scope: GenerationScope
    from_date: date
    to_date: date
    ruleset: GenerationRuleSet


class GenerationRunRequest(BaseModel):
    """Run generation request schema."""
    org_id: int
    term_id: int
    scope: GenerationScope
    from_date: date
    to_date: date
    ruleset: GenerationRuleSet
    preview_first: bool = False


class GeneratedLesson(BaseModel):
    """Generated lesson proposal."""
    date: date
    slot_id: int
    room_id: Optional[int]
    enrollment_id: int
    group_id: int  # Add group_id for conflict checking
    score: Optional[float] = None  # optimization score


class LessonBlock(BaseModel):
    """Block of consecutive lessons for a group."""
    date: date
    start_slot_id: int
    end_slot_id: int
    room_id: Optional[int]
    enrollment_id: int
    group_id: int
    teacher_id: int
    course_id: int
    block_size: int  # Number of consecutive lessons
    score: Optional[float] = None


class GenerationResult(BaseModel):
    """Generation result schema."""
    proposals: List[GeneratedLesson]
    blocks: List[LessonBlock] = []  # Block-based proposals
    stats: Dict[str, Any]
    conflicts: List[str] = []
    success: bool = True
