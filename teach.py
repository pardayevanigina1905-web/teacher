import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_check_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_check_server, daemon=True).start()

# --- BU YERDAN PASTDAGI QISMGA O'Z BOTINGIZ KODINI YOZING ---
import asyncio
import sqlite3
import time
import random
import re
from datetime import datetime

from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    TelegramObject
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state


# ============================================================
# SOZLAMALAR
# ============================================================

BOT_TOKEN = "8685900981:AAG8Riv_PL2gywLAMYkn9dDdy3_s-YNzUdM"
ADMIN_ID = 7391661479
DB_NAME = "pnt.db"

CLASSES = [
    "5-sinf", "6-sinf", "7-sinf", "8-sinf", "9-sinf", "10-sinf", "11-sinf",
    "Texnikum 1-kurs", "Texnikum 2-kurs"
]

TYPING_TASKS = {
    "oson": [
        "salom", "informatika", "kompyuter", "maktab", "ustoz", "oquvchi", 
        "kitob", "dars", "sinf", "monitor", "klaviatura", "sichqoncha", 
        "internet", "fayl", "papka", "dastur", "rasm", "video", "matn", 
        "ekran", "printer", "protsessor", "xotira", "windows", "python"
    ],
    "orta": [
        "Kompyuter qurilmalarini organish", "Informatika fanini yaxshi organing",
        "Klaviaturada tez yozishni mashq qiling", "Fayllarni papkalarga joylashtiring",
        "Kompyuterda yangi hujjat yarating", "Internetdan togri foydalanishni biling"
    ],
    "qiyin": [
        "Kompyuter texnologiyalaridan samarali foydalanish bilim va malakani talab qiladi",
        "Axborot texnologiyalarini organish zamonaviy dunyoda juda muhim hisoblanadi"
    ]
}


# ============================================================
# BOT VA STATE'LAR
# ============================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class RegistrationState(StatesGroup):
    fullname = State()
    class_name = State()

class ProfileState(StatesGroup):
    fullname = State()
    class_name = State()

class HomeworkState(StatesGroup):
    topic = State()
    waiting_file = State()

class TeacherContactState(StatesGroup):
    question = State()

class AdminLessonState(StatesGroup):
    class_name = State()
    title = State()
    video = State()
    slide = State()

class AdminBookState(StatesGroup):
    class_name = State()
    file = State()

class AdminDeleteBookState(StatesGroup):
    book_id = State()

class AdminLifehackState(StatesGroup):
    title = State()
    text = State()
    video = State()

class AdminDeleteLessonState(StatesGroup):
    lesson_id = State()

class TypingState(StatesGroup):
    difficulty = State()
    tasks = State()
    current = State()
    correct = State()
    wrong = State()
    total_started = State()
    writing = State()

class TestState(StatesGroup):
    answering = State()

class AdminTestState(StatesGroup):
    lesson_id = State()
    question = State()
    option_a = State()
    option_b = State()
    option_c = State()
    option_d = State()
    correct = State()

class AdminBulkTestState(StatesGroup):
    lesson_id = State()
    raw_tests = State()

class AdminDeleteTestState(StatesGroup):
    test_id = State()

class AdminReplyQuestionState(StatesGroup):
    question_id = State()
    user_id = State()
    answer_text = State()

class AdminGradeHWState(StatesGroup):
    hw_id = State()
    user_id = State()
    score = State()

class AdminManageStudentState(StatesGroup):
    target_user_id = State()
    new_fullname = State()
    new_class = State()


# ============================================================
# DATABASE FUNKSIYALARI
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def add_column_if_not_exists(table_name, column_name, column_type):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = [row["name"] for row in cur.fetchall()]
    if column_name not in columns:
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
    conn.commit()
    conn.close()

