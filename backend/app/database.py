import sqlite3
from contextlib import contextmanager
from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  call_id TEXT NOT NULL UNIQUE,
  phone TEXT,
  tier TEXT NOT NULL DEFAULT 'cold',
  budget TEXT,
  products TEXT,
  timeline TEXT,
  features TEXT,
  barrier TEXT,
  summary TEXT,
  recorded_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS callbacks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  call_id TEXT NOT NULL,
  phone TEXT,
  when_text TEXT NOT NULL,
  at TEXT NOT NULL,
  display TEXT NOT NULL,
  tier TEXT,
  note TEXT,
  booked_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS whatsapp_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  call_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  context TEXT,
  created_at TEXT NOT NULL
);
"""


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript(SCHEMA)


@contextmanager
def connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def fetch_all(sql: str, params=()):
    with connect() as connection:
        return [dict(row) for row in connection.execute(sql, params).fetchall()]


def fetch_one(sql: str, params=()):
    with connect() as connection:
        row = connection.execute(sql, params).fetchone()
        return dict(row) if row else None
