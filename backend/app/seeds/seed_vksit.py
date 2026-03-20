"""
Seed script: realistic VKSIT data for schedule generation.

Usage:
    cd Raspisanie/backend
    python -m app.seeds.seed_vksit

The script is idempotent — running it twice will not create duplicates.
It creates (for org_id = 1):
  • Academic year 2025-2026 + two terms
  • 5 time slots (pairs 1–5)
  • 12 rooms (audiences)
  • 3 specialties × 4 years = up to 12 groups
  • 20 teachers
  • 30 courses
  • CourseAssignments (teacher ↔ course)
  • Enrollments (group ↔ courseAssignment with planned_hours)
"""

import asyncio
import logging
from datetime import date, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.academic import AcademicYear, Term
from app.models.educational import Course, CourseAssignment, Enrollment, Group, Teacher
from app.models.facilities import Room, TeacherAvailability, TimeTableSlot
from app.models.organization import Organization
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

ORG_ID = 1

# ── Academic calendar ────────────────────────────────────────────────────────

ACADEMIC_YEAR = {
    "name": "2025-2026",
    "start_date": date(2025, 9, 1),
    "end_date":   date(2026, 6, 30),
}

TERMS = [
    {"name": "Осенний семестр 2025", "start_date": date(2025, 9, 1),  "end_date": date(2026, 1, 25)},
    {"name": "Весенний семестр 2026", "start_date": date(2026, 2, 3), "end_date": date(2026, 6, 28)},
]

# ── Time slots (academic pairs) ──────────────────────────────────────────────

SLOTS = [
    {"label": "Пара 1", "start_time": time(8,  30), "end_time": time(10,  0),  "break_minutes": 10},
    {"label": "Пара 2", "start_time": time(10, 10), "end_time": time(11, 40),  "break_minutes": 30},
    {"label": "Пара 3", "start_time": time(12, 10), "end_time": time(13, 40),  "break_minutes": 10},
    {"label": "Пара 4", "start_time": time(13, 50), "end_time": time(15, 20),  "break_minutes": 10},
    {"label": "Пара 5", "start_time": time(15, 30), "end_time": time(17,  0),  "break_minutes": 0},
]

# ── Rooms ────────────────────────────────────────────────────────────────────

ROOMS = [
    {"number": "101", "capacity": 30},
    {"number": "102", "capacity": 30},
    {"number": "103", "capacity": 30},
    {"number": "201", "capacity": 25},
    {"number": "202", "capacity": 25},
    {"number": "203", "capacity": 25},
    {"number": "301", "capacity": 20},
    {"number": "302", "capacity": 20},
    {"number": "303", "capacity": 20},
    {"number": "ИТ-1", "capacity": 15},
    {"number": "ИТ-2", "capacity": 15},
    {"number": "Акт",  "capacity": 120},
]

# ── Groups (specialties × years) ─────────────────────────────────────────────
# Three specialties of VKSIT: ИБ, РиУПО (progs), ССА (net admins)

GROUPS = [
    # ИБ — Information Security
    {"name": "ИБ-11",   "size": 26, "year_level": 1, "generation_type": 2},
    {"name": "ИБ-21",   "size": 24, "year_level": 2, "generation_type": 2},
    {"name": "ИБ-31",   "size": 22, "year_level": 3, "generation_type": 2},
    {"name": "ИБ-41",   "size": 20, "year_level": 4, "generation_type": 2},
    # РиУПО — Software Development
    {"name": "РиУПО-11","size": 28, "year_level": 1, "generation_type": 2},
    {"name": "РиУПО-21","size": 27, "year_level": 2, "generation_type": 2},
    {"name": "РиУПО-31","size": 25, "year_level": 3, "generation_type": 2},
    {"name": "РиУПО-41","size": 23, "year_level": 4, "generation_type": 2},
    # ССА — Network & System Administration
    {"name": "ССА-11",  "size": 25, "year_level": 1, "generation_type": 2},
    {"name": "ССА-21",  "size": 24, "year_level": 2, "generation_type": 2},
    {"name": "ССА-31",  "size": 22, "year_level": 3, "generation_type": 2},
    {"name": "ССА-41",  "size": 20, "year_level": 4, "generation_type": 2},
]

