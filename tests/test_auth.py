"""Critérios de aceite da US01 – Cadastro e login."""
import time

from app import db


def test_cadastro_valido_cria_conta_e_loga(client):
    r = client.post("/api/register", json={"name": "Ana", "email": "ana@exemplo.com", "password": "senha1234"})
    assert r.status_code == 201
    assert r.get_json()["token"]


def test_email_duplicado_retorna_erro_claro(client, auth):
    r = client.post("/api/register", json={"name": "Outra", "email": "ANA@exemplo.com", "password": "senha1234"})
    assert r.status_code == 409
    assert "já está cadastrado" in r.get_json()["erro"]


def test_senha_curta_e_rejeitada(client):
    r = client.post("/api/register", json={"name": "Ana", "email": "a@b.com", "password": "1234567"})
    assert r.status_code == 400


def test_email_invalido_e_rejeitado(client):
    r = client.post("/api/register", json={"name": "Ana", "email": "sem-arroba", "password": "senha1234"})
    assert r.status_code == 400


def test_login_com_credenciais_corretas(client, auth):
    r = client.post("/api/login", json={"email": "ana@exemplo.com", "password": "senha1234"})
    assert r.status_code == 200 and r.get_json()["token"]


def test_login_com_senha_errada(client, auth):
    r = client.post("/api/login", json={"email": "ana@exemplo.com", "password": "errada123"})
    assert r.status_code == 401


def test_bloqueio_apos_5_falhas(client, auth):
    for _ in range(5):
        client.post("/api/login", json={"email": "ana@exemplo.com", "password": "errada123"})
    r = client.post("/api/login", json={"email": "ana@exemplo.com", "password": "senha1234"})
    assert r.status_code == 423


def test_bloqueio_expira_depois_de_15_minutos(client, auth):
    for _ in range(5):
        client.post("/api/login", json={"email": "ana@exemplo.com", "password": "errada123"})
    with client.application.app_context():
        conn = db.get_db()
        conn.execute("UPDATE users SET locked_until = ?", (time.time() - 1,))
        conn.commit()
    r = client.post("/api/login", json={"email": "ana@exemplo.com", "password": "senha1234"})
    assert r.status_code == 200


def test_senha_nao_e_gravada_em_texto_puro(client, auth):
    with client.application.app_context():
        row = db.get_db().execute("SELECT password_hash FROM users").fetchone()
    assert "senha1234" not in row["password_hash"]


def test_rota_protegida_sem_token(client):
    assert client.get("/api/cart").status_code == 401
