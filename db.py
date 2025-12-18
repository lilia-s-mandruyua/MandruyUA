import sqlite3
from datetime import datetime

DB_NAME = "mandruy.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origin TEXT,
        destination TEXT,
        mode TEXT,
        time_min INTEGER,
        price REAL,
        transfers INTEGER,
        score REAL,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_route(origin, destination, route):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO routes (
        origin, destination, mode,
        time_min, price, transfers, score, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        origin,
        destination,
        route["mode"],
        route["time_min"],
        route["price"],
        route["transfers"],
        route.get("score"),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_saved_routes():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT origin, destination, mode, time_min, price, transfers, score, created_at
    FROM routes
    ORDER BY created_at DESC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows
