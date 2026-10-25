"""Finalização do pedido (F05) e acompanhamento de status (F09, versão simplificada)."""
from flask import Blueprint, g, jsonify

from .auth import login_required
from .cart import cart_view
from .db import get_db

bp = Blueprint("orders", __name__, url_prefix="/api")

STATUS = ["Recebido", "Em preparo", "A caminho", "Entregue"]


def order_view(db, order):
    items = db.execute(
        "SELECT name, price_cents, qty FROM order_items WHERE order_id = ?", (order["id"],)
    ).fetchall()
    return {
        "id": order["id"],
        "status": order["status"],
        "total_cents": order["total_cents"],
        "created_at": order["created_at"],
        "items": [dict(i) for i in items],
    }


@bp.post("/orders")
@login_required
def create_order():
    db = get_db()
    cart = cart_view(db, g.user_id)
    if not cart["items"]:
        return jsonify(erro="O carrinho está vazio."), 400
    cur = db.execute(
        "INSERT INTO orders (user_id, restaurant_id, total_cents, status) VALUES (?, ?, ?, ?)",
        (g.user_id, cart["restaurant_id"], cart["total_cents"], STATUS[0]),
    )
    for it in cart["items"]:
        db.execute(
            "INSERT INTO order_items (order_id, name, price_cents, qty) VALUES (?, ?, ?, ?)",
            (cur.lastrowid, it["name"], it["price_cents"], it["qty"]),
        )
    db.execute("DELETE FROM cart_items WHERE user_id = ?", (g.user_id,))
    db.commit()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(order_view(db, order)), 201


@bp.get("/orders")
@login_required
def list_orders():
    db = get_db()
    rows = db.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (g.user_id,)).fetchall()
    return jsonify([order_view(db, r) for r in rows])


def _own_order(db, order_id):
    return db.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, g.user_id)).fetchone()


@bp.get("/orders/<int:order_id>")
@login_required
def get_order(order_id):
    db = get_db()
    order = _own_order(db, order_id)
    if order is None:
        return jsonify(erro="Pedido não encontrado."), 404
    return jsonify(order_view(db, order))


@bp.post("/orders/<int:order_id>/advance")
@login_required
def advance(order_id):
    """Simula o restaurante/entregador avançando o status (até existir o painel F07)."""
    db = get_db()
    order = _own_order(db, order_id)
    if order is None:
        return jsonify(erro="Pedido não encontrado."), 404
    idx = STATUS.index(order["status"])
    if idx == len(STATUS) - 1:
        return jsonify(erro="O pedido já foi entregue."), 409
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (STATUS[idx + 1], order_id))
    db.commit()
    return jsonify(order_view(db, _own_order(db, order_id)))