# ── Teachers ──────────────────────────────────────────────────────────────────

TEACHERS = [
    {"first_name": "Андрей",    "last_name": "Иванов",     "email": "a.ivanov@vksit.ru"},
    {"first_name": "Мария",     "last_name": "Петрова",    "email": "m.petrova@vksit.ru"},
    {"first_name": "Сергей",    "last_name": "Сидоров",    "email": "s.sidorov@vksit.ru"},
    {"first_name": "Ольга",     "last_name": "Козлова",    "email": "o.kozlova@vksit.ru"},
    {"first_name": "Дмитрий",   "last_name": "Новиков",    "email": "d.novikov@vksit.ru"},
    {"first_name": "Елена",     "last_name": "Морозова",   "email": "e.morozova@vksit.ru"},
    {"first_name": "Алексей",   "last_name": "Волков",     "email": "a.volkov@vksit.ru"},
    {"first_name": "Наталья",   "last_name": "Алексеева",  "email": "n.alekseeva@vksit.ru"},
    {"first_name": "Виктор",    "last_name": "Лебедев",    "email": "v.lebedev@vksit.ru"},
    {"first_name": "Татьяна",   "last_name": "Семёнова",   "email": "t.semenova@vksit.ru"},
    {"first_name": "Игорь",     "last_name": "Егоров",     "email": "i.egorov@vksit.ru"},
    {"first_name": "Людмила",   "last_name": "Павлова",    "email": "l.pavlova@vksit.ru"},
    {"first_name": "Николай",   "last_name": "Степанов",   "email": "n.stepanov@vksit.ru"},
    {"first_name": "Ирина",     "last_name": "Белова",     "email": "i.belova@vksit.ru"},
    {"first_name": "Пётр",      "last_name": "Комаров",    "email": "p.komarov@vksit.ru"},
    {"first_name": "Юлия",      "last_name": "Орлова",     "email": "yu.orlova@vksit.ru"},
    {"first_name": "Роман",     "last_name": "Кузнецов",   "email": "r.kuznetsov@vksit.ru"},
    {"first_name": "Светлана",  "last_name": "Тихонова",   "email": "s.tikhonova@vksit.ru"},
    {"first_name": "Михаил",    "last_name": "Фёдоров",    "email": "m.fedorov@vksit.ru"},
    {"first_name": "Анна",      "last_name": "Соколова",   "email": "a.sokolova@vksit.ru"},
]

# ── Courses ───────────────────────────────────────────────────────────────────

COURSES = [
    # Common (all specialties)
    {"name": "Математика",              "type": "lecture"},
    {"name": "Информатика",             "type": "lecture"},
    {"name": "Физическая культура",     "type": "practical"},
    {"name": "Русский язык",            "type": "lecture"},
    {"name": "История",                 "type": "lecture"},
    {"name": "Английский язык",         "type": "practical"},
    {"name": "Экономика",               "type": "lecture"},
    {"name": "Право",                   "type": "lecture"},
    # ИБ-specific
    {"name": "Основы информационной безопасности", "type": "lecture"},
    {"name": "Криптография",            "type": "lecture"},
    {"name": "Защита сетей",            "type": "lab"},
    {"name": "Безопасность ОС",         "type": "lab"},
    {"name": "Анализ уязвимостей",      "type": "lab"},
    # РиУПО-specific
    {"name": "Программирование",        "type": "lab"},
    {"name": "Алгоритмы и структуры данных", "type": "lecture"},
    {"name": "Базы данных",             "type": "lab"},
    {"name": "Web-разработка",          "type": "lab"},
    {"name": "Разработка мобильных приложений", "type": "lab"},
    {"name": "Тестирование ПО",         "type": "practical"},
    # ССА-specific
    {"name": "Сетевые технологии",      "type": "lecture"},
    {"name": "Администрирование Linux", "type": "lab"},
    {"name": "Администрирование Windows", "type": "lab"},
    {"name": "Виртуализация",           "type": "lab"},
    {"name": "Cisco / MikroTik",        "type": "lab"},
    # Advanced / cross-specialty
    {"name": "Проектная деятельность",  "type": "practical"},
    {"name": "Технологии программирования", "type": "lecture"},
    {"name": "Управление IT-проектами", "type": "lecture"},
    {"name": "Облачные технологии",     "type": "lecture"},
    {"name": "Машинное обучение",       "type": "lecture"},
    {"name": "Философия",               "type": "lecture"},
]

