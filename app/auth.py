"""US01 – Cadastro e login de cliente."""
import re
import secrets
import time
from functools import wraps

from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/api")

MAX_ATTEMPTS = 5
LOCK_SECONDS = 15 * 60
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _new_token(db, user_id):
    token = secrets.token_hex(24)
    db.execute("INSERT INTO tokens (token, user_id) VALUES (?, ?)", (token, user_id))
    db.commit()
    return token


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        token = header[7:] if header.startswith("Bearer ") else ""
        row = get_db().execute("SELECT user_id FROM tokens WHERE token = ?", (token,)).fetchone()
        if row is None:
            return jsonify(erro="Não autenticado."), 401
        g.user_id = row["user_id"]
        return view(*args, **kwargs)

    return wrapper


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not name or not EMAIL_RE.match(email):
        return jsonify(erro="Informe nome e e-mail válidos."), 400
    if len(password) < 8:
        return jsonify(erro="A senha deve ter pelo menos 8 caracteres."), 400
    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
        return jsonify(erro="Este e-mail já está cadastrado."), 409
    cur = db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, generate_password_hash(password)),
    )
    db.commit()
    return jsonify(token=_new_token(db, cur.lastrowid), name=name), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user is None:
        return jsonify(erro="E-mail ou senha incorretos."), 401
    if user["locked_until"] > time.time():
        return jsonify(erro="Conta bloqueada temporariamente. Tente novamente em 15 minutos."), 423
    if not check_password_hash(user["password_hash"], password):
        attempts = user["failed_attempts"] + 1
        locked = time.time() + LOCK_SECONDS if attempts >= MAX_ATTEMPTS else 0
        db.execute(
            "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
            (0 if locked else attempts, locked, user["id"]),
        )
        db.commit()
        return jsonify(erro="E-mail ou senha incorretos."), 401
    db.execute("UPDATE users SET failed_attempts = 0, locked_until = 0 WHERE id = ?", (user["id"],))
    db.commit()
    return jsonify(token=_new_token(db, user["id"]), name=user["name"])
