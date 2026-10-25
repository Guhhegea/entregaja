import pytest

from app import create_app, metrics


@pytest.fixture()
def client(tmp_path):
    metrics.reset()
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    return app.test_client()


@pytest.fixture()
def auth(client):
    """Cadastra um cliente e devolve o cabeçalho de autenticação."""
    r = client.post("/api/register", json={"name": "Ana", "email": "ana@exemplo.com", "password": "senha1234"})
    return {"Authorization": f"Bearer {r.get_json()['token']}"}
