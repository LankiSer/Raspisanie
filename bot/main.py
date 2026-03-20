"""VKSIT Schedule Telegram Bot — aiogram 3.x."""

import asyncio
import logging
import os
from datetime import date, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
)
from dotenv import load_dotenv
import httpx

load_dotenv()

BOT_TOKEN    = os.environ["BOT_TOKEN"]
API_BASE     = os.environ.get("API_BASE_URL", "http://backend:8000/api/v1")
API_BOT_TOKEN = os.environ.get("API_BOT_TOKEN", "")  # Optional bearer token for bot→API calls

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)


# ── API client ────────────────────────────────────────────────────────────────

async def _api_get(path: str, params: dict | None = None):
    headers = {}
    if API_BOT_TOKEN:
        headers["Authorization"] = f"Bearer {API_BOT_TOKEN}"
    async with httpx.AsyncClient(base_url=API_BASE, timeout=15) as client:
        r = await client.get(path, params=params or {}, headers=headers)
        r.raise_for_status()
        return r.json()


# ── Keyboards ─────────────────────────────────────────────────────────────────

def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Расписание на сегодня"), KeyboardButton(text="📆 Расписание на неделю")],
            [KeyboardButton(text="🔍 Поиск по группе"),       KeyboardButton(text="🔍 Поиск по преподавателю")],
            [KeyboardButton(text="❓ Задать вопрос")],
        ],
        resize_keyboard=True,
    )


# ── FSM ───────────────────────────────────────────────────────────────────────

class SearchStates(StatesGroup):
    waiting_group_name   = State()
    waiting_teacher_name = State()
    waiting_question     = State()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_lesson(lesson: dict) -> str:
    time = f"{lesson.get('start_time','')[:5]}–{lesson.get('end_time','')[:5]}"
    return (
        f"  {time} | {lesson.get('course_name','')} "
        f"({lesson.get('group_name','')}) "
        f"— {lesson.get('teacher_name','')} "
        f"ауд. {lesson.get('room_number','')}"
    )


async def _schedule_for_day(day: date, group_id: int | None = None, teacher_id: int | None = None) -> str:
    params: dict = {
        "start_date": str(day),
        "end_date":   str(day),
    }
    if group_id:
        params["group_id"] = group_id
    if teacher_id:
        params["teacher_id"] = teacher_id

    try:
        data = await _api_get("/lessons/term", params)
    except Exception as exc:
        return f"⚠️ Не удалось получить расписание: {exc}"

    if not data:
        return f"📭 На {day.strftime('%d.%m.%Y')} занятий нет."

    lines = [f"📅 *{day.strftime('%A, %d.%m.%Y')}*"]
    for lesson in data:
        lines.append(_fmt_lesson(lesson))
    return "\n".join(lines)


async def _schedule_for_week(group_id: int | None = None, teacher_id: int | None = None) -> str:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)

    params: dict = {
        "start_date": str(monday),
        "end_date":   str(friday),
    }
    if group_id:
        params["group_id"] = group_id
    if teacher_id:
        params["teacher_id"] = teacher_id

    try:
        data = await _api_get("/lessons/term", params)
    except Exception as exc:
        return f"⚠️ Не удалось получить расписание: {exc}"

    if not data:
        return "📭 На текущей неделе занятий нет."

    days: dict[str, list] = {}
    for lesson in data:
        days.setdefault(lesson["date"], []).append(lesson)

    lines = [f"📆 *Расписание {monday.strftime('%d.%m')}–{friday.strftime('%d.%m.%Y')}*"]
    for day_str in sorted(days):
        day_date = date.fromisoformat(day_str)
        lines.append(f"\n*{day_date.strftime('%A, %d.%m')}*")
        for lesson in days[day_str]:
            lines.append(_fmt_lesson(lesson))
    return "\n".join(lines)


# ── Handlers ──────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "👋 Привет! Я бот расписания *ВКСИТ*.\n\n"
        "Выберите действие в меню ниже или используйте команды:\n"
        "/today — расписание на сегодня\n"
        "/week — расписание на неделю\n"
        "/group <название> — поиск по группе\n"
        "/teacher <фамилия> — поиск по преподавателю",
        parse_mode="Markdown",
        reply_markup=main_kb(),
    )


@router.message(Command("today"))
@router.message(F.text == "📅 Расписание на сегодня")
async def cmd_today(msg: Message):
    text = await _schedule_for_day(date.today())
    await msg.answer(text, parse_mode="Markdown")


@router.message(Command("week"))
@router.message(F.text == "📆 Расписание на неделю")
async def cmd_week(msg: Message):
    text = await _schedule_for_week()
    await msg.answer(text, parse_mode="Markdown")


# ── Group search ──────────────────────────────────────────────────────────────

@router.message(F.text == "🔍 Поиск по группе")
@router.message(Command("group"))
async def cmd_group_start(msg: Message, state: FSMContext):
    # If command has argument, use it directly
    parts = (msg.text or "").split(maxsplit=1)
    if len(parts) > 1:
        await _group_search(msg, parts[1], state)
        return
    await state.set_state(SearchStates.waiting_group_name)
    await msg.answer("Введите название или часть названия группы:", reply_markup=ReplyKeyboardRemove())


