import sqlite3

class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        with self.connection:
            # 🎬 Movies
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    code TEXT PRIMARY KEY,
                    name TEXT,
                    file_id TEXT
                )
            """)

            # 👥 Users
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER UNIQUE,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    # =======================
    # 🎬 MOVIES
    # =======================
    def add_movie(self, code, name, file_id):
        try:
            with self.connection:
                self.cursor.execute(
                    "INSERT INTO movies VALUES (?, ?, ?)",
                    (code, name, file_id)
                )
                return True
        except sqlite3.IntegrityError:
            return False

    def get_movie(self, code):
        self.cursor.execute("SELECT * FROM movies WHERE code = ?", (code,))
        return self.cursor.fetchone()

    def get_all_movies(self):
        self.cursor.execute("SELECT code, name FROM movies")
        return self.cursor.fetchall()

    def delete_movie(self, code):
        with self.connection:
            self.cursor.execute("DELETE FROM movies WHERE code = ?", (code,))
            return self.cursor.rowcount > 0

    # =======================
    # 👥 USERS
    # =======================
    def add_user(self, user_id):
        try:
            with self.connection:
                self.cursor.execute(
                    "INSERT INTO users (user_id) VALUES (?)",
                    (user_id,)
                )
        except:
            pass  # mavjud bo‘lsa skip

    def update_last_active(self, user_id):
        with self.connection:
            self.cursor.execute("""
                UPDATE users 
                SET last_active = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            """, (user_id,))

    def get_users_count(self):
        self.cursor.execute("SELECT COUNT(*) FROM users")
        return self.cursor.fetchone()[0]

    def get_all_users(self):
        self.cursor.execute("SELECT user_id FROM users")
        return [row[0] for row in self.cursor.fetchall()]

    def get_active_users(self, minutes=1440):
        self.cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE last_active >= datetime('now', ?)
        """, (f"-{minutes} minutes",))
        return self.cursor.fetchone()[0]