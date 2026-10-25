"""Busca de restaurantes e visualização de cardápio (F02 e F03)."""
from flask import Blueprint, jsonify, request

from .db import get_db

bp = Blueprint("catalog", __name__, url_prefix="/api")


@bp.get("/restaurants")
def restaurants():
    q = (request.args.get("q") or "").strip()
    rows = get_db().execute(
        "SELECT id, name, category FROM restaurants WHERE name LIKE ? OR category LIKE ? ORDER BY name",
        (f"%{q}%", f"%{q}%"),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.get("/restaurants/<int:rid>/menu")
def menu(rid):
    db = get_db()
    rest = db.execute("SELECT id, name, category FROM restaurants WHERE id = ?", (rid,)).fetchone()
    if rest is None:
        return jsonify(erro="Restaurante não encontrado."), 404
    items = db.execute(
        "SELECT id, name, price_cents FROM items WHERE restaurant_id = ? ORDER BY id", (rid,)
    ).fetchall()
    return jsonify(restaurant=dict(rest), items=[dict(i) for i in items])
