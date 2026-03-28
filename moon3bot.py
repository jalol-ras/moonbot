import telebot
from telebot import types
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8023802405:AAENHfz3hu4fHGofQPug4PyMmwxVKozkv7U"
GROUP_ID = -1003531497426
ADMIN_ID = 8064975342 # твой ID

bot = telebot.TeleBot(TOKEN)

db = sqlite3.connect("database.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    inviter_id INTEGER,
    stars REAL DEFAULT 0,
    invites INTEGER DEFAULT 0,
    joined INTEGER DEFAULT 0
)
""")
db.commit()


# --- МЕНЮ ---
def menu(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👤 Профиль", "🏆 Топ")
    kb.add("🔗 Моя ссылка")

    # если админ
    if user_id == ADMIN_ID:
        kb.add("👑 Админ панель")

    return kb


# --- АДМИН МЕНЮ ---
def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📊 Статистика", "👥 Пользователи")
    kb.add("💰 Выдать звезды")
    kb.add("🔙 Назад")
    return kb


# --- КНОПКА АДМИН ПАНЕЛИ ---
@bot.message_handler(func=lambda m: m.text == "👑 Админ панель")
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return

    bot.send_message(
        message.chat.id,
        "👑 Админ панель\n\nВыбери действие 👇",
        reply_markup=admin_menu()
    )
# --- СТАРТ ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    args = message.text.split()
    inviter = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    # --- РЕГИСТРАЦИЯ ---
    if not user:
        if inviter == user_id:
            inviter = None

        cursor.execute(
            "INSERT INTO users (user_id, username, inviter_id) VALUES (?, ?, ?)",
            (user_id, username, inviter)
        )
        db.commit()

    # --- ССЫЛКА ---
    ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"

    # --- КНОПКА В ЧАТ ---
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🚀 Перейти в чат", url="https://t.me/moonlight_relaxes")
    )

    # --- СООБЩЕНИЕ ---
    bot.send_message(
        message.chat.id,
        f"👋 Привет, {username}!\n\n"
        f"🌙 Добро пожаловать в MoonLight Relaxes\n\n"
        f"💎 Здесь ты можешь:\n"
        f"— приглашать друзей\n"
        f"— получать ⭐ за каждого\n"
        f"— попадать в топ\n\n"
        f"🎁 Награда: +2.5⭐ за каждого друга\n\n"
        f"❗ ВАЖНО:\n"
        f"1. Нажми /start\n"
        f"2. Потом заходи в чат\n\n"
        f"🔗 Твоя ссылка:\n{ref_link}",
        reply_markup=markup
    )

    # --- МЕНЮ ---
    bot.send_message(
        message.chat.id,
        "👇 Выбирай действие:",
       reply_markup=menu(user_id)
    )
@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats(message):
    if message.from_user.id != ADMIN_ID:
        return

    users_count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_stars = cursor.execute("SELECT SUM(stars) FROM users").fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"📊 Статистика\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"⭐ Всего звёзд: {total_stars}"
    )

# --- ССЫЛКА ---
@bot.message_handler(func=lambda m: m.text == "🔗 Моя ссылка")
def ref(message):
    link = f"https://t.me/{bot.get_me().username}?start={message.from_user.id}"

    bot.send_message(
        message.chat.id,
        f"🔗 Твоя личная ссылка:\n\n{link}\n\n"
        f"💎 За каждого друга: +2.5⭐"
    )

@bot.message_handler(func=lambda m: m.text == "👥 Пользователи")
def users_list(message):
    if message.from_user.id != ADMIN_ID:
        return

    users = cursor.execute("SELECT username, stars FROM users").fetchall()

    text = "👥 Пользователи:\n\n"

    for u in users[:20]:
        text += f"{u[0]} — ⭐ {u[1]}\n"

    bot.send_message(message.chat.id, text)
@bot.message_handler(func=lambda m: m.text == "🔙 Назад")
def back(message):
    bot.send_message(
        message.chat.id,
        "🔙 Главное меню",
        reply_markup=menu(message.from_user.id)
    )

# --- ПРОФИЛЬ ---
@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    user = cursor.execute(
        "SELECT stars, invites FROM users WHERE user_id=?",
        (message.from_user.id,)
    ).fetchone()

    if user:
        stars, invites = user
        level = get_level(stars)

        bot.send_message(
            message.chat.id,
            f"👤 Твой профиль\n\n"
            f"🏆 Уровень: {level}\n"
            f"👥 Пригласил: {invites}\n"
            f"⭐ Звёзды: {stars}"
        )

# --- ТОП 5 ---
@bot.message_handler(func=lambda m: m.text == "🏆 Топ")
def top(message):
    top_users = cursor.execute(
        "SELECT username, invites FROM users ORDER BY invites DESC LIMIT 5"
    ).fetchall()

    text = "🏆 Топ приглашений:\n\n"

    for i, user in enumerate(top_users, 1):
        text += f"{i}. {user[0]} — {user[1]} чел.\n"

    bot.send_message(message.chat.id, text)

# --- АДМИН ПАНЕЛЬ ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return

    users_count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_stars = cursor.execute("SELECT SUM(stars) FROM users").fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"👑 Админ панель\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"⭐ Всего звёзд: {total_stars}"
    )

@bot.message_handler(commands=['users'])
def users_list(message):
    if message.from_user.id != ADMIN_ID:
        return

    users = cursor.execute("SELECT username, stars FROM users").fetchall()

    text = "📊 Пользователи:\n\n"

    for u in users[:20]:
        text += f"{u[0]} — ⭐ {u[1]}\n"

    bot.send_message(message.chat.id, text)

# --- ВХОД В ГРУППУ ---
@bot.message_handler(content_types=['new_chat_members'])
def join_group(message):
    if message.chat.id != GROUP_ID:
        return

    for u in message.new_chat_members:
        user_id = u.id
        print("Зашёл:", user_id)
        data = cursor.execute(
            "SELECT inviter_id, joined FROM users WHERE user_id=?",
            (user_id,)
        ).fetchone()

        if not data or not data[0] or data[1] == 1:
            return

        inviter_id = data[0]

        # начисление
        cursor.execute(
            "UPDATE users SET stars = stars + 2.5, invites = invites + 1 WHERE user_id=?",
            (inviter_id,)
        )

        cursor.execute(
            "UPDATE users SET joined = 1 WHERE user_id=?",
            (user_id,)
        )

        db.commit()

        # имя пригласившего (БЕЗ ОШИБКИ)
        result = cursor.execute(
            "SELECT username FROM users WHERE user_id=?",
            (inviter_id,)
        ).fetchone()

        if result:
            inviter_name = result[0]
        else:
            inviter_name = "Неизвестный"

        text = (
            f"🎉 Новый участник!\n\n"
            f"👤 {u.first_name} зашёл по ссылке {inviter_name}\n"
            f"⭐ {inviter_name} получил +2.5 звезды"
        )

        bot.send_message(GROUP_ID, text)
        bot.send_message(inviter_id, text)

# --- ВЫХОД ---
@bot.message_handler(content_types=['left_chat_member'])
def leave_group(message):
    if message.chat.id != GROUP_ID:
        return

    user_id = message.left_chat_member.id

    inviter = cursor.execute(
        "SELECT inviter_id FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()

    if inviter and inviter[0]:
        bot.send_message(
            ADMIN_ID,
            f"⚠️ Участник вышел\n\n"
            f"👤 {message.left_chat_member.first_name}\n"
            f"Был приглашён ID: {inviter[0]}"
        )

# --- УРОВНИ ---
def get_level(stars):
    if stars >= 50:
        return "🔥 Легенда"
    elif stars >= 30:
        return "🟣 Топ"
    elif stars >= 15:
        return "🔵 Продвинутый"
    elif stars >= 5:
        return "🟢 Активный"
    else:
        return "🐣 Новичок"
print("✅ Бот успешно запущен и работает!")

bot.infinity_polling()

