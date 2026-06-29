import sqlite3


class SQLiteConnection:
    _instance = None

    @classmethod
    def get_connection(cls, db_path="app.db"):
        if cls._instance is None:
            cls._instance = sqlite3.connect(db_path)
        return cls._instance
