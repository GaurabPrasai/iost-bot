from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from db import add_subscriber, get_subscriber, update_subscriber, delete_subscriber, get_recent_notices

COURSE_DISPLAY = {
    "CSIT":  "B.Sc.CSIT",
    "BIT":   "BIT",
    "BTECH": "B.Tech (Food Technology)",
    "MSC":   "M.Sc.",
    "BSC":   "B.Sc.",
}

# Maps keyboard button text → internal course code
COURSE_MAP = {
    "CSIT":           "CSIT",
    "BIT":            "BIT",
    "B.TECH FOOD":    "BTECH",
    "M.SC.":          "MSC",
    "B.SC.":          "BSC",
}

CURRENT_NEPALI_YEAR = 2083
VALID_BATCH_RANGE   = range(2074, CURRENT_NEPALI_YEAR + 1)


# ── Commands ───────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[Bot] /start received from {update.effective_chat.id}")  # add this
    chat_id  = update.effective_chat.id
    username = update.effective_user.username

    add_subscriber(chat_id, username)
    update_subscriber(chat_id, state="AWAITING_COURSE")

    keyboard = [
        ["CSIT", "BIT"],
        ["B.Tech Food", "M.Sc."],
        ["B.Sc."],
    ]
    await update.message.reply_text(
        "Welcome to IOST Notice Bot 🎓\n\n"
        "Get instant notifications for exam schedules, form filling deadlines, "
        "results, and all important notices — filtered for your course.\n\n"
        "Which course are you in?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *IOST Notice Bot*\n\n"
        "/start — Register or re-register\n"
        "/mystatus — See your current registration\n"
        "/unsubscribe — Stop receiving notices\n"
        "/help — Show this message\n\n"
        "Notices are checked every 5 minutes. You'll only receive notices "
        "relevant to your course and batch year.",
        parse_mode="Markdown",
    )


async def mystatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id    = update.effective_chat.id
    subscriber = get_subscriber(chat_id)

    if not subscriber or subscriber["state"] != "REGISTERED":
        await update.message.reply_text(
            "You're not registered yet. Send /start to get started."
        )
        return

    course = COURSE_DISPLAY.get(subscriber["course"], subscriber["course"])
    await update.message.reply_text(
        f"✅ *Your Registration*\n\n"
        f"Course: {course}\n"
        f"Batch Year: {subscriber['batch_year']} BS",
        parse_mode="Markdown",
    )


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    delete_subscriber(chat_id)
    await update.message.reply_text(
        "You've been unsubscribed. You won't receive any more notices.\n"
        "Send /start anytime to re-register.",
        reply_markup=ReplyKeyboardRemove(),
    )
async def latest(update, context):
    chat_id    = update.effective_chat.id
    subscriber = get_subscriber(chat_id)

    if not subscriber or subscriber["state"] != "REGISTERED":
        await update.message.reply_text("Register first with /start.")
        return

    notices = get_recent_notices(subscriber["course"])

    if not notices:
        await update.message.reply_text("No notices found yet.")
        return

    for notice in notices:
        await update.message.reply_text(
            f"📢 {notice['title']}\n\n🔗 {notice['url']}\n📅 {notice['detected_at']}"
        )


# ── Message handler (registration flow) ───────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id    = update.effective_chat.id
    text       = update.message.text.strip()
    subscriber = get_subscriber(chat_id)

    if not subscriber:
        await update.message.reply_text("Send /start to register first.")
        return

    state = subscriber["state"]

    # ── Step 1: user picks a course ──
    if state == "AWAITING_COURSE":
        course = COURSE_MAP.get(text.upper().replace(".", "").replace(" ", " "))

        # Try a looser match in case of slight button text variation
        if not course:
            for key, val in COURSE_MAP.items():
                if key in text.upper():
                    course = val
                    break

        if not course:
            await update.message.reply_text(
                "Please choose a course using the buttons below."
            )
            return

        update_subscriber(chat_id, course=course, state="AWAITING_BATCH")
        await update.message.reply_text(
            f"Got it — *{COURSE_DISPLAY[course]}* ✅\n\n"
            f"What's your batch year?\n"
            f"Enter the Nepali year you enrolled (e.g. *2080*)",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )

    # ── Step 2: user enters batch year ──
    elif state == "AWAITING_BATCH":
        if not text.isdigit() or int(text) not in VALID_BATCH_RANGE:
            await update.message.reply_text(
                f"Please enter a valid Nepali batch year "
                f"between {VALID_BATCH_RANGE.start} and {VALID_BATCH_RANGE.stop - 1}.\n"
                f"Example: *2080*",
                parse_mode="Markdown",
            )
            return

        batch_year = int(text)
        # Re-fetch subscriber to get the course saved in previous step
        subscriber = get_subscriber(chat_id)
        update_subscriber(chat_id, batch_year=batch_year, state="REGISTERED")

        course = COURSE_DISPLAY.get(subscriber["course"], subscriber["course"])
        await update.message.reply_text(
            f"✅ You're all set!\n\n"
            f"Course: *{course}*\n"
            f"Batch: *{batch_year} BS*\n\n"
            f"You'll now receive notices relevant to you automatically. "
            f"No need to check the website anymore!",
            parse_mode="Markdown",
        )

    # ── Already registered ──
    elif state == "REGISTERED":
        await update.message.reply_text(
            "You're already registered ✅\n\n"
            "Use /mystatus to see your details or /unsubscribe to stop notices."
        )