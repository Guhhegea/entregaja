"""US02 – Carrinho de compras (F04). O carrinho fica salvo no banco."""
from flask import Blueprint, g, jsonify, request

from .auth import login_required
from .db import get_db

bp = Blueprint("cart", __name__, url_prefix="/api")


def cart_view(db, user_id):
    rows = db.execute(
        """SELECT i.id AS item_id, i.name, i.price_cents, i.restaurant_id, c.qty
           FROM cart_items c JOIN items i ON i.id = c.item_id
           WHERE c.user_id = ? ORDER BY i.id""",
        (user_id,),
    ).fetchall()
    items = [dict(r) for r in rows]
    total = sum(r["price_cents"] * r["qty"] for r in items)
    return {"restaurant_id": items[0]["restaurant_id"] if items else None, "items": items, "total_cents": total}


@bp.get("/cart")
@login_required
def get_cart():
    return jsonify(cart_view(get_db(), g.user_id))


@bp.post("/cart/items")
@login_required
def add_item():
    data = request.get_json(silent=True) or {}
    qty = data.get("qty", 1)
    if not isinstance(qty, int) or qty < 1:
        return jsonify(erro="Quantidade mínima: 1."), 400
    db = get_db()
    item = db.execute("SELECT id, restaurant_id FROM items WHERE id = ?", (data.get("item_id"),)).fetchone()
    if item is None:
        return jsonify(erro="Item não encontrado."), 404
    current = cart_view(db, g.user_id)["restaurant_id"]
    if current is not None and current != item["restaurant_id"]:
        if not data.get("replace"):
            return jsonify(erro="O carrinho tem itens de outro restaurante.", codigo="outro_restaurante"), 409
        db.execute("DELETE FROM cart_items WHERE user_id = ?", (g.user_id,))
    db.execute(
        """INSERT INTO cart_items (user_id, item_id, qty) VALUES (?, ?, ?)
           ON CONFLICT(user_id, item_id) DO UPDATE SET qty = qty + excluded.qty""",
        (g.user_id, item["id"], qty),
    )
    db.commit()
    return jsonify(cart_view(db, g.user_id)), 201


@bp.patch("/cart/items/<int:item_id>")
@login_required
def update_item(item_id):
    qty = (request.get_json(silent=True) or {}).get("qty")
    if not isinstance(qty, int):
        return jsonify(erro="Informe a quantidade."), 400
    db = get_db()
    if qty < 1:
        db.execute("DELETE FROM cart_items WHERE user_id = ? AND item_id = ?", (g.user_id, item_id))
    else:
        db.execute("UPDATE cart_items SET qty = ? WHERE user_id = ? AND item_id = ?", (qty, g.user_id, item_id))
    db.commit()
    return jsonify(cart_view(db, g.user_id))


@bp.delete("/cart/items/<int:item_id>")
@login_required
def remove_item(item_id):
    db = get_db()
    db.execute("DELETE FROM cart_items WHERE user_id = ? AND item_id = ?", (g.user_id, item_id))
    db.commit()
    return jsonify(cart_view(db, g.user_id))
