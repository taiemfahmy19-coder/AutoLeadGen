"""AutoLeadGen v2 - Database Connection Management with WAL Mode and Thread Safety."""
import sqlite3
import os
import threading
from contextlib import contextmanager
from config.settings import DB_PATH
from utils.logger import error

_local = threading.local()
_lock = threading.Lock()


def get_raw_connection(db_path=DB_PATH) -> sqlite3.Connection:
    """
    Create a hardened SQLite connection with WAL mode and foreign keys enabled.
    """
    db_dir = os.path.dirname(os.path.abspath(db_path))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(
        db_path,
        check_same_thread=False,
        timeout=15.0  # Wait up to 15s if locked
    )
    # Configure hardened SQLite pragmas
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 15000;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


class DatabaseManager:
    """Singleton/thread-safe manager for SQLite connections."""
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._conn = get_raw_connection(self.db_path)
        self._lock = threading.Lock()

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    @contextmanager
    def transaction(self):
        """Thread-safe transactional context manager with automatic commit/rollback."""
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception as e:
                self._conn.rollback()
                error(f"Database transaction rollback due to: {e}")
                raise

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass
