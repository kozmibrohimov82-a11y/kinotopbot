import sqlite3

class Database:
    def __init__(self, db_file):
        # check_same_thread=False xatolikni oldini oladi
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        with self.connection:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    code TEXT PRIMARY KEY,
                    name TEXT,
                    file_id TEXT
                )
            """)

    def add_movie(self, code, name, file_id):
        try:
            with self.connection:
                self.cursor.execute("INSERT INTO movies VALUES (?, ?, ?)", (code, name, file_id))
                return True
        except sqlite3.IntegrityError:
            return False

    # MANA SHU FUNKSIYA NOMI main.py DAGI BILAN BIR XIL BO'LISHI KERAK
    def get_movie(self, code):
        self.cursor.execute("SELECT * FROM movies WHERE code = ?", (code,))
        return self.cursor.fetchone()

    def get_all_movies(self):
        # Barcha kinolarni ro'yxat ko'rinishida qaytaradi
        self.cursor.execute("SELECT code, name FROM movies")
        return self.cursor.fetchall()
