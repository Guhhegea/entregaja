"""Acesso ao banco SQLite, criação do esquema e dados iniciais."""
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS tokens (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
    name TEXT NOT NULL,
    price_cents INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS cart_items (
    user_id INTEGER NOT NULL REFERENCES users(id),
    item_id INTEGER NOT NULL REFERENCES items(id),
    qty INTEGER NOT NULL,
    PRIMARY KEY (user_id, item_id)
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
    total_cents INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS order_items (
    order_id INTEGER NOT NULL REFERENCES orders(id),
    name TEXT NOT NULL,
    price_cents INTEGER NOT NULL,
    qty INTEGER NOT NULL
);
"""

SEED = {
    "Pizzaria Bella Massa": ("Pizza", [("Pizza Margherita", 4290), ("Pizza Calabresa", 4590), ("Refrigerante 2L", 1200)]),
    "Sushi Sakura": ("Japonesa", [("Combo 20 peças", 6490), ("Temaki salmão", 2290), ("Chá gelado", 900)]),
    "Hamburgueria do Zé": ("Lanches", [("X-Burger", 2590), ("X-Bacon", 3190), ("Batata frita", 1490)]),
}


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    if conn.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0] == 0:
        for name, (category, items) in SEED.items():
            cur = conn.execute("INSERT INTO restaurants (name, category) VALUES (?, ?)", (name, category))
            for item_name, price in items:
                conn.execute(
                    "INSERT INTO items (restaurant_id, name, price_cents) VALUES (?, ?, ?)",
                    (cur.lastrowid, item_name, price),
                )
    conn.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
