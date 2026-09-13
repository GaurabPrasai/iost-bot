import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, TypeHandler, filters

from bot import start, help_command, mystatus, unsubscribe, handle_message, latest
from db import init_db, is_notice_seen, mark_notice_seen
from notifier import send_notice_to_subscribers
from scraper import scrape_notices

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),
    ],
)


async def scrape_and_notify(bot):
    print("[Scheduler] Scraping notices...")
    notices = scrape_notices()
    new_count = 0
    for notice in notices:
        if is_notice_seen(notice["id"]):
            continue
        mark_notice_seen(notice["id"], notice["title"], notice["url"], notice["courses"])
        await send_notice_to_subscribers(bot, notice)
        new_count += 1
    print(f"[Scheduler] Done — {new_count} new notice(s) found.")


async def error_handler(update, context):
    print(f"[Error] {context.error}")


async def post_init(app):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scrape_and_notify,
        trigger="interval",
        minutes=5,
        args=[app.bot],
        id="scraper_job",
    )
    scheduler.start()

    # Run once immediately on startup
    await scrape_and_notify(app.bot)
    print("[Main] Scheduler started.")


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set in .env file")

    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start",       start))
    app.add_handler(CommandHandler("help",        help_command))
    app.add_handler(CommandHandler("mystatus",    mystatus))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("latest", latest))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    print("[Main] Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()