# ── Course assignments (teacher index → course name list) ────────────────────
# Format: (teacher_index, course_name)

ASSIGNMENTS_MAP = [
    # т_0 Иванов
    (0, "Математика"),
    (0, "Алгоритмы и структуры данных"),
    # т_1 Петрова
    (1, "Русский язык"),
    (1, "История"),
    # т_2 Сидоров
    (2, "Информатика"),
    (2, "Программирование"),
    # т_3 Козлова
    (3, "Английский язык"),
    # т_4 Новиков
    (4, "Основы информационной безопасности"),
    (4, "Криптография"),
    # т_5 Морозова
    (5, "Базы данных"),
    (5, "Программирование"),
    # т_6 Волков
    (6, "Защита сетей"),
    (6, "Безопасность ОС"),
    # т_7 Алексеева
    (7, "Web-разработка"),
    (7, "Тестирование ПО"),
    # т_8 Лебедев
    (8, "Сетевые технологии"),
    (8, "Cisco / MikroTik"),
    # т_9 Семёнова
    (9, "Экономика"),
    (9, "Управление IT-проектами"),
    # т_10 Егоров
    (10, "Администрирование Linux"),
    (10, "Администрирование Windows"),
    # т_11 Павлова
    (11, "Физическая культура"),
    # т_12 Степанов
    (12, "Анализ уязвимостей"),
    (12, "Виртуализация"),
    # т_13 Белова
    (13, "Право"),
    (13, "Философия"),
    # т_14 Комаров
    (14, "Разработка мобильных приложений"),
    (14, "Машинное обучение"),
    # т_15 Орлова
    (15, "Проектная деятельность"),
    (15, "Облачные технологии"),
    # т_16 Кузнецов
    (16, "Технологии программирования"),
    # т_17 Тихонова
    (17, "Алгоритмы и структуры данных"),
    # т_18 Фёдоров
    (18, "Математика"),
    # т_19 Соколова
    (19, "Английский язык"),
]

# ── Enrollment plan: (group_name, course_name, planned_hours) ────────────────
# 72 = 2 lessons/week × 18 weeks × 2h = one per semester standard

