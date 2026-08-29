HTTP API:
"8765983282:AAFxz0d0swqoQZhOTmeXNrFPhcuKQEZuBJw"
import os
import logging
import sqlite3
from typing import Optional
import telebot
from telebot import types

# --- 1. Configure Professional Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("intelligence_core.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger: logging.Logger = logging.getLogger("TeamX-Intelligence-Core")

# --- 2. Database Initialization (SQLite) ---
def init_db() -> None:
    with sqlite3.connect("teamx_intel.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

def log_action(user_id: int, username: str, action: str) -> None:
    try:
        with sqlite3.connect("teamx_intel.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO security_logs (user_id, username, action) VALUES (?, ?, ?)",
                (user_id, username, action)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Database error: {e}")

# --- 3. Secure Token Initialization ---
TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    logger.critical("❌ Critical Error: Bot token is missing.")
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable must be set.")

# --- 4. Initialize Bot Instance ---
bot = telebot.TeleBot(TOKEN, parse_mode="MarkdownV2")

# --- Helper: Escape MarkdownV2 special characters ---
def escape_markdown(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

# --- Error Handler ---
def handle_error(message: types.Message, error: Exception, custom_msg: Optional[str] = None) -> None:
    logger.error(f"Error in chat [{message.chat.id}] by user [{message.from_user.id}]: {error}")
    error_text = custom_msg or "❌ حدث خطأ داخلي في النظام الاستخباراتي. يرجى المحاولة لاحقاً."
    try:
        bot.reply_to(message, escape_markdown(error_text))
    except Exception as ex:
        logger.error(f"Failed to dispatch error reply: {ex}")

# --- Admin Check Helper ---
def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ["creator", "administrator"]
    except Exception as e:
        logger.error(f"Failed to check admin status: {e}")
        return False

# --- /start Command ---
@bot.message_handler(commands=['start'])
def send_welcome(message: types.Message) -> None:
    try:
        welcome_text = (
            "🌟 *مرحباً بك أيها القائد في النواة المتقدمة لفريق X.* \n\n"
            "النظام الآن مربوط بقاعدة البيانات المحلية وجاهز للمهام الاستخباراتية. \n\n"
            "📌 *الأوامر المتاحة للنظام:*\n"
            "• `/start` - تفعيل النظام وبدء الجلسة\n"
            "• `/whois` - فحص واستخراج بيانات عنصر (بالرد على رسالته)\n"
            "• `/echo [نص]` - اختبار الاستجابة وترديد النص\n"
            "• `/info` - تقرير حالة النظام والنسخة\n"
            "• `/ban` - حظر عنصر مشبوه (للمشرفين فقط)\n"
            "• `/kick` - طرد عنصر من الشبكة (للمشرفين فقط)"
        )
        bot.reply_to(message, welcome_text)
    except Exception as e:
        handle_error(message, e)

# --- /whois Command (Intelligence Feature) ---
@bot.message_handler(commands=['whois'])
def whois_command(message: types.Message) -> None:
    try:
        if not message.reply_to_message:
            bot.reply_to(message, escape_markdown("⚠️ يرجى الرد على رسالة الشخص المستهدف لجلب تقريره الاستخباراتي."))
            return

        target = message.reply_to_message.from_user
        user_id = target.id
        username = target.username or "لا يوجد"
        first_name = target.first_name or "غير معروف"
        is_bot = "نعم" if target.is_bot else "لا"

        report = (
            "🕵️‍♂️ *تقرير استعلام عن عنصر (Whois)*\n\n"
            f"🆔 *معرف المستخدم (ID):* `{user_id}`\n"
            f"👤 *الاسم الأول:* {first_name}\n"
            f"🔗 *اسم المستخدم:* @{username}\n"
            f"🤖 *هل هو بوت؟:* {is_bot}"
        )
        log_action(message.from_user.id, message.from_user.username or "unknown", "WHOIS_CHECK")
        bot.reply_to(message, report)
    except Exception as e:
        handle_error(message, e, "❌ فشل استخراج بيانات العنصر.")

# --- /echo Command ---
@bot.message_handler(commands=['echo'])
def echo_command(message: types.Message) -> None:
    try:
        parts = message.text.split(maxsplit=1)
        text = parts[1] if len(parts) > 1 else ""
        if text:
            response = f"🔁 *تأكيد استلام الإشارة:* `{text}`"
            bot.reply_to(message, response)
        else:
            bot.reply_to(message, escape_markdown("⚠️ يرجى إرفاق النص بعد الأمر. مثال: `/echo تفعيل`"))
    except Exception as e:
        handle_error(message, e)

# --- /info Command ---
@bot.message_handler(commands=['info'])
def send_info(message: types.Message) -> None:
    try:
        info_text = (
            "ℹ️ *تقرير حالة النظام الاستخباراتي* \n\n"
            "🤖 *اسم النظام:* Team X Intelligence Core (DB Enabled)\n"
            "📊 *الإصدار الميداني:* 3.0 Pro\n"
            "👨‍💻 *المطور الرئيسي:* فريق X (نصرالدين)\n"
            "🌍 *البيئة البرمجية:* Python + SQLite3"
        )
        bot.reply_to(message, info_text)
    except Exception as e:
        handle_error(message, e)

# --- /ban Command (Admin Only) ---
@bot.message_handler(commands=['ban'])
def ban_user(message: types.Message) -> None:
    try:
        if message.chat.type not in ["group", "supergroup"]:
            bot.reply_to(message, escape_markdown("⚠️ هذا الأمر حصري للعمليات الجماعية داخل المجموعات."))
            return

        if not is_admin(message.chat.id, message.from_user.id):
            bot.reply_to(message, escape_markdown("❌ مرفوض: ليس لديك صلاحيات إدارية كافية لتنفيذ هذا الأمر."))
            return

        if not message.reply_to_message:
            bot.reply_to(message, escape_markdown("⚠️ يرجى الرد على رسالة العنصر المستهدف لتنفيذ الحظر."))
            return

        target_user = message.reply_to_message.from_user
        bot.ban_chat_member(message.chat.id, target_user.id)
        name = target_user.username or target_user.first_name
        log_action(message.from_user.id, message.from_user.username or "unknown", f"BAN_USER_{target_user.id}")
        bot.reply_to(message, escape_markdown(f"❌ تم حظر العنصر [{name}] نهائياً من الشبكة بنجاح وتسجيل العملية."))
    except Exception as e:
        handle_error(message, e, "❌ فشل تنفيذ عملية الحظر.")

# --- /kick Command (Admin Only) ---
@bot.message_handler(commands=['kick'])
def kick_user(message: types.Message) -> None:
    try:
        if message.chat.type not in ["group", "supergroup"]:
            bot.reply_to(message, escape_markdown("⚠️ هذا الأمر حصري للعمليات الجماعية داخل المجموعات."))
            return

        if not is_admin(message.chat.id, message.from_user.id):
            bot.reply_to(message, escape_markdown("❌ مرفوض: ليس لديك صلاحيات إدارية كافية لتنفيذ هذا الأمر."))
            return

        if not message.reply_to_message:
            bot.reply_to(message, escape_markdown("⚠️ يرجى الرد على رسالة العنصر المستهدف لطرده."))
            return

        target_user = message.reply_to_message.from_user
        bot.kick_chat_member(message.chat.id, target_user.id)  # Corrected: Use kick_chat_member
        name = target_user.username or target_user.first_name
        log_action(message.from_user.id, message.from_user.username or "unknown", f"KICK_USER_{target_user.id}")
        bot.reply_to(message, escape_markdown(f"🚪 تم إخراج العنصر [{name}] من النطاق وتسجيل العملية."))
    except Exception as e:
        handle_error(message, e, "❌ فشل تنفيذ عملية الطرد.")

# --- General Message Handler ---
@bot.message_handler(func=lambda message: True)
def secure_listener(message: types.Message) -> None:
    try:
        if message.text:
            logger.info(f"Received message from chat {message.chat.id}: {message.text[:30]}...")
    except Exception as e:
        handle_error(message, e)

# --- Core Execution Loop ---
if __name__ == "__main__":
    logger.info("🛡️ Team X Intelligence Bot Core (v3.0) is active and logging operations...")
    try:
        bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=20)
    except Exception as critical_err:
        logger.critical(f"🔥 Fatal core collapse: {critical_err}")
