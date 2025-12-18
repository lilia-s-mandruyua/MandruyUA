import sqlite3

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
        score REAL
    )
    """)

    conn.commit()
    conn.close()

def save_routes(origin, destination, routes):
    conn = get_connection()
    cur = conn.cursor()

    for r in routes:
        cur.execute("""
        INSERT INTO routes (origin, destination, mode, time_min, price, transfers, score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            origin,
            destination,
            r["mode"],
            r["time_min"],
            r["price"],
            r["transfers"],
            r["score"]
        ))

    conn.commit()
    conn.close()