@router.message(SearchStates.waiting_group_name)
async def process_group_name(msg: Message, state: FSMContext):
    await state.clear()
    await _group_search(msg, msg.text or "", state)


async def _group_search(msg: Message, query: str, state: FSMContext):
    try:
        groups = await _api_get("/educational/groups", {"search": query})
    except Exception as exc:
        await msg.answer(f"⚠️ Ошибка поиска: {exc}", reply_markup=main_kb())
        return

    if not groups:
        await msg.answer("Группы не найдены.", reply_markup=main_kb())
        return

    if len(groups) == 1:
        text = await _schedule_for_week(group_id=groups[0]["group_id"])
        await msg.answer(f"*Группа {groups[0]['name']}*\n\n{text}", parse_mode="Markdown", reply_markup=main_kb())
        return

    # Multiple matches — show inline keyboard
    buttons = [
        [InlineKeyboardButton(text=g["name"], callback_data=f"grp_{g['group_id']}")]
        for g in groups[:10]
    ]
    await msg.answer(
        "Найдено несколько групп. Выберите:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("grp_"))
async def cb_group(call: CallbackQuery):
    group_id = int(call.data.split("_")[1])
    await call.answer()
    text = await _schedule_for_week(group_id=group_id)
    await call.message.answer(text, parse_mode="Markdown", reply_markup=main_kb())


# ── Teacher search ────────────────────────────────────────────────────────────

@router.message(F.text == "🔍 Поиск по преподавателю")
@router.message(Command("teacher"))
async def cmd_teacher_start(msg: Message, state: FSMContext):
    parts = (msg.text or "").split(maxsplit=1)
    if len(parts) > 1:
        await _teacher_search(msg, parts[1])
        return
    await state.set_state(SearchStates.waiting_teacher_name)
    await msg.answer("Введите фамилию преподавателя:", reply_markup=ReplyKeyboardRemove())


@router.message(SearchStates.waiting_teacher_name)
async def process_teacher_name(msg: Message, state: FSMContext):
    await state.clear()
    await _teacher_search(msg, msg.text or "")


async def _teacher_search(msg: Message, query: str):
    try:
        teachers = await _api_get("/educational/teachers", {"search": query})
    except Exception as exc:
        await msg.answer(f"⚠️ Ошибка поиска: {exc}", reply_markup=main_kb())
        return

    if not teachers:
        await msg.answer("Преподаватели не найдены.", reply_markup=main_kb())
        return

    if len(teachers) == 1:
        t = teachers[0]
        name = f"{t['first_name']} {t['last_name']}"
        text = await _schedule_for_week(teacher_id=t["teacher_id"])
        await msg.answer(f"*{name}*\n\n{text}", parse_mode="Markdown", reply_markup=main_kb())
        return

    buttons = [
        [InlineKeyboardButton(
            text=f"{t['first_name']} {t['last_name']}",
            callback_data=f"tch_{t['teacher_id']}"
        )]
        for t in teachers[:10]
    ]
    await msg.answer(
        "Найдено несколько преподавателей. Выберите:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("tch_"))
async def cb_teacher(call: CallbackQuery):
    teacher_id = int(call.data.split("_")[1])
    await call.answer()
    text = await _schedule_for_week(teacher_id=teacher_id)
    await call.message.answer(text, parse_mode="Markdown", reply_markup=main_kb())


# ── Question to admin ─────────────────────────────────────────────────────────

@router.message(F.text == "❓ Задать вопрос")
async def cmd_ask_question(msg: Message, state: FSMContext):
    await state.set_state(SearchStates.waiting_question)
    await msg.answer(
        "Напишите ваш вопрос. Администратор ответит в ближайшее время.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(SearchStates.waiting_question)
async def process_question(msg: Message, state: FSMContext):
    await state.clear()
    question_text = msg.text or ""
    tg_user_id = msg.from_user.id
    tg_username = msg.from_user.username or ""
    full_name = msg.from_user.full_name or ""

    try:
        async with httpx.AsyncClient(base_url=API_BASE, timeout=10) as client:
            headers = {}
            if API_BOT_TOKEN:
                headers["Authorization"] = f"Bearer {API_BOT_TOKEN}"
            await client.post("/tg/messages", json={
                "tg_user_id": tg_user_id,
                "tg_username": tg_username,
                "full_name": full_name,
                "text": question_text,
            }, headers=headers)
        await msg.answer(
            "✅ Ваш вопрос отправлен. Администратор ответит вам здесь.",
            reply_markup=main_kb(),
        )
    except Exception as exc:
        logger.error(f"Failed to save question: {exc}")
        await msg.answer(
            "⚠️ Не удалось отправить вопрос. Попробуйте позже.",
            reply_markup=main_kb(),
        )


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    logger.info("Starting VKSIT Schedule Bot...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
