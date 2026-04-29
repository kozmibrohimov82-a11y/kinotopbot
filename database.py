import sqlite3
from datetime import datetime, timedelta


class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                file_id TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                username TEXT PRIMARY KEY
            )
        """)

        self.conn.commit()

    # ─── USERS ────────────────────────────────────────────
    def add_user(self, user_id: int):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,)
        )
        self.conn.commit()

    def update_last_active(self, user_id: int):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,)
        )
        self.conn.commit()

    def get_users_count(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        return cur.fetchone()[0]

    def get_active_users(self, minutes: int) -> int:
        since = (datetime.utcnow() - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
        cur = self.conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM users WHERE last_active >= ?",
            (since,)
        )
        return cur.fetchone()[0]

    def get_all_users(self) -> list[int]:
        cur = self.conn.cursor()
        cur.execute("SELECT user_id FROM users")
        return [row[0] for row in cur.fetchall()]

    # ─── MOVIES ───────────────────────────────────────────
    def add_movie(self, code: str, name: str, file_id: str) -> bool:
        try:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO movies (code, name, file_id) VALUES (?, ?, ?)",
                (code, name, file_id)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_movie(self, code: str):
        cur = self.conn.cursor()
        cur.execute("SELECT code, name, file_id FROM movies WHERE code = ?", (code,))
        return cur.fetchone()

    def get_all_movies(self) -> list:
        cur = self.conn.cursor()
        cur.execute("SELECT code, name FROM movies ORDER BY rowid DESC")
        return cur.fetchall()

    def delete_movie(self, code: str) -> bool:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM movies WHERE code = ?", (code,))
        self.conn.commit()
        return cur.rowcount > 0

    # ─── CHANNELS ─────────────────────────────────────────
    def add_channel(self, username: str) -> bool:
        try:
            cur = self.conn.cursor()
            cur.execute("INSERT INTO channels (username) VALUES (?)", (username,))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_channel(self, username: str) -> bool:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM channels WHERE username = ?", (username,))
        self.conn.commit()
        return cur.rowcount > 0

    def get_channels(self) -> list[str]:
        cur = self.conn.cursor()
        cur.execute("SELECT username FROM channels")
        return [row[0] for row in cur.fetchall()]