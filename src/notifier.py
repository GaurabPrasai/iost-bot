from db import (
    get_all_registered,
    get_subscribers_by_course,
    is_notice_sent,
    mark_notice_sent,
)

COURSE_DISPLAY = {
    "CSIT":  "B.Sc.CSIT",
    "BIT":   "BIT",
    "BTECH": "B.Tech (Food Technology)",
    "MSC":   "M.Sc.",
    "BSC":   "B.Sc.",
    "ALL":   "General",
}


def format_message(notice):
    courses_label = ", ".join(
        COURSE_DISPLAY.get(c, c) for c in notice["courses"]
    )
    return (
        f"📢 *New Notice — {courses_label}*\n\n"
        f"{notice['title']}\n\n"
        f"🔗 {notice['url']}\n"
        f"📅 {notice['date']}"
    )


async def send_notice_to_subscribers(bot, notice):
    courses      = notice["courses"]
    target_batch = notice["target_batch"]

    # Collect relevant subscribers
    if "ALL" in courses:
        subscribers = get_all_registered()
    else:
        seen     = set()
        subscribers = []
        for course in courses:
            for s in get_subscribers_by_course(course):
                if s["chat_id"] not in seen:
                    seen.add(s["chat_id"])
                    subscribers.append(s)

    message = format_message(notice)

    for sub in subscribers:
        chat_id    = sub["chat_id"]
        batch_year = sub.get("batch_year")

        # Filter by batch if the notice specifies one
        if target_batch and batch_year and batch_year != target_batch:
            continue

        # Skip if already sent to this user
        if is_notice_sent(notice["id"], chat_id):
            continue

        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown"
            )
            mark_notice_sent(notice["id"], chat_id)
            print(f"[Notifier] Sent notice {notice['id']} → {chat_id}")
        except Exception as e:
            print(f"[Notifier] Failed to send to {chat_id}: {e}")