ENROLLMENT_PLAN = [
    # ──────────── Common for all groups ────────────
    *[(g["name"], "Математика",           72) for g in GROUPS[:8]],
    *[(g["name"], "Информатика",          54) for g in GROUPS[:8]],
    *[(g["name"], "Физическая культура",  36) for g in GROUPS],
    *[(g["name"], "Английский язык",      54) for g in GROUPS],
    *[(g["name"], "История",              36) for g in GROUPS[:4]],
    *[(g["name"], "Русский язык",         36) for g in GROUPS[:4]],
    *[(g["name"], "Экономика",            36) for g in GROUPS[4:8]],
    *[(g["name"], "Право",                36) for g in GROUPS[4:8]],
    # ──────────── ИБ ────────────
    *[(g["name"], "Основы информационной безопасности", 72) for g in GROUPS[:4]],
    *[(g["name"], "Криптография",         54) for g in GROUPS[1:4]],
    *[(g["name"], "Защита сетей",         54) for g in GROUPS[2:4]],
    *[(g["name"], "Безопасность ОС",      54) for g in GROUPS[2:4]],
    *[(g["name"], "Анализ уязвимостей",   54) for g in GROUPS[3:4]],
    # ──────────── РиУПО ────────────
    *[(g["name"], "Программирование",     90) for g in GROUPS[4:8]],
    *[(g["name"], "Алгоритмы и структуры данных", 72) for g in GROUPS[4:7]],
    *[(g["name"], "Базы данных",          72) for g in GROUPS[5:8]],
    *[(g["name"], "Web-разработка",       72) for g in GROUPS[5:8]],
    *[(g["name"], "Тестирование ПО",      36) for g in GROUPS[6:8]],
    *[(g["name"], "Разработка мобильных приложений", 54) for g in GROUPS[7:8]],
    # ──────────── ССА ────────────
    *[(g["name"], "Сетевые технологии",   72) for g in GROUPS[8:]],
    *[(g["name"], "Администрирование Linux",   54) for g in GROUPS[9:]],
    *[(g["name"], "Администрирование Windows", 54) for g in GROUPS[9:]],
    *[(g["name"], "Cisco / MikroTik",     54) for g in GROUPS[10:]],
    *[(g["name"], "Виртуализация",        54) for g in GROUPS[10:]],
    # ──────────── Cross-specialty (senior years) ────────────
    *[(g["name"], "Проектная деятельность", 36) for g in GROUPS[2:4] + GROUPS[6:8] + GROUPS[10:]],
    *[(g["name"], "Облачные технологии",   36) for g in GROUPS[3:4] + GROUPS[7:8] + GROUPS[11:]],
    *[(g["name"], "Управление IT-проектами", 36) for g in GROUPS[7:8] + GROUPS[11:]],
    *[(g["name"], "Машинное обучение",     36) for g in GROUPS[7:8]],
    *[(g["name"], "Философия",             36) for g in GROUPS[:4]],
]


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_or_create(db: AsyncSession, model, filter_kwargs: dict, create_kwargs: dict):
    """Return existing row or create a new one.  Returns (instance, created:bool)."""
    result = await db.execute(select(model).filter_by(**filter_kwargs))
    obj = result.scalar_one_or_none()
    if obj:
        return obj, False
    obj = model(**{**filter_kwargs, **create_kwargs})
    db.add(obj)
    await db.flush()
    return obj, True


# ── Main seed function ────────────────────────────────────────────────────────

