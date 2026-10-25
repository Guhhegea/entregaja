"""Pedido (F05), acompanhamento (US03 simplificada) e infraestrutura de monitoramento."""


def _pedido(client, auth):
    item = client.get("/api/restaurants/1/menu").get_json()["items"][0]["id"]
    client.post("/api/cart/items", json={"item_id": item, "qty": 2}, headers=auth)
    return client.post("/api/orders", headers=auth).get_json()


def test_finalizar_pedido_cria_pedido_e_esvazia_carrinho(client, auth):
    pedido = _pedido(client, auth)
    assert pedido["status"] == "Recebido"
    assert client.get("/api/cart", headers=auth).get_json()["items"] == []


def test_pedido_com_carrinho_vazio_e_rejeitado(client, auth):
    assert client.post("/api/orders", headers=auth).status_code == 400


def test_status_segue_a_ordem_e_nao_retrocede(client, auth):
    pedido = _pedido(client, auth)
    vistos = [pedido["status"]]
    for _ in range(3):
        vistos.append(client.post(f"/api/orders/{pedido['id']}/advance", headers=auth).get_json()["status"])
    assert vistos == ["Recebido", "Em preparo", "A caminho", "Entregue"]
    assert client.post(f"/api/orders/{pedido['id']}/advance", headers=auth).status_code == 409


def test_cliente_nao_ve_pedido_de_outro(client, auth):
    pedido = _pedido(client, auth)
    r = client.post("/api/register", json={"name": "Bia", "email": "bia@exemplo.com", "password": "senha1234"})
    outro = {"Authorization": f"Bearer {r.get_json()['token']}"}
    assert client.get(f"/api/orders/{pedido['id']}", headers=outro).status_code == 404


def test_historico_lista_pedidos_do_cliente(client, auth):
    _pedido(client, auth)
    assert len(client.get("/api/orders", headers=auth).get_json()) == 1


def test_busca_de_restaurantes_filtra_por_nome_ou_categoria(client):
    assert [r["name"] for r in client.get("/api/restaurants?q=sushi").get_json()] == ["Sushi Sakura"]
    assert len(client.get("/api/restaurants").get_json()) == 3


def test_cardapio_de_restaurante_inexistente(client):
    assert client.get("/api/restaurants/999/menu").status_code == 404


def test_health_check(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_metricas_contam_requisicoes(client):
    client.get("/health")
    corpo = client.get("/metrics").get_data(as_text=True)
    assert 'http_requests_total{method="GET",route="/health",status="200"} 1' in corpo


def test_erro_inesperado_retorna_500_json(client):
    app = client.application
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.get("/boom")
    def boom():
        raise RuntimeError("falha de teste")

    r = client.get("/boom")
    assert r.status_code == 500 and r.get_json()["erro"] == "Erro interno do servidor."
