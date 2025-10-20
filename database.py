import sqlite3
from datetime import timedelta, datetime

def init_db():
    with sqlite3.connect('reminders.db') as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT,
                date DATE,
                time TIME
            )
            ''')
        conn.commit()

def init_focus():
    with sqlite3.connect('time.db') as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS focus (
                number_of_sessions INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                over_time TIMESTAMP,
                duration INTEGER
            )
            ''')
        conn.commit()

def reminder(user_id: int, text: str, date: str, time: str):
    with sqlite3.connect('reminders.db') as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO reminders (user_id, text, date, time)
            VALUES (?, ?, ?, ?)
            ''', (user_id, text, date, time,))
        conn.commit()


def focus(user_id: int, start_time: str, end_time: str, over_time: str):
    with sqlite3.connect('time.db') as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO focus (user_id, start_time, end_time, over_time)
            VALUES (?, ?, ?, ?)
            ''', (user_id, start_time, end_time, over_time,))
        conn.commit()

def save_focus_session(user_id: int, start_time: datetime, end_time: datetime):
    duration = int((end_time - start_time).total_seconds())
    with sqlite3.connect("reminders.db") as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO focus_sessions (user_id, start_time, end_time, duration)
            VALUES (?, ?, ?, ?)
        """, (user_id, start_time, end_time, duration))
        conn.commit()

def get_focus_stats(user_id: int):
    with sqlite3.connect('time.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT duration FROM focus WHERE user_id = ?", (user_id,))
        durations = [row[0] for row in cur.fetchall()]

    if not durations:
        return 0, timedelta(0), timedelta(0)

    total_sessions = len(durations)
    total_time = timedelta(seconds=sum(durations))
    avg_duration = total_time / total_sessions

    return total_sessions, total_time, avg_duration




def get_stats(user_id: int):
    with sqlite3.connect('reminders.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM reminders")
        count = cur.fetchone()[0]
    return count




