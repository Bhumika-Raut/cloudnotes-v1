import sqlite3
import os

ALLOWED_EXTENSIONS = {"txt", "md", "pdf", "png", "jpg", "jpeg", "gif"}

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    filename TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    filename VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class DBWrapper:
    def __init__(self, conn, is_postgres=False):
        self.conn = conn
        self.is_postgres = is_postgres

    def execute(self, query, params=()):
        if not self.is_postgres:
            query = query.replace("%s", "?")
            return self.conn.execute(query, params)
        else:
            query = query.replace("?", "%s")
            cur = self.conn.cursor()
            cur.execute(query, params)
            return cur

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


def is_postgres_url(db_config):
    if not db_config:
        return False
    return db_config.startswith("postgresql://") or db_config.startswith("postgres://")


def get_db_connection(db_config=None):
    if not db_config:
        db_config = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PATH") or "database/cloudnotes.db"

    if is_postgres_url(db_config):
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(db_config, row_factory=dict_row)
        return DBWrapper(conn, is_postgres=True)
    else:
        if isinstance(db_config, str) and db_config.startswith("sqlite:///"):
            db_config = db_config.replace("sqlite:///", "")
        if isinstance(db_config, str) and "/" in db_config:
            os.makedirs(os.path.dirname(os.path.abspath(db_config)), exist_ok=True)
        conn = sqlite3.connect(db_config)
        conn.row_factory = sqlite3.Row
        return DBWrapper(conn, is_postgres=False)


def init_db(db_config=None):
    if not db_config:
        db_config = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PATH") or "database/cloudnotes.db"

    if is_postgres_url(db_config):
        import psycopg

        conn = psycopg.connect(db_config)
        with conn.cursor() as cur:
            cur.execute(PG_SCHEMA)
        conn.commit()
        conn.close()
    else:
        if isinstance(db_config, str) and db_config.startswith("sqlite:///"):
            db_config = db_config.replace("sqlite:///", "")
        if isinstance(db_config, str) and "/" in db_config:
            os.makedirs(os.path.dirname(os.path.abspath(db_config)), exist_ok=True)
        conn = sqlite3.connect(db_config)
        with conn:
            conn.executescript(SQLITE_SCHEMA)
        conn.close()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