async def seed(db: AsyncSession):
    # 1. Ensure organisation
    org, created = await _get_or_create(
        db, Organization,
        {"org_id": ORG_ID},
        {"name": "АПОУ ВО «Вологодский колледж связи и информационных технологий»"},
    )
    if created:
        logger.info("Created organisation: ВКСИТ")

    # 2. Academic year
    ay, _ = await _get_or_create(
        db, AcademicYear,
        {"org_id": ORG_ID, "name": ACADEMIC_YEAR["name"]},
        {"start_date": ACADEMIC_YEAR["start_date"], "end_date": ACADEMIC_YEAR["end_date"]},
    )

    # 3. Terms
    term_map = {}
    for t_data in TERMS:
        t, _ = await _get_or_create(
            db, Term,
            {"org_id": ORG_ID, "name": t_data["name"]},
            {"academic_year_id": ay.id, "start_date": t_data["start_date"], "end_date": t_data["end_date"]},
        )
        term_map[t_data["name"]] = t
    logger.info("Terms: %s", list(term_map.keys()))

    # 4. Time slots
    slot_objs = []
    for s_data in SLOTS:
        s, created = await _get_or_create(
            db, TimeTableSlot,
            {"org_id": ORG_ID, "start_time": s_data["start_time"]},
            {"end_time": s_data["end_time"], "label": s_data["label"], "break_minutes": s_data["break_minutes"]},
        )
        slot_objs.append(s)
        if created:
            logger.info("  Slot %s: %s–%s", s.label, s.start_time, s.end_time)
    logger.info("Time slots: %d", len(slot_objs))

    # 5. Rooms
    room_objs = []
    for r_data in ROOMS:
        r, created = await _get_or_create(
            db, Room,
            {"org_id": ORG_ID, "number": r_data["number"]},
            {"capacity": r_data["capacity"]},
        )
        room_objs.append(r)
    logger.info("Rooms: %d", len(room_objs))

    # 6. Groups
    group_map = {}
    for g_data in GROUPS:
        g, created = await _get_or_create(
            db, Group,
            {"org_id": ORG_ID, "name": g_data["name"]},
            {"size": g_data["size"], "year_level": g_data["year_level"], "generation_type": g_data["generation_type"]},
        )
        group_map[g_data["name"]] = g
        if created:
            logger.info("  Group: %s (size %d)", g.name, g.size)
    logger.info("Groups: %d", len(group_map))

    # 7. Teachers
    teacher_list = []
    for t_data in TEACHERS:
        t, created = await _get_or_create(
            db, Teacher,
            {"org_id": ORG_ID, "email": t_data["email"]},
            {"first_name": t_data["first_name"], "last_name": t_data["last_name"]},
        )
        teacher_list.append(t)
        if created:
            logger.info("  Teacher: %s %s", t.first_name, t.last_name)
    logger.info("Teachers: %d", len(teacher_list))

    # 7b. Доступность преподавателей: пн–пт 08:00–20:00 (для генерации и отчётов)
    av_start, av_end = time(8, 0), time(20, 0)
    for t in teacher_list:
        for wd in range(1, 6):  # 1=Пн … 5=Пт
            await _get_or_create(
                db,
                TeacherAvailability,
                {
                    "org_id": ORG_ID,
                    "teacher_id": t.teacher_id,
                    "weekday": wd,
                    "start_time": av_start,
                },
                {"end_time": av_end, "is_available": True},
            )

    # 8. Courses
    course_map = {}
    for c_data in COURSES:
        c, created = await _get_or_create(
            db, Course,
            {"org_id": ORG_ID, "name": c_data["name"]},
            {"type": c_data["type"]},
        )
        course_map[c_data["name"]] = c
    logger.info("Courses: %d", len(course_map))

    # 9. Course assignments
    assignment_map = {}  # (teacher_id, course_id) → assignment
    for teacher_idx, course_name in ASSIGNMENTS_MAP:
        teacher = teacher_list[teacher_idx]
        course  = course_map.get(course_name)
        if not course:
            logger.warning("Course '%s' not found, skipping assignment", course_name)
            continue
        asgn, created = await _get_or_create(
            db, CourseAssignment,
            {"org_id": ORG_ID, "teacher_id": teacher.teacher_id, "course_id": course.course_id},
            {},
        )
        key = (teacher.teacher_id, course.course_id)
        assignment_map[key] = asgn
    logger.info("Course assignments: %d", len(assignment_map))

    # Build course→assignments lookup for enrollment step
    course_to_assignments: dict = {}
    for (tid, cid), asgn in assignment_map.items():
        course_to_assignments.setdefault(cid, []).append(asgn)

    # 10. Enrollments
    enr_count = 0
    for group_name, course_name, planned_hours in ENROLLMENT_PLAN:
        group  = group_map.get(group_name)
        course = course_map.get(course_name)
        if not group or not course:
            continue
        assignments = course_to_assignments.get(course.course_id, [])
        if not assignments:
            logger.warning("No assignment for course '%s', skipping enrollment for %s", course_name, group_name)
            continue
        # Pick the first available assignment (deterministic)
        asgn = assignments[0]
        enr, created = await _get_or_create(
            db, Enrollment,
            {"org_id": ORG_ID, "assignment_id": asgn.assignment_id, "group_id": group.group_id},
            {"planned_hours": planned_hours, "unit": "per_semester"},
        )
        if created:
            enr_count += 1
    logger.info("Enrollments created: %d", enr_count)

    await db.commit()
    logger.info("✓ Seed completed.")


async def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