def initialize_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            fullname TEXT,
            class_name TEXT,
            is_school_student INTEGER DEFAULT 1,
            is_banned INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT,
            title TEXT,
            video_id TEXT,
            slide_id TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lesson_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER,
            question TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_answer TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lesson_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            lesson_id INTEGER,
            viewed_at TEXT,
            UNIQUE(user_id, lesson_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS slide_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            lesson_id INTEGER,
            viewed_at TEXT,
            UNIQUE(user_id, lesson_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT,
            title TEXT,
            file_id TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            class_name TEXT,
            topic TEXT,
            file_type TEXT,
            file_id TEXT,
            caption TEXT,
            grade INTEGER DEFAULT NULL,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lifehacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            text TEXT,
            video_id TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS teacher_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            fullname TEXT,
            class_name TEXT,
            question TEXT,
            answer TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rating (
            user_id INTEGER PRIMARY KEY,
            lesson_points INTEGER DEFAULT 0,
            slide_points INTEGER DEFAULT 0,
            test_points INTEGER DEFAULT 0,
            typing_points INTEGER DEFAULT 0,
            homework_points INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    
    try:
        add_column_if_not_exists("teacher_questions", "answer", "TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        add_column_if_not_exists("homework", "grade", "INTEGER")
    except sqlite3.OperationalError:
        pass

    add_column_if_not_exists("rating", "slide_points", "INTEGER DEFAULT 0")
    add_column_if_not_exists("rating", "homework_points", "INTEGER DEFAULT 0")
    add_column_if_not_exists("users", "is_banned", "INTEGER DEFAULT 0")
    add_column_if_not_exists("lifehacks", "video_id", "TEXT")

initialize_database()


# ============================================================
# YORDAMCHI FUNKSIYALAR
# ============================================================

def is_admin(user_id):
    return user_id == ADMIN_ID

def get_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, fullname, class_name, is_school_student, is_banned, created_at FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    return user

def create_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO users (id, fullname, class_name, is_school_student, is_banned, created_at)
        VALUES (?, ?, ?, ?, 0, ?)
    """, (user_id, None, None, 1, datetime.now().isoformat()))
    cur.execute("""
        INSERT OR IGNORE INTO rating (user_id, lesson_points, slide_points, test_points, typing_points, homework_points)
        VALUES (?, 0, 0, 0, 0, 0)
    """, (user_id,))
    conn.commit()
    conn.close()

def update_user(user_id, fullname=None, class_name=None):
    conn = get_connection()
    cur = conn.cursor()
    if fullname is not None:
        cur.execute("UPDATE users SET fullname = ? WHERE id = ?", (fullname, user_id))
    if class_name is not None:
        cur.execute("UPDATE users SET class_name = ? WHERE id = ?", (class_name, user_id))
    conn.commit()
    conn.close()

def ensure_rating_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO rating (user_id, lesson_points, slide_points, test_points, typing_points, homework_points) VALUES (?, 0, 0, 0, 0, 0)", (user_id,))
    conn.commit()
    conn.close()

def mark_lesson_viewed(user_id, lesson_id):
    ensure_rating_user(user_id)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO lesson_views (user_id, lesson_id, viewed_at) VALUES (?, ?, ?)", (user_id, lesson_id, datetime.now().isoformat()))
    if cur.rowcount > 0:
        cur.execute("UPDATE rating SET lesson_points = lesson_points + 5 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def mark_slide_viewed(user_id, lesson_id):
    ensure_rating_user(user_id)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO slide_views (user_id, lesson_id, viewed_at) VALUES (?, ?, ?)", (user_id, lesson_id, datetime.now().isoformat()))
    if cur.rowcount > 0:
        cur.execute("UPDATE rating SET slide_points = slide_points + 5 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def add_test_points(user_id, points):
    ensure_rating_user(user_id)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE rating SET test_points = test_points + ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()

def add_typing_points(user_id, points):
    ensure_rating_user(user_id)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE rating SET typing_points = typing_points + ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()

def add_homework_points(user_id, points):
    ensure_rating_user(user_id)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE rating SET homework_points = homework_points + ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()

def get_all_users_rating():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id AS user_id, u.fullname, u.class_name, u.is_banned,
               COALESCE(r.lesson_points, 0) AS lesson_points,
               COALESCE(r.slide_points, 0) AS slide_points,
               COALESCE(r.test_points, 0) AS test_points,
               COALESCE(r.typing_points, 0) AS typing_points,
               COALESCE(r.homework_points, 0) AS homework_points,
               (COALESCE(r.lesson_points, 0) + COALESCE(r.slide_points, 0) + COALESCE(r.test_points, 0) + COALESCE(r.typing_points, 0) + COALESCE(r.homework_points, 0)) AS total_points
        FROM users u
        LEFT JOIN rating r ON u.id = r.user_id
        WHERE u.is_banned = 0
        ORDER BY total_points DESC, u.id ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def parse_bulk_tests_text(raw_text: str):
    raw_blocks = re.split(r'(?:\n|^)\d+[\.\)]\s*', raw_text.strip())
    parsed_list = []

    for block in raw_blocks:
        if not block.strip():
            continue

        correct_match = re.search(r'To[\'’`‘]?g[\'’`‘]?ri javob:\s*([A-Da-d])', block, re.IGNORECASE)
        correct_letter = correct_match.group(1).upper() if correct_match else "A"
        opt_matches = re.findall(r'([A-D])[\)\.]\s*(.+)', block)
        
        first_opt_pos = len(block)
        for m in re.finditer(r'[A-D][\)\.]', block):
            first_opt_pos = m.start()
            break
            
        q_text = block[:first_opt_pos].strip()
        options = {}
        for letter, opt_val in opt_matches:
            clean_opt = re.sub(r'\(To[\'’`‘]?g[\'’`‘]?ri javob:.*?\)', '', opt_val, flags=re.IGNORECASE).strip()
            options[letter.upper()] = clean_opt

        if q_text and len(options) >= 2:
            parsed_list.append({
                "question": q_text,
                "option_a": options.get("A", ""),
                "option_b": options.get("B", ""),
                "option_c": options.get("C", ""),
                "option_d": options.get("D", ""),
                "correct": correct_letter
            })

    return parsed_list


# ============================================================
# MIDDLEWARE - BLOKLANGANLARI TEKSHIRISH
# ============================================================

class BanCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user_id = getattr(getattr(event, "from_user", None), "id", None)
        if user_id:
            user = get_user(user_id)
            if user and user["is_banned"] == 1:
                if isinstance(event, Message):
                    await event.answer("🚫 <b>Siz botdan chiqarilgansiz (bloklangansiz)!</b>", parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    await event.answer("🚫 Siz botdan chiqarilgansiz!", show_alert=True)
                return
        return await handler(event, data)


# ============================================================
# MENYULAR VA KEYBOARDLAR
# ============================================================

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Video darslar"), KeyboardButton(text="📚 Elektron kutubxona")],
            [KeyboardButton(text="📝 Uyga vazifa"), KeyboardButton(text="⌨️ Tez yozish")],
            [KeyboardButton(text="⚡ Kompyuter layfxaklari"), KeyboardButton(text="🏆 Reyting")],
            [KeyboardButton(text="👤 Shaxsiy profil"), KeyboardButton(text="👨‍🏫 Ustoz bilan bog‘lanish")]
        ],
        resize_keyboard=True
    )

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Video darslar"), KeyboardButton(text="📚 Elektron kutubxona")],
            [KeyboardButton(text="📝 Uyga vazifa"), KeyboardButton(text="⌨️ Tez yozish")],
            [KeyboardButton(text="⚡ Kompyuter layfxaklari"), KeyboardButton(text="🏆 Reyting")],
            [KeyboardButton(text="👤 Shaxsiy profil"), KeyboardButton(text="👨‍🏫 Ustoz bilan bog‘lanish")],
            [KeyboardButton(text="👨‍💻 ADMIN PANEL")]
        ],
        resize_keyboard=True
    )

def get_registration_keyboard():
    buttons = []
    for cn in CLASSES[:7]:
        buttons.append([InlineKeyboardButton(text=f"🏫 {cn}", callback_data=f"reg_class:{cn}")])
    buttons.append([InlineKeyboardButton(text="🏛 Texnikum talabasiman", callback_data="reg_texnikum")])
    buttons.append([InlineKeyboardButton(text="🎓 Maktabni bitirganman", callback_data="reg_graduated")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_texnikum_course_keyboard(prefix="reg_class:"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1-kurs", callback_data=f"{prefix}Texnikum 1-kurs")],
        [InlineKeyboardButton(text="2-kurs", callback_data=f"{prefix}Texnikum 2-kurs")]
    ])

def category_keyboard(prefix):
    buttons = []
    for cn in CLASSES:
        buttons.append([InlineKeyboardButton(text=f"📚 {cn}", callback_data=f"{prefix}:{cn}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_panel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Video darslar boshqaruvi", callback_data="admin_video_menu")],
            [InlineKeyboardButton(text="📚 Kitoblar boshqaruvi", callback_data="admin_book_menu")],
            [InlineKeyboardButton(text="📝 Uyga vazifalar (Baholash)", callback_data="admin_homework_list")],
            [InlineKeyboardButton(text="⚡ Layfxak qo‘shish", callback_data="admin_lifehack_add")],
            [InlineKeyboardButton(text="❓ O‘quvchilar savollari", callback_data="admin_questions_list")],
            [InlineKeyboardButton(text="👥 O‘quvchilarni boshqarish", callback_data="admin_students_menu")]
        ]
    )

def admin_book_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Kitob qo‘shish", callback_data="admin_book_add")],
            [InlineKeyboardButton(text="📚 Kitoblar ro‘yxati", callback_data="admin_books_list")],
            [InlineKeyboardButton(text="🗑 Kitob o‘chirish", callback_data="admin_delete_book")]
        ]
    )

def admin_video_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Yangi mavzu qo'shish", callback_data="admin_add_lesson")],
            [InlineKeyboardButton(text="📚 Mavzular ro'yxati", callback_data="admin_lessons_list")],
            [InlineKeyboardButton(text="🗑 Mavzuni o‘chirish", callback_data="admin_delete_lesson")],
            [InlineKeyboardButton(text="➕ Bitta test qo'shish", callback_data="admin_add_single_test")],
            [InlineKeyboardButton(text="📥 Bulk test qo‘shish", callback_data="admin_add_bulk_test")],
            [InlineKeyboardButton(text="📋 Testlar ro'yxati", callback_data="admin_tests_list_btn")],
            [InlineKeyboardButton(text="🗑 Testni o‘chirish", callback_data="admin_delete_test_btn")]
        ]
    )


# ============================================================
# START VA REGISTRATION HANDLERLARI
# ============================================================

@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = get_user(user_id)

    if not user:
        create_user(user_id)
        await state.set_state(RegistrationState.fullname)
        await message.answer(
            "👋 <b>Teacher Nigina Bot</b>ga xush kelibsiz!\n\n"
            "Botdan foydalanish uchun avval ro‘yxatdan o‘tamiz.\n\n"
            "✍️ <b>Ism va familiyangizni yozing:</b>\n\nMasalan: <code>Nigina Pardayeva</code>",
            parse_mode="HTML"
        )
        return

    if not user["fullname"]:
        await state.set_state(RegistrationState.fullname)
        await message.answer("✍️ <b>Ism va familiyangizni yozing:</b>", parse_mode="HTML")
        return

    if not user["class_name"]:
        await show_class_selection(message, state)
        return

    markup = admin_menu() if is_admin(user_id) else main_menu()
    await message.answer(f"👋 <b>Xush kelibsiz!</b>\n\n👤 {user['fullname']}\n🏫 {user['class_name']}", reply_markup=markup, parse_mode="HTML")

@dp.message(RegistrationState.fullname, F.text)
async def registration_fullname(message: Message, state: FSMContext):
    fullname = (message.text or "").strip()
    if len(fullname) < 3:
        await message.answer("❗ Ism va familiyangizni to‘liqroq yozing.")
        return
    update_user(message.from_user.id, fullname=fullname)
    await state.clear()
    await show_class_selection(message, state)

async def show_class_selection(message: Message, state: FSMContext):
    await state.set_state(RegistrationState.class_name)
    await message.answer("🏫 <b>Sinfingizni yoki ta'lim bosqichingizni tanlang:</b>", reply_markup=get_registration_keyboard(), parse_mode="HTML")

@dp.callback_query(RegistrationState.class_name, F.data == "reg_texnikum")
async def registration_texnikum_select(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("🏛 <b>Texnikum kursingizni tanlang:</b>", reply_markup=get_texnikum_course_keyboard("reg_class:"), parse_mode="HTML")

@dp.callback_query(RegistrationState.class_name, F.data.startswith("reg_class:"))
async def registration_class(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    class_name = callback.data.split(":", 1)[1]
    update_user(callback.from_user.id, class_name=class_name)
    await state.clear()
    user = get_user(callback.from_user.id)
    await callback.message.answer(f"✅ <b>Ro‘yxatdan o‘tish yakunlandi!</b>\n\n👤 {user['fullname']}\n🏫 {user['class_name']}", reply_markup=main_menu(), parse_mode="HTML")

@dp.callback_query(RegistrationState.class_name, F.data == "reg_graduated")
async def registration_graduated(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    update_user(callback.from_user.id, class_name="Maktabni bitirganman")
    await state.clear()
    user = get_user(callback.from_user.id)
    await callback.message.answer(f"✅ <b>Ro‘yxatdan o‘tish yakunlandi!</b>\n\n👤 {user['fullname']}\n🎓 Maktabni bitirganman", reply_markup=main_menu(), parse_mode="HTML")


# ============================================================
# PROFIL HANDLERLARI
# ============================================================

@dp.message(F.text == "👤 Shaxsiy profil")
@dp.message(Command("profil"))
async def profile_handler(message: Message, state: FSMContext):
    await state.clear()
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❗ Avval /start buyrug‘ini bosing.")
        return

    ensure_rating_user(message.from_user.id)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT lesson_points, slide_points, test_points, typing_points, homework_points FROM rating WHERE user_id = ?", (message.from_user.id,))
    rating = cur.fetchone()
    conn.close()

    total = rating['lesson_points'] + rating['slide_points'] + rating['test_points'] + rating['typing_points'] + rating['homework_points']
    all_users = get_all_users_rating()
    my_place = "-"
    for idx, row in enumerate(all_users, 1):
        if row["user_id"] == message.from_user.id:
            my_place = idx
            break

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Ism-familiyani o‘zgartirish", callback_data="profile_edit_name")],
        [InlineKeyboardButton(text="🏫 Sinf/Bosqichni o‘zgartirish", callback_data="profile_edit_class")]
    ])

    await message.answer(
        f"👤 <b>SHAXSIY PROFIL</b>\n\n"
        f"🆔 ID: <code>{user['id']}</code>\n"
        f"👤 Ism-familiya: <b>{user['fullname'] or '—'}</b>\n"
        f"🏫 Sinf/Bosqich: <b>{user['class_name'] or '—'}</b>\n\n"
        f"🏆 <b>Natijalaringiz:</b>\n"
        f"🎥 Video darslar: {rating['lesson_points']} ball\n"
        f"🖥 Slaydlar: {rating['slide_points']} ball\n"
        f"📝 Testlar: {rating['test_points']} ball\n"
        f"⌨️ Tez yozish: {rating['typing_points']} ball\n"
        f"📚 Uyga vazifalar: {rating['homework_points']} ball\n"
        f"⭐ Jami ball: <b>{total} ball</b>\n"
        f"🏅 Reytingdagi o‘rningiz: <b>{my_place}-o'rin</b>",
        reply_markup=keyboard, parse_mode="HTML"
    )

@dp.callback_query(F.data == "profile_edit_name")
async def profile_edit_name(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(ProfileState.fullname)
    await callback.message.answer("✏️ Yangi ism va familiyangizni yozing:")

@dp.message(ProfileState.fullname, F.text)
async def profile_save_name(message: Message, state: FSMContext):
    fullname = (message.text or "").strip()
    if len(fullname) < 3:
        await message.answer("❗ Ism va familiyani to‘g‘ri yozing.")
        return
    update_user(message.from_user.id, fullname=fullname)
    await state.clear()
    await message.answer("✅ Ism-familiyangiz yangilandi.")

@dp.callback_query(F.data == "profile_edit_class")
async def profile_edit_class(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(ProfileState.class_name)
    await callback.message.answer("🏫 Yangi sinf yoki bosqichni tanlang:", reply_markup=get_registration_keyboard())

@dp.callback_query(ProfileState.class_name, F.data == "reg_texnikum")
async def profile_texnikum_select(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("🏛 <b>Texnikum kursingizni tanlang:</b>", reply_markup=get_texnikum_course_keyboard("profile_class:"), parse_mode="HTML")

@dp.callback_query(ProfileState.class_name, F.data.startswith("reg_class:"))
@dp.callback_query(ProfileState.class_name, F.data.startswith("profile_class:"))
async def profile_save_class(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    class_name = callback.data.split(":", 1)[1]
    update_user(callback.from_user.id, class_name=class_name)
    await state.clear()
    await callback.message.answer(f"✅ O'zgarish saqlandi: <b>{class_name}</b>", parse_mode="HTML")


# ============================================================
# VIDEO DARSLAR VA QUIZ TESTLAR
# ============================================================

@dp.message(F.text == "🎬 Video darslar")
@dp.message(Command("video"))
async def video_lessons_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🎬 <b>VIDEO DARSLAR</b>\n\nSinf yoki bo'limni tanlang:", reply_markup=category_keyboard("vd_class"), parse_mode="HTML")

@dp.callback_query(F.data.startswith("vd_class:"))
async def video_class_selected(callback: CallbackQuery):
    await callback.answer()
    class_name = callback.data.split(":", 1)[1]
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM lessons WHERE class_name = ? ORDER BY id ASC", (class_name,))
    lessons = cur.fetchall()
    conn.close()

    if not lessons:
        await callback.message.answer(f"📚 <b>{class_name}</b>\n\nHozircha video darslar joylanmagan.", parse_mode="HTML")
        return

    buttons = [[InlineKeyboardButton(text=f"📖 {l['title']}", callback_data=f"vd_lesson:{l['id']}")] for l in lessons]
    await callback.message.answer(f"📚 <b>{class_name}</b>\n\nMavzuni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")

@dp.callback_query(F.data.startswith("vd_lesson:"))
async def video_lesson_menu(callback: CallbackQuery):
    await callback.answer()
    lesson_id = int(callback.data.split(":", 1)[1])
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    lesson = cur.fetchone()
    conn.close()

    if not lesson:
        await callback.message.answer("❌ Mavzu topilmadi.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎥 Video ko‘rish (+5 ball)", callback_data=f"vd_video:{lesson_id}")],
        [InlineKeyboardButton(text="🖥 Slayd ko‘rish (+5 ball)", callback_data=f"vd_slide:{lesson_id}")],
        [InlineKeyboardButton(text="📝 Test ishlash", callback_data=f"vd_test:{lesson_id}")]
    ])
    await callback.message.answer(f"📖 <b>MAVZU:</b> {lesson['title']}\n🏫 Bosqich: {lesson['class_name']}", reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data.startswith("vd_video:"))
async def lesson_video(callback: CallbackQuery):
    await callback.answer()
    lesson_id = int(callback.data.split(":", 1)[1])
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    lesson = cur.fetchone()
    conn.close()

    if not lesson or not lesson["video_id"]:
        await callback.message.answer("🎥 Bu mavzu uchun video joylanmagan.")
        return

    mark_lesson_viewed(callback.from_user.id, lesson_id)
    await callback.message.answer_video(video=lesson["video_id"], caption=f"🎥 <b>{lesson['title']}</b>", parse_mode="HTML")

@dp.callback_query(F.data.startswith("vd_slide:"))
async def lesson_slide(callback: CallbackQuery):
    await callback.answer()
    lesson_id = int(callback.data.split(":", 1)[1])
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    lesson = cur.fetchone()
    conn.close()

    if not lesson or not lesson["slide_id"]:
        await callback.message.answer("🖥 Bu mavzu uchun slayd joylanmagan.")
        return

    mark_slide_viewed(callback.from_user.id, lesson_id)
    await callback.message.answer_document(document=lesson["slide_id"], caption=f"🖥 <b>{lesson['title']}</b> Slayd (PDF/PPT)", parse_mode="HTML")

@dp.callback_query(F.data.startswith("vd_test:"))
async def start_quiz_test(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    
    lesson_id = int(callback.data.split(":", 1)[1])
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lesson_tests WHERE lesson_id = ? ORDER BY id ASC", (lesson_id,))
    tests = cur.fetchall()
    conn.close()

    if not tests:
        await callback.message.answer("📝 Ushbu mavzu bo'yicha testlar topilmadi.")
        return

    await state.set_state(TestState.answering)
    await state.update_data(
        tests=[dict(t) for t in tests],
        current=0,
        score=0,
        start_time=time.time()
    )
    await display_quiz_question(callback.message, state)

async def display_quiz_question(message: Message, state: FSMContext, edit: bool = False):
    data = await state.get_data()
    tests = data["tests"]
    current = data["current"]

    if current >= len(tests):
        await finish_quiz_test(message, state)
        return

    test = tests[current]
    buttons = [
        [InlineKeyboardButton(text=f"A) {test['option_a']}", callback_data="quiz_ans:A")],
        [InlineKeyboardButton(text=f"B) {test['option_b']}", callback_data="quiz_ans:B")],
    ]
    if test.get('option_c'):
        buttons.append([InlineKeyboardButton(text=f"C) {test['option_c']}", callback_data="quiz_ans:C")])
    if test.get('option_d'):
        buttons.append([InlineKeyboardButton(text=f"D) {test['option_d']}", callback_data="quiz_ans:D")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = f"❓ <b>SAVOL {current + 1}/{len(tests)}</b>\n\n{test['question']}"

    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(TestState.answering, F.data.startswith("quiz_ans:"))
async def process_quiz_answer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tests = data["tests"]
    current = data["current"]
    test = tests[current]

    user_choice = callback.data.split(":", 1)[1]
    correct_choice = test["correct_answer"].upper()

    if user_choice == correct_choice:
        data["score"] += 10
        await callback.answer(text="✅ To'g'ri javob! (+10 ball)", show_alert=True)
    else:
        correct_text = test.get(f"option_{correct_choice.lower()}", correct_choice)
        await callback.answer(text=f"❌ Noto'g'ri!\nTo'g'ri javob: {correct_choice}) {correct_text}", show_alert=True)

    data["current"] += 1
    await state.update_data(current=data["current"], score=data["score"])
    await display_quiz_question(callback.message, state, edit=True)

async def finish_quiz_test(message: Message, state: FSMContext):
    data = await state.get_data()
    total_time = max(1.0, time.time() - data["start_time"])
    total_q = len(data["tests"])
    correct_q = data["score"] // 10
    total_points = data["score"]

    add_test_points(message.from_user.id, total_points)
    await state.clear()

    summary = (
        f"🏆 <b>TEST YAKUNLANDI!</b>\n\n"
        f"⏱ <b>Ketgan vaqt:</b> {total_time:.1f} soniya\n"
        f"🎯 <b>To'g'ri javoblar:</b> {correct_q}/{total_q} ta\n"
        f"⭐ <b>To'plangan ball:</b> +{total_points} ball"
    )

    try:
        await message.edit_text(summary, parse_mode="HTML")
    except Exception:
        await message.answer(summary, parse_mode="HTML")


# ============================================================
# ELEKTRON KUTUBXONA
# ============================================================

@dp.message(F.text == "📚 Elektron kutubxona")
@dp.message(Command("kitob"))
async def library_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("📚 <b>ELEKTRON KUTUBXONA</b>\n\nKerakli sinf yoki bo'limni tanlang:", reply_markup=category_keyboard("lib_class"), parse_mode="HTML")

@dp.callback_query(F.data.startswith("lib_class:"))
async def library_class(callback: CallbackQuery):
    await callback.answer()
    class_name = callback.data.split(":", 1)[1]
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, file_id FROM books WHERE class_name = ? ORDER BY id ASC", (class_name,))
    books = cur.fetchall()
    conn.close()

    if not books:
        await callback.message.answer(f"📚 <b>{class_name}</b>\n\nHozircha darsliklar joylanmagan.", parse_mode="HTML")
        return

    for book in books:
        try:
            await callback.message.answer_document(document=book["file_id"], caption=f"📚 <b>{book['title']}</b>", parse_mode="HTML")
        except Exception as e:
            print(f"Kitob yuborishda xatolik: {e}")


# ============================================================
# UYGA VAZIFA
# ============================================================

@dp.message(F.text == "📝 Uyga vazifa")
@dp.message(Command("uygavazifa"))
async def homework_start(message: Message, state: FSMContext):
    await state.clear()
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❗ Avval /start bosing.")
        return
    await state.set_state(HomeworkState.topic)
    await message.answer("📝 <b>UYGA VAZIFA TOPSHIRISH</b>\n\nTopshirmoqchi bo'lgan uyga vazifa mavzusini yozing:", parse_mode="HTML")

@dp.message(HomeworkState.topic, F.text)
async def homework_topic(message: Message, state: FSMContext):
    topic = (message.text or "").strip()
    await state.update_data(topic=topic)
    await state.set_state(HomeworkState.waiting_file)
    await message.answer("📎 Endi vazifani yuboring (Matn, rasm, video, ovozli xabar yoki fayl ko'rinishida):")

@dp.message(HomeworkState.waiting_file)
async def homework_file_received(message: Message, state: FSMContext):
    data = await state.get_data()
    user = get_user(message.from_user.id)
    
    file_id = None
    file_type = None
    caption = message.caption or message.text or ""

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.voice:
        file_id = message.voice.file_id
        file_type = "voice"
    elif message.text:
        file_type = "text"
        file_id = "text"
    else:
        await message.answer("❗ Iltimos, matn, rasm, video, ovozli xabar yoki fayl yuboring.")
        return

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO homework (user_id, class_name, topic, file_type, file_id, caption, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (message.from_user.id, user["class_name"], data["topic"], file_type, file_id, caption, datetime.now().isoformat()))
    hw_id = cur.lastrowid
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer("✅ Uyga vazifangiz qabul qilindi va ustozga yuborildi! Tez orada baholanadi.")

    admin_text = (
        f"📝 <b>YANGI UYGA VAZIFA KELDI! (ID: #{hw_id})</b>\n\n"
        f"👤 <b>O'quvchi:</b> {user['fullname']} (ID: <code>{user['id']}</code>)\n"
        f"🏫 <b>Sinf/Bosqich:</b> {user['class_name']}\n"
        f"📌 <b>Mavzu:</b> {data['topic']}\n"
        f"💬 <b>Mazmuni/Izoh:</b> {caption}"
    )

    grade_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Baholash (Ball berish)", callback_data=f"admin_grade_hw:{hw_id}:{user['id']}")]
    ])

    try:
        if file_type == "photo":
            await bot.send_photo(ADMIN_ID, photo=file_id, caption=admin_text, reply_markup=grade_kb, parse_mode="HTML")
        elif file_type == "video":
            await bot.send_video(ADMIN_ID, video=file_id, caption=admin_text, reply_markup=grade_kb, parse_mode="HTML")
        elif file_type == "document":
            await bot.send_document(ADMIN_ID, document=file_id, caption=admin_text, reply_markup=grade_kb, parse_mode="HTML")
        elif file_type == "voice":
            await bot.send_voice(ADMIN_ID, voice=file_id, caption=admin_text, reply_markup=grade_kb, parse_mode="HTML")
        elif file_type == "text":
            await bot.send_message(ADMIN_ID, text=admin_text, reply_markup=grade_kb, parse_mode="HTML")
    except Exception as e:
        print(f"Adminga yuborishda xatolik: {e}")


# ============================================================
# TEZ YOZISH (TYPING)
# ============================================================

@dp.message(F.text == "⌨️ Tez yozish")
@dp.message(Command("tezyozish"))
async def typing_menu(message: Message, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Oson", callback_data="typing:oson")],
        [InlineKeyboardButton(text="🟡 O‘rtacha", callback_data="typing:orta")],
        [InlineKeyboardButton(text="🔴 Qiyin", callback_data="typing:qiyin")]
    ])
    await message.answer("⌨️ <b>TEZ YOZISH MASHQI</b>\n\nQiyinchilik darajasini tanlang:", reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data.startswith("typing:"))
async def typing_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    diff = callback.data.split(":", 1)[1]
    if diff not in TYPING_TASKS: return

    tasks = TYPING_TASKS[diff].copy()
    random.shuffle(tasks)
    selected_tasks = tasks[:10]

    await state.set_state(TypingState.writing)
    await state.update_data(
        difficulty=diff,
        tasks=selected_tasks,
        current=0,
        correct=0,
        wrong=0,
        total_started=time.time()
    )
    await send_typing_task(callback.message, state)

async def send_typing_task(message, state):
    data = await state.get_data()
    tasks = data["tasks"]
    current = data["current"]

    if current >= len(tasks):
        await finish_typing(message, state)
        return

    task = tasks[current]
    await message.answer(f"⌨️ Topshiriq: <b>{current + 1}/{len(tasks)}</b>\n\n📌 <code>{task}</code>", parse_mode="HTML")

@dp.message(TypingState.writing, F.text)
async def typing_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    task = data["tasks"][data["current"]]

    if message.text.strip() == task:
        data["correct"] += 1
        await message.answer("✅ To‘g‘ri!")
    else:
        data["wrong"] += 1
        await message.answer(f"❌ Xato! To'g'ri matn: <code>{task}</code>", parse_mode="HTML")

    data["current"] += 1
    await state.update_data(current=data["current"], correct=data["correct"], wrong=data["wrong"])
    await send_typing_task(message, state)

async def finish_typing(message: Message, state: FSMContext):
    data = await state.get_data()
    elapsed = max(1.0, time.time() - data["total_started"])
    correct = data["correct"]
    points = correct * 3

    add_typing_points(message.from_user.id, points)
    await state.clear()

    await message.answer(
        f"🏁 <b>MASHQ YAKUNLANDI!</b>\n\n"
        f"⏱ <b>Ketgan vaqt:</b> {elapsed:.1f} soniya\n"
        f"✅ <b>To'g'ri:</b> {correct} ta\n"
        f"❌ <b>Xato:</b> {data['wrong']} ta\n"
        f"⭐ <b>To'plangan ball:</b> +{points} ball",
        parse_mode="HTML"
    )


# ============================================================
# KOMPYUTER LAYFXAKLARI VA REYTING (YANGILANGAN QISM)
# ============================================================

@dp.message(F.text == "⚡ Kompyuter layfxaklari")
async def lifehacks_menu(message: Message):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM lifehacks ORDER BY id DESC")
    hacks = cur.fetchall()
    conn.close()

    if not hacks:
        await message.answer("⚡ Hozircha kompyuter layfxaklari kiritilmagan.")
        return

    # Har bir mavzu alohida inline tugma (karta) ko'rinishida chiqariladi
    buttons = [[InlineKeyboardButton(text=f"💡 {h['title']}", callback_data=f"lh_show:{h['id']}")] for h in hacks]
    await message.answer(
        "⚡ <b>KOMPYUTER LAYFXAKLARI BO'LIMI</b>\n\nKerakli mavzuni tanlang:", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), 
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("lh_show:"))
async def lifehack_detail(callback: CallbackQuery):
    await callback.answer()
    lh_id = int(callback.data.split(":", 1)[1])
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT title, text, video_id FROM lifehacks WHERE id = ?", (lh_id,))
    hack = cur.fetchone()
    conn.close()

    if not hack:
        await callback.message.answer("❌ Bu layfxak topilmadi yoki o'chib ketgan.")
        return

    msg_text = f"💡 <b>{hack['title']}</b>\n\n📝 <b>Izoh:</b>\n{hack['text']}"
    
    # Agar video biriktirilgan bo'lsa, videosi va izohi birga yuboriladi
    if hack['video_id']:
        await callback.message.answer_video(video=hack['video_id'], caption=msg_text, parse_mode="HTML")
    else:
        await callback.message.answer(msg_text, parse_mode="HTML")

@dp.message(F.text == "🏆 Reyting")
async def show_rating(message: Message):
    rows = get_all_users_rating()
    if not rows:
        await message.answer("🏆 Hozircha reyting ma'lumotlari yo'q.")
        return

    text = "🏆 <b>UMUMIY REYTING (TOP-10):</b>\n\n"
    for idx, r in enumerate(rows[:10], 1):
        name = r["fullname"] if r["fullname"] else f"Foydalanuvchi #{r['user_id']}"
        text += f"{idx}. <b>{name}</b> ({r['class_name'] or '—'}) — <b>{r['total_points']} ball</b>\n"

    await message.answer(text, parse_mode="HTML")


# ============================================================
# USTOZ BILAN BOG'LANISH
# ============================================================

@dp.message(F.text == "👨‍🏫 Ustoz bilan bog‘lanish")
async def teacher_contact(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(TeacherContactState.question)
    await message.answer("💬 Ustozga savol yoki taklifingizni yozib yuboring:")

@dp.message(TeacherContactState.question, F.text)
async def teacher_question_receive(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    question = message.text.strip()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO teacher_questions (user_id, fullname, class_name, question, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (message.from_user.id, user["fullname"], user["class_name"], question, datetime.now().isoformat()))
    q_id = cur.lastrowid
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer("✅ Savolingiz ustozga yetkazildi! Tez orada javob olasiz.")

    reply_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Javob berish", callback_data=f"reply_q:{q_id}:{message.from_user.id}")]
    ])

    await bot.send_message(
        ADMIN_ID,
        f"❓ <b>YANGI SAVOL! (ID: #{q_id})</b>\n\n"
        f"👤 <b>O'quvchi:</b> {user['fullname']} (ID: <code>{message.from_user.id}</code>)\n"
        f"🏫 <b>Sinf:</b> {user['class_name']}\n"
        f"💬 <b>Savol:</b> {question}",
        reply_markup=reply_kb,
        parse_mode="HTML"
    )


# ============================================================
# ADMIN PANEL HANDLERLARI
# ============================================================

@dp.message(F.text == "👨‍💻 ADMIN PANEL")
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    if not is_admin(message.from_user.id):
        return
    await message.answer("👨‍💻 <b>ADMIN PANEL</b>", reply_markup=admin_panel_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "admin_video_menu")
async def admin_video_m(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("🎬 <b>Video darslar va testlar boshqaruvi:</b>", reply_markup=admin_video_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "admin_book_menu")
async def admin_book_m(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("📚 <b>Kitoblar boshqaruvi:</b>", reply_markup=admin_book_keyboard(), parse_mode="HTML")


# ----- KITOB QO'SHISH -----

@dp.callback_query(F.data == "admin_book_add")
async def admin_book_add_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminBookState.class_name)
    await callback.message.answer("📚 Qaysi sinf/bosqich uchun kitob qo'shasiz?", reply_markup=category_keyboard("adm_bk_cls"))

@dp.callback_query(AdminBookState.class_name, F.data.startswith("adm_bk_cls:"))
async def admin_book_add_class(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    class_name = callback.data.split(":", 1)[1]
    await state.update_data(class_name=class_name)
    await state.set_state(AdminBookState.file)
    await callback.message.answer(f"📎 <b>{class_name}</b> uchun kitob faylini (PDF yoki PPT) yuboring:\n\n<i>Kitob nomi fayl nomidan avtomatik olinadi!</i>", parse_mode="HTML")

@dp.message(AdminBookState.file, F.document)
async def admin_book_add_file(message: Message, state: FSMContext):
    data = await state.get_data()
    file_id = message.document.file_id
    book_title = message.document.file_name or "Darslik kitob"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO books (class_name, title, file_id, created_at)
        VALUES (?, ?, ?, ?)
    """, (data["class_name"], book_title, file_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer(f"✅ <b>Kitob muvaffaqiyatli saqlandi!</b>\n📖 Nomi: {book_title}", parse_mode="HTML")

@dp.callback_query(F.data == "admin_books_list")
async def admin_books_list(callback: CallbackQuery):
    await callback.answer()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, class_name, title FROM books ORDER BY id DESC")
    books = cur.fetchall()
    conn.close()

    if not books:
        await callback.message.answer("📚 Kitoblar ro'yxati bo'sh.")
        return

    text = "📚 <b>KITOBLAR RO'YXATI:</b>\n\n"
    for b in books:
        text += f"🆔 <b>{b['id']}</b> | [{b['class_name']}] - {b['title']}\n"
    
    await callback.message.answer(text, parse_mode="HTML")

@dp.callback_query(F.data == "admin_delete_book")
async def admin_delete_book_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminDeleteBookState.book_id)
    await callback.message.answer("🗑 O‘chirmoqchi bo‘lgan **Kitob ID** raqamini yozing:", parse_mode="HTML")

@dp.message(AdminDeleteBookState.book_id, F.text)
async def admin_delete_book_confirm(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗ Faqat son kiriting.")
        return
    book_id = int(message.text)
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer(f"✅ ID #{book_id} kitob o‘chirildi.")


# ----- LAYFXAK QO'SHISH -----

@dp.callback_query(F.data == "admin_lifehack_add")
async def admin_lh_add(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminLifehackState.title)
    await callback.message.answer("⚡ Layfxak mavzusini (sarlavhasini) kiriting:")

@dp.message(AdminLifehackState.title, F.text)
async def admin_lh_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminLifehackState.text)
    await message.answer("📝 Layfxak uchun izoh (matn) kiriting:")

@dp.message(AdminLifehackState.text, F.text)
async def admin_lh_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text.strip())
    await state.set_state(AdminLifehackState.video)
    
    skip_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⏭ Video yo'q (O'tkazib yuborish)", callback_data="skip_lh_video")]])
    await message.answer("🎥 Layfxak uchun video yuboring (yoki pastdagi tugma orqali o'tkazib yuboring):", reply_markup=skip_kb)

@dp.message(AdminLifehackState.video, F.video)
async def admin_lh_video(message: Message, state: FSMContext):
    data = await state.get_data()
    video_id = message.video.file_id

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO lifehacks (title, text, video_id, created_at) VALUES (?, ?, ?, ?)", 
                (data["title"], data["text"], video_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer("✅ <b>Layfxak (video bilan) muvaffaqiyatli saqlandi!</b>", parse_mode="HTML")

@dp.callback_query(AdminLifehackState.video, F.data == "skip_lh_video")
async def admin_lh_skip_video(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO lifehacks (title, text, video_id, created_at) VALUES (?, ?, ?, ?)", 
                (data["title"], data["text"], None, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    await state.clear()
    await callback.message.answer("✅ <b>Layfxak muvaffaqiyatli saqlandi!</b>", parse_mode="HTML")


# ----- O'QUVCHI SAVOLLARI -----

@dp.callback_query(F.data == "admin_questions_list")
async def admin_questions_list(callback: CallbackQuery):
    await callback.answer()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM teacher_questions ORDER BY id DESC LIMIT 15")
    questions = cur.fetchall()
    conn.close()

    if not questions:
        await callback.message.answer("❓ O'quvchilar tomonidan savollar kelmagan.")
        return

    for q in questions:
        status = f"✅ Javob berilgan: {q['answer']}" if q['answer'] else "⏳ Javob berilmagan"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💬 Javob berish", callback_data=f"reply_q:{q['id']}:{q['user_id']}")]])
        text = (
            f"❓ <b>SAVOL ID: #{q['id']}</b>\n"
            f"👤 O'quvchi: <b>{q['fullname']}</b> (ID: <code>{q['user_id']}</code>)\n"
            f"🏫 Sinf: {q['class_name']}\n"
            f"💬 Savol: <b>{q['question']}</b>\n"
            f"📌 Holat: {status}"
        )
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data.startswith("reply_q:"))
async def admin_reply_q_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    _, q_id, u_id = callback.data.split(":")
    await state.set_state(AdminReplyQuestionState.answer_text)
    await state.update_data(question_id=int(q_id), user_id=int(u_id))
    await callback.message.answer(f"✍️ <b>ID #{q_id}</b>-savol egasiga yuboriladigan javob matnini kiriting:", parse_mode="HTML")

@dp.message(AdminReplyQuestionState.answer_text, F.text)
async def admin_reply_q_send(message: Message, state: FSMContext):
    data = await state.get_data()
    answer_text = message.text.strip()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE teacher_questions SET answer = ? WHERE id = ?", (answer_text, data["question_id"]))
    conn.commit()
    conn.close()

    try:
        await bot.send_message(
            data["user_id"],
            f"👨‍🏫 <b>USTOZNING JAVOBI:</b>\n\n💬 {answer_text}",
            parse_mode="HTML"
        )
        await message.answer("✅ Javobingiz o'quvchiga muvaffaqiyatli yetkazildi!")
    except Exception as e:
        await message.answer(f"⚠️ Javob saqlandi, lekin o'quvchiga yuborishda xatolik: {e}")

    await state.clear()


# ----- UYGA VAZIFA BAHOLASH -----

@dp.callback_query(F.data == "admin_homework_list")
async def admin_homework_list(callback: CallbackQuery):
    await callback.answer()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT h.*, u.fullname FROM homework h
        LEFT JOIN users u ON h.user_id = u.id
        ORDER BY h.id DESC LIMIT 15
    """)
    hws = cur.fetchall()
    conn.close()

    if not hws:
        await callback.message.answer("📝 Topshirilgan uyga vazifalar yo'q.")
        return

    for h in hws:
        grade_str = f"⭐ Baholangan: {h['grade']} ball" if h['grade'] is not None else "⏳ Baholanmagan"
        caption = (
            f"📝 <b>UYGA VAZIFA ID: #{h['id']}</b>\n"
            f"👤 O'quvchi: <b>{h['fullname']}</b> (ID: <code>{h['user_id']}</code>)\n"
            f"🏫 Sinf: {h['class_name']}\n"
            f"📌 Mavzu: <b>{h['topic']}</b>\n"
            f"💬 Izoh: {h['caption'] or '—'}\n"
            f"📊 Holat: {grade_str}"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⭐ Baholash", callback_data=f"admin_grade_hw:{h['id']}:{h['user_id']}")]])

        try:
            if h["file_type"] == "photo":
                await callback.message.answer_photo(photo=h["file_id"], caption=caption, reply_markup=kb, parse_mode="HTML")
            elif h["file_type"] == "video":
                await callback.message.answer_video(video=h["file_id"], caption=caption, reply_markup=kb, parse_mode="HTML")
            elif h["file_type"] == "document":
                await callback.message.answer_document(document=h["file_id"], caption=caption, reply_markup=kb, parse_mode="HTML")
            elif h["file_type"] == "voice":
                await callback.message.answer_voice(voice=h["file_id"], caption=caption, reply_markup=kb, parse_mode="HTML")
            else:
                await callback.message.answer(caption, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.answer(caption, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data.startswith("admin_grade_hw:"))
async def admin_grade_hw_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    _, hw_id, u_id = callback.data.split(":")
    await state.set_state(AdminGradeHWState.score)
    await state.update_data(hw_id=int(hw_id), user_id=int(u_id))
    await callback.message.answer(f"⭐ <b>ID #{hw_id}</b> uyga vazifa uchun o'quvchiga nechta ball berilsin?\n\n<i>Faqat raqam yozing (Masalan: 10, 20, 50):</i>", parse_mode="HTML")

@dp.message(AdminGradeHWState.score, F.text)
async def admin_grade_hw_save(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗ Faqat son kiriting!")
        return

    score = int(message.text)
    data = await state.get_data()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE homework SET grade = ? WHERE id = ?", (score, data["hw_id"]))
    conn.commit()
    conn.close()

    add_homework_points(data["user_id"], score)

    try:
        await bot.send_message(
            data["user_id"],
            f"🎉 <b>UYGA VAZIFAINGIZ BAHOLANDI!</b>\n\n⭐ Sizning uyga vazifangiz ustoz tomonidan <b>+{score} ball</b> bilan baholandi!",
            parse_mode="HTML"
        )
        await message.answer(f"✅ ID #{data['hw_id']} vazifa baholandi va o'quvchiga +{score} ball qo'shildi!")
    except Exception as e:
        await message.answer(f"✅ Baho saqlandi, lekin o'quvchiga xabar yuborilmadi: {e}")

    await state.clear()


# ----- O'QUVCHILARNI BOSHQARISH -----

@dp.callback_query(F.data == "admin_students_menu")
async def admin_students_menu(callback: CallbackQuery):
    await callback.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Barcha o'quvchilar ro'yxati", callback_data="admin_students_list")],
        [InlineKeyboardButton(text="✏️ O'quvchi ma'lumotlarini tahrirlash", callback_data="admin_edit_student_start")],
        [InlineKeyboardButton(text="🔄 O'quvchi natijalarini nolga tushirish (Reset)", callback_data="admin_reset_student_start")],
        [InlineKeyboardButton(text="🚫 O'quvchini botdan chiqarish (Bloklash)", callback_data="admin_ban_student_start")]
    ])
    await callback.message.answer("👥 <b>O'QUVCHILARNI BOSHQARISH</b>", reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "admin_students_list")
async def admin_students_list(callback: CallbackQuery):
    await callback.answer()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, fullname, class_name, is_banned FROM users ORDER BY id DESC")
    users = cur.fetchall()
    conn.close()

    if not users:
        await callback.message.answer("👥 O'quvchilar topilmadi.")
        return

    text = "👥 <b>O'QUVCHILAR RO'YXATI:</b>\n\n"
    for u in users:
        status = "🔴 (Bloklangan)" if u["is_banned"] == 1 else "🟢"
        text += f"{status} ID: <code>{u['id']}</code> | <b>{u['fullname'] or '—'}</b> | {u['class_name'] or '—'}\n"

    await callback.message.answer(text, parse_mode="HTML")

@dp.callback_query(F.data == "admin_edit_student_start")
async def admin_edit_student_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminManageStudentState.target_user_id)
    await callback.message.answer("✏️ Tahrirlamoqchi bo'lgan **O'quvchi ID** raqamini kiriting:", parse_mode="HTML")

@dp.message(AdminManageStudentState.target_user_id, F.text)
async def admin_edit_student_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗ Faqat son kiriting.")
        return
    u_id = int(message.text)
    user = get_user(u_id)
    if not user:
        await message.answer("❌ Bunday ID ga ega o'quvchi topilmadi.")
        await state.clear()
        return

    await state.update_data(target_user_id=u_id)
    await state.set_state(AdminManageStudentState.new_fullname)
    await message.answer(f"👤 O'quvchining yangi **Ism va familiyasi**ni kiriting (Hozirgi: {user['fullname']}):", parse_mode="HTML")

@dp.message(AdminManageStudentState.new_fullname, F.text)
async def admin_edit_student_name(message: Message, state: FSMContext):
    await state.update_data(new_fullname=message.text.strip())
    await state.set_state(AdminManageStudentState.new_class)
    await message.answer("🏫 O'quvchi uchun yangi sinf/bosqichni tanlang:", reply_markup=category_keyboard("adm_std_cls"))

@dp.callback_query(AdminManageStudentState.new_class, F.data.startswith("adm_std_cls:"))
async def admin_edit_student_class(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    new_class = callback.data.split(":", 1)[1]
    data = await state.get_data()

    update_user(data["target_user_id"], fullname=data["new_fullname"], class_name=new_class)
    await state.clear()
    await callback.message.answer(f"✅ O'quvchi ma'lumotlari muvaffaqiyatli yangilandi!\n\n👤 {data['new_fullname']}\n🏫 {new_class}")

@dp.callback_query(F.data == "admin_reset_student_start")
async def admin_reset_student_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("🔄 Natijalari (ballari) nolga tushiriladigan **O'quvchi ID** raqamini yozing:", parse_mode="HTML")
    await state.set_state("waiting_reset_student_id")

@dp.message(StateFilter("waiting_reset_student_id"), F.text)
async def admin_reset_student_confirm(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗ Faqat son kiriting.")
        return
    u_id = int(message.text)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE rating SET lesson_points=0, slide_points=0, test_points=0, typing_points=0, homework_points=0
        WHERE user_id = ?
    """, (u_id,))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer(f"✅ ID <code>{u_id}</code> o'quvchining barcha ballari va natijalari 0 ga tushirildi!", parse_mode="HTML")

@dp.callback_query(F.data == "admin_ban_student_start")
async def admin_ban_student_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("🚫 Botdan chiqariladigan (bloklanadigan) **O'quvchi ID** raqamini yozing:", parse_mode="HTML")
    await state.set_state("waiting_ban_student_id")

@dp.message(StateFilter("waiting_ban_student_id"), F.text)
async def admin_ban_student_confirm(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗ Faqat son kiriting.")
        return
    u_id = int(message.text)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_banned = 1 WHERE id = ?", (u_id,))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer(f"✅ ID <code>{u_id}</code> o'quvchi botdan chiqarildi (bloklandi)!", parse_mode="HTML")


# ----- DARSLAR VA TESTLAR -----

@dp.callback_query(F.data == "admin_add_lesson")
async def admin_add_lesson_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminLessonState.class_name)
    await callback.message.answer("🏫 Qaysi sinf/bosqich uchun mavzu qo'shmoqchisiz?", reply_markup=category_keyboard("adm_less_cls"))

@dp.callback_query(AdminLessonState.class_name, F.data.startswith("adm_less_cls:"))
async def admin_add_lesson_class(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    class_name = callback.data.split(":", 1)[1]
    await state.update_data(class_name=class_name)
    await state.set_state(AdminLessonState.title)
    await callback.message.answer(f"📌 <b>{class_name}</b> uchun mavzu nomini kiriting:")

@dp.message(AdminLessonState.title, F.text)
async def admin_add_lesson_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminLessonState.video)
    
    skip_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⏭ O'tkazib yuborish (Video yo'q)", callback_data="skip_video")]])
    await message.answer("🎥 Mavzu uchun video darslik yuboring:", reply_markup=skip_kb)

@dp.message(AdminLessonState.video, F.video)
async def admin_add_lesson_video(message: Message, state: FSMContext):
    await state.update_data(video_id=message.video.file_id)
    await ask_lesson_slide(message, state)

@dp.callback_query(AdminLessonState.video, F.data == "skip_video")
async def admin_skip_video(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(video_id=None)
    await ask_lesson_slide(callback.message, state)

async def ask_lesson_slide(message: Message, state: FSMContext):
    await state.set_state(AdminLessonState.slide)
    skip_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⏭ O'tkazib yuborish (Slayd yo'q)", callback_data="skip_slide")]])
    await message.answer("🖥 Mavzu uchun slayd faylini (PDF yoki PPT/PPTX) yuboring:", reply_markup=skip_kb)

@dp.message(AdminLessonState.slide, F.document)
async def admin_add_lesson_slide(message: Message, state: FSMContext):
    data = await state.get_data()
    slide_id = message.document.file_id
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO lessons (class_name, title, video_id, slide_id, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (data["class_name"], data["title"], data.get("video_id"), slide_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer("✅ <b>Yangi mavzu va slayd muvaffaqiyatli saqlandi!</b>", parse_mode="HTML")

@dp.callback_query(AdminLessonState.slide, F.data == "skip_slide")
async def admin_skip_slide(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO lessons (class_name, title, video_id, slide_id, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (data["class_name"], data["title"], data.get("video_id"), None, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer("✅ <b>Yangi mavzu saqlandi!</b>", parse_mode="HTML")

@dp.callback_query(F.data == "admin_lessons_list")
async def admin_lessons_list(callback: CallbackQuery):
    await callback.answer()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, class_name, title FROM lessons ORDER BY id DESC LIMIT 20")
    lessons = cur.fetchall()
    conn.close()

    if not lessons:
        await callback.message.answer("📚 Mavzular ro'yxati bo'sh.")
        return

    text = "📚 <b>MAVZULAR RO'YXATI:</b>\n\n"
    for l in lessons:
        text += f"🆔 <b>{l['id']}</b> | [{l['class_name']}] - {l['title']}\n"
    
    await callback.message.answer(text, parse_mode="HTML")

@dp.callback_query(F.data == "admin_delete_lesson")
async def admin_delete_lesson_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminDeleteLessonState.lesson_id)
    await callback.message.answer("🗑 O‘chirmoqchi bo‘lgan **Mavzu ID** raqamini yozing:", parse_mode="HTML")

@dp.message(AdminDeleteLessonState.lesson_id, F.text)
async def admin_delete_lesson_confirm(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗ Faqat son kiriting.")
        return
    lesson_id = int(message.text)
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
    cur.execute("DELETE FROM lesson_tests WHERE lesson_id = ?", (lesson_id,))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer(f"✅ ID #{lesson_id} mavzu va unga tegishli testlar o‘chirildi.")

@dp.callback_query(F.data == "admin_add_single_test")
async def admin_add_single_test_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminTestState.lesson_id)
    await callback.message.answer("📝 Test qo'shiladigan **Mavzu ID** raqamini yozing:", parse_mode="HTML")

@dp.message(AdminTestState.lesson_id, F.text)
async def admin_test_lesson_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗ Faqat son kiriting.")
        return
    await state.update_data(lesson_id=int(message.text))
    await state.set_state(AdminTestState.question)
    await message.answer("❓ Savol matnini kiriting:")

@dp.message(AdminTestState.question, F.text)
async def admin_test_q(message: Message, state: FSMContext):
    await state.update_data(question=message.text.strip())
    await state.set_state(AdminTestState.option_a)
    await message.answer("🔹 A variantni kiriting:")

@dp.message(AdminTestState.option_a, F.text)
async def admin_test_opt_a(message: Message, state: FSMContext):
    await state.update_data(option_a=message.text.strip())
    await state.set_state(AdminTestState.option_b)
    await message.answer("🔹 B variantni kiriting:")

@dp.message(AdminTestState.option_b, F.text)
async def admin_test_opt_b(message: Message, state: FSMContext):
    await state.update_data(option_b=message.text.strip())
    await state.set_state(AdminTestState.option_c)
    await message.answer("🔹 C variantni kiriting:")

@dp.message(AdminTestState.option_c, F.text)
async def admin_test_opt_c(message: Message, state: FSMContext):
    await state.update_data(option_c=message.text.strip())
    await state.set_state(AdminTestState.option_d)
    await message.answer("🔹 D variantni kiriting:")

@dp.message(AdminTestState.option_d, F.text)
async def admin_test_opt_d(message: Message, state: FSMContext):
    await state.update_data(option_d=message.text.strip())
    await state.set_state(AdminTestState.correct)
    await message.answer("🎯 To'g'ri javob kalitini kiriting (A, B, C yoki D):")

@dp.message(AdminTestState.correct, F.text)
async def admin_test_correct(message: Message, state: FSMContext):
    correct = message.text.strip().upper()
    if correct not in ["A", "B", "C", "D"]:
        await message.answer("❗ Faqat A, B, C yoki D harflaridan birini kiriting.")
        return
    
    data = await state.get_data()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO lesson_tests (lesson_id, question, option_a, option_b, option_c, option_d, correct_answer, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data["lesson_id"], data["question"], data["option_a"], data["option_b"], data["option_c"], data["option_d"], correct, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer("✅ Test muvaffaqiyatli saqlandi!")

@dp.callback_query(F.data == "admin_add_bulk_test")
async def start_bulk_test_add(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminBulkTestState.lesson_id)
    await callback.message.answer("📝 Testlar qo'shiladigan <b>Mavzu ID</b> raqamini yozing:", parse_mode="HTML")

@dp.message(AdminBulkTestState.lesson_id, F.text)
async def process_bulk_lesson_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗ Faqat son kiriting.")
        return
    await state.update_data(lesson_id=int(message.text))
    await state.set_state(AdminBulkTestState.raw_tests)
    await message.answer("📥 Barcha testlarni bitta xabarda yuboring:")

@dp.message(AdminBulkTestState.raw_tests, F.text)
async def process_bulk_tests_text_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    lesson_id = data["lesson_id"]
    
    parsed_tests = parse_bulk_tests_text(message.text)

    if not parsed_tests:
        await message.answer("❌ Birorta ham test aniqlanmadi. Matn formatini tekshirib qayta yuboring.")
        return

    conn = get_connection()
    cur = conn.cursor()
    saved_count = 0

    for t in parsed_tests:
        cur.execute("""
            INSERT INTO lesson_tests (lesson_id, question, option_a, option_b, option_c, option_d, correct_answer, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (lesson_id, t["question"], t["option_a"], t["option_b"], t["option_c"], t["option_d"], t["correct"], datetime.now().isoformat()))
        saved_count += 1

    conn.commit()
    conn.close()

    await state.clear()
    await message.answer(f"✅ <b>{saved_count} ta test</b> muvaffaqiyatli tahlil qilindi va bazaga saqlandi!", parse_mode="HTML")

@dp.callback_query(F.data == "admin_tests_list_btn")
async def admin_tests_list(callback: CallbackQuery):
    await callback.answer()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, lesson_id, question FROM lesson_tests ORDER BY id DESC LIMIT 20")
    tests = cur.fetchall()
    conn.close()

    if not tests:
        await message.answer("📝 Testlar ro'yxati bo'sh.")
        return

    text = "📋 <b>TESTLAR RO'YXATI:</b>\n\n"
    for t in tests:
        text += f"🆔 <b>{t['id']}</b> (Mavzu ID: {t['lesson_id']}): {t['question'][:30]}...\n"
    
    await callback.message.answer(text, parse_mode="HTML")

@dp.callback_query(F.data == "admin_delete_test_btn")
async def admin_delete_test_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AdminDeleteTestState.test_id)
    await callback.message.answer("🗑 O‘chirmoqchi bo‘lgan **Test ID** raqamini yozing:", parse_mode="HTML")

@dp.message(AdminDeleteTestState.test_id, F.text)
async def admin_delete_test_confirm(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗ Faqat son kiriting.")
        return
    test_id = int(message.text)
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM lesson_tests WHERE id = ?", (test_id,))
    conn.commit()
    conn.close()

    await state.clear()
    await message.answer(f"✅ ID #{test_id} test o‘chirildi.")


# ============================================================
# NOMA'LUM MATNLAR (FALLBACK) - FAQAT DEFAULT STATE UCHUN
# ============================================================

@dp.message(StateFilter(default_state), F.text)
async def unknown_text_handler(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)

    if user and user["fullname"] and user["class_name"]:
        markup = admin_menu() if is_admin(user_id) else main_menu()
        await message.answer(
            "⚠️ <b>Iltimos, bo‘limni tanlang!</b>\n\n"
            "Tushunarsiz matn kiritdingiz. Davom etish uchun quyidagi menyu tugmalaridan birini tanlang 👇",
            reply_markup=markup,
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "⚠️ <b>Siz hali ro‘yxatdan o‘tmagansiz!</b>\n\n"
            "Botdan foydalanish uchun /start buyrug‘ini bosing.",
            parse_mode="HTML"
        )


# ============================================================
# BOTNI ISHGA TUSHIRISH
# ============================================================

async def main():
    dp.message.outer_middleware(BanCheckMiddleware())
    dp.callback_query.outer_middleware(BanCheckMiddleware())
    
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot muvaffaqiyatli ishga tushdi...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi!")
