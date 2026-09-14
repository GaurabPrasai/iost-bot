import sqlite3

DB_PATH = "iost_bot.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets you access columns by name
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id     INTEGER PRIMARY KEY,
            username    TEXT,
            course      TEXT,
            batch_year  INTEGER,
            state       TEXT DEFAULT 'NEW',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seen_notices (
            notice_id    INTEGER PRIMARY KEY,
            title        TEXT,
            url          TEXT,
            courses      TEXT,
            notice_date  TEXT,
            detected_at  TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_notices (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            notice_id   INTEGER,
            chat_id     INTEGER,
            sent_at     TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(notice_id, chat_id)
        )
    """)

    conn.commit()
    conn.close()


# ── Subscriber functions ───────────────────────────────────────────────────────

def add_subscriber(chat_id, username=None):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO subscribers (chat_id, username, state) VALUES (?, ?, 'NEW')",
        (chat_id, username)
    )
    conn.commit()
    conn.close()


def get_subscriber(chat_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM subscribers WHERE chat_id = ?", (chat_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_subscriber(chat_id, **kwargs):
    conn = get_connection()
    for key, value in kwargs.items():
        conn.execute(
            f"UPDATE subscribers SET {key} = ? WHERE chat_id = ?",
            (value, chat_id)
        )
    conn.commit()
    conn.close()


def delete_subscriber(chat_id):
    conn = get_connection()
    conn.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()


def get_all_registered():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM subscribers WHERE state = 'REGISTERED'"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_subscribers_by_course(course):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM subscribers WHERE course = ? AND state = 'REGISTERED'",
        (course,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Notice functions ───────────────────────────────────────────────────────────

def is_notice_seen(notice_id):
    conn = get_connection()
    result = conn.execute(
        "SELECT 1 FROM seen_notices WHERE notice_id = ?", (notice_id,)
    ).fetchone()
    conn.close()
    return result is not None


def mark_notice_seen(notice_id, title, url, courses, notice_date):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO seen_notices (notice_id, title, url, courses, notice_date) VALUES (?, ?, ?, ?, ?)",
        (notice_id, title, url, ",".join(courses), notice_date)
    )
    conn.commit()
    conn.close()


def is_notice_sent(notice_id, chat_id):
    conn = get_connection()
    result = conn.execute(
        "SELECT 1 FROM sent_notices WHERE notice_id = ? AND chat_id = ?",
        (notice_id, chat_id)
    ).fetchone()
    conn.close()
    return result is not None


def mark_notice_sent(notice_id, chat_id):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO sent_notices (notice_id, chat_id) VALUES (?, ?)",
        (notice_id, chat_id)
    )
    conn.commit()
    conn.close()

def get_recent_notices(course, weeks=1):
    from datetime import datetime, timedelta
    cutoff = (datetime.now() - timedelta(weeks=weeks)).strftime("%Y-%m-%d")
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM seen_notices
        WHERE courses LIKE ?
        AND notice_date >= ?
        ORDER BY notice_date DESC
    """, (f"%{course}%", cutoff)).fetchall()
    conn.close()
    return [dict(r) for r in rows]