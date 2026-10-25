"""Critérios de aceite da US02 – Carrinho de compras."""


def _item(client, restaurant_id, index=0):
    return client.get(f"/api/restaurants/{restaurant_id}/menu").get_json()["items"][index]["id"]


def test_adicionar_item_entra_com_quantidade_1(client, auth):
    r = client.post("/api/cart/items", json={"item_id": _item(client, 1)}, headers=auth)
    assert r.status_code == 201
    assert r.get_json()["items"][0]["qty"] == 1


def test_alterar_quantidade_recalcula_total(client, auth):
    item = _item(client, 1)
    cart = client.post("/api/cart/items", json={"item_id": item}, headers=auth).get_json()
    price = cart["items"][0]["price_cents"]
    cart = client.patch(f"/api/cart/items/{item}", json={"qty": 3}, headers=auth).get_json()
    assert cart["total_cents"] == price * 3


def test_remover_item_zera_o_carrinho(client, auth):
    item = _item(client, 1)
    client.post("/api/cart/items", json={"item_id": item}, headers=auth)
    cart = client.delete(f"/api/cart/items/{item}", headers=auth).get_json()
    assert cart["items"] == [] and cart["total_cents"] == 0


def test_quantidade_zero_remove_o_item(client, auth):
    item = _item(client, 1)
    client.post("/api/cart/items", json={"item_id": item}, headers=auth)
    cart = client.patch(f"/api/cart/items/{item}", json={"qty": 0}, headers=auth).get_json()
    assert cart["items"] == []


def test_somente_um_restaurante_por_vez(client, auth):
    client.post("/api/cart/items", json={"item_id": _item(client, 1)}, headers=auth)
    r = client.post("/api/cart/items", json={"item_id": _item(client, 2)}, headers=auth)
    assert r.status_code == 409
    assert r.get_json()["codigo"] == "outro_restaurante"


def test_confirmar_troca_de_restaurante_esvazia_o_carrinho(client, auth):
    client.post("/api/cart/items", json={"item_id": _item(client, 1)}, headers=auth)
    r = client.post("/api/cart/items", json={"item_id": _item(client, 2), "replace": True}, headers=auth)
    assert r.status_code == 201
    assert len(r.get_json()["items"]) == 1


def test_carrinho_persiste_entre_requisicoes(client, auth):
    client.post("/api/cart/items", json={"item_id": _item(client, 1)}, headers=auth)
    assert len(client.get("/api/cart", headers=auth).get_json()["items"]) == 1


def test_quantidade_minima_1(client, auth):
    r = client.post("/api/cart/items", json={"item_id": _item(client, 1), "qty": 0}, headers=auth)
    assert r.status_code == 400
