"""
SQLite database layer for the Finance Data Tracker.
Handles schema creation, persistence, and all query operations.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = "finance_tracker.db"


@contextmanager
def _connect(db_path: str = DB_PATH):
    """
    Context manager that opens a database connection with Row factory enabled,
    commits on clean exit, and rolls back on any exception.

    Args:
        db_path: Path to the SQLite database file.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str = DB_PATH) -> None:
    """
    Create the database schema if it does not already exist.

    Tables created:
        - stocks: one row per tracked company (ticker is the primary key).
        - price_history: daily OHLCV rows; (ticker, date) is unique.

    Args:
        db_path: Path to the SQLite database file.
    """
    with _connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                ticker       TEXT PRIMARY KEY,
                name         TEXT NOT NULL,
                sector       TEXT DEFAULT 'Unknown',
                industry     TEXT DEFAULT 'Unknown',
                added_on     TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker  TEXT    NOT NULL,
                date    TEXT    NOT NULL,
                open    REAL,
                high    REAL,
                low     REAL,
                close   REAL,
                volume  INTEGER,
                UNIQUE(ticker, date),
                FOREIGN KEY (ticker) REFERENCES stocks(ticker)
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_ph_ticker ON price_history(ticker)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_ph_date   ON price_history(date)"
        )


def save_stock(
    ticker: str,
    name: str,
    sector: str = "Unknown",
    industry: str = "Unknown",
    db_path: str = DB_PATH,
) -> None:
    """
    Insert a new stock or update its metadata if the ticker already exists.

    Args:
        ticker: Stock ticker symbol (stored in upper-case).
        name: Company name.
        sector: Industry sector (e.g. "Technology").
        industry: Specific industry (e.g. "Consumer Electronics").
        db_path: Path to the database file.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO stocks (ticker, name, sector, industry, added_on, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET
                name         = excluded.name,
                sector       = excluded.sector,
                industry     = excluded.industry,
                last_updated = excluded.last_updated
            """,
            (ticker.upper(), name, sector, industry, now, now),
        )


def stock_exists(ticker: str, db_path: str = DB_PATH) -> bool:
    """
    Return True if the ticker is already saved in the stocks table.

    Args:
        ticker: Stock ticker symbol.
        db_path: Path to the database file.
    """
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM stocks WHERE ticker = ?", (ticker.upper(),)
        ).fetchone()
        return row is not None


def get_all_stocks(db_path: str = DB_PATH) -> List[sqlite3.Row]:
    """
    Retrieve every stock saved in the database, ordered alphabetically by ticker.

    Args:
        db_path: Path to the database file.

    Returns:
        List of Row objects with columns: ticker, name, sector, industry,
        added_on, last_updated.
    """
    with _connect(db_path) as conn:
        return conn.execute("SELECT * FROM stocks ORDER BY ticker").fetchall()


def get_stock_info(ticker: str, db_path: str = DB_PATH) -> Optional[sqlite3.Row]:
    """
    Retrieve a single stock's metadata row.

    Args:
        ticker: Stock ticker symbol.
        db_path: Path to the database file.

    Returns:
        Row with stock metadata or None if the ticker is not in the database.
    """
    with _connect(db_path) as conn:
        return conn.execute(
            "SELECT * FROM stocks WHERE ticker = ?", (ticker.upper(),)
        ).fetchone()


def save_price_history(
    ticker: str, records: List[Dict[str, Any]], db_path: str = DB_PATH
) -> int:
    """
    Bulk-insert daily OHLCV records for a stock, silently skipping duplicates.

    Args:
        ticker: Stock ticker symbol.
        records: List of dicts with keys: date, open, high, low, close, volume.
        db_path: Path to the database file.

    Returns:
        Number of rows actually inserted (0 if all were duplicates).
    """
    if not records:
        return 0

    rows = [
        (ticker.upper(), r["date"], r["open"], r["high"], r["low"], r["close"], r["volume"])
        for r in records
    ]
    with _connect(db_path) as conn:
        cur = conn.cursor()
        cur.executemany(
            """
            INSERT OR IGNORE INTO price_history
                (ticker, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        return cur.rowcount


def get_price_history(
    ticker: str, days: int = 30, db_path: str = DB_PATH
) -> List[sqlite3.Row]:
    """
    Retrieve the most recent price history rows for a stock, oldest-first.

    Args:
        ticker: Stock ticker symbol.
        days: Maximum number of trading days to return.
        db_path: Path to the database file.

    Returns:
        List of Row objects with columns: date, open, high, low, close, volume.
    """
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT date, open, high, low, close, volume
            FROM price_history
            WHERE ticker = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (ticker.upper(), days),
        ).fetchall()
    return list(reversed(rows))


def get_latest_price(ticker: str, db_path: str = DB_PATH) -> Optional[sqlite3.Row]:
    """
    Return the single most-recent price record for a stock.

    Args:
        ticker: Stock ticker symbol.
        db_path: Path to the database file.

    Returns:
        Row with columns date/open/high/low/close/volume, or None if no data.
    """
    with _connect(db_path) as conn:
        return conn.execute(
            """
            SELECT date, open, high, low, close, volume
            FROM price_history
            WHERE ticker = ?
            ORDER BY date DESC
            LIMIT 1
            """,
            (ticker.upper(),),
        ).fetchone()
