from app.models.rota import Rota


def test_rota_e_criada_com_data_padrao(db_session):
    rota = Rota(nome="Manaus - Tefe")
    db_session.add(rota)
    db_session.commit()
    db_session.refresh(rota)

    assert rota.id is not None
    assert rota.criado_em is not None


from app.models.parada import Parada


def _criar_rota(client, headers, nome="Manaus - Tefe"):
    resposta = client.post("/rotas", json={"nome": nome}, headers=headers)
    assert resposta.status_code == 201
    return resposta.json()["id"]


def _criar_parada(client, headers, rota_id, nome, ordem):
    return client.post(
        f"/rotas/{rota_id}/paradas", json={"nome": nome, "ordem": ordem}, headers=headers
    )


def test_crud_de_rota(client, headers_empresa):
    rota_id = _criar_rota(client, headers_empresa)

    lista = client.get("/rotas", headers=headers_empresa)
    assert [r["id"] for r in lista.json()] == [rota_id]

    editada = client.patch(f"/rotas/{rota_id}", json={"nome": "Manaus - Coari"}, headers=headers_empresa)
    assert editada.status_code == 200
    assert editada.json()["nome"] == "Manaus - Coari"

    assert client.delete(f"/rotas/{rota_id}", headers=headers_empresa).status_code == 204
    assert client.get(f"/rotas/{rota_id}", headers=headers_empresa).status_code == 404


def test_detalhe_da_rota_lista_paradas_ordenadas(client, headers_empresa):
    rota_id = _criar_rota(client, headers_empresa)
    for nome, ordem in [("Tefe", 3), ("Manaus", 1), ("Coari", 2)]:
        assert _criar_parada(client, headers_empresa, rota_id, nome, ordem).status_code == 201

    detalhe = client.get(f"/rotas/{rota_id}", headers=headers_empresa).json()
    assert [p["nome"] for p in detalhe["paradas"]] == ["Manaus", "Coari", "Tefe"]

    paradas = client.get(f"/rotas/{rota_id}/paradas", headers=headers_empresa).json()
    assert [p["ordem"] for p in paradas] == [1, 2, 3]


def test_ordem_repetida_na_rota_retorna_409(client, headers_empresa):
    rota_id = _criar_rota(client, headers_empresa)
    _criar_parada(client, headers_empresa, rota_id, "Manaus", 1)

    assert _criar_parada(client, headers_empresa, rota_id, "Coari", 1).status_code == 409

    parada_id = _criar_parada(client, headers_empresa, rota_id, "Coari", 2).json()["id"]
    conflito = client.patch(f"/rotas/{rota_id}/paradas/{parada_id}", json={"ordem": 1}, headers=headers_empresa)
    assert conflito.status_code == 409


def test_editar_e_excluir_parada(client, headers_empresa):
    rota_id = _criar_rota(client, headers_empresa)
    parada_id = _criar_parada(client, headers_empresa, rota_id, "Manaus", 1).json()["id"]

    editada = client.patch(f"/rotas/{rota_id}/paradas/{parada_id}", json={"nome": "Porto de Manaus"}, headers=headers_empresa)
    assert editada.status_code == 200
    assert editada.json()["nome"] == "Porto de Manaus"

    assert client.delete(f"/rotas/{rota_id}/paradas/{parada_id}", headers=headers_empresa).status_code == 204
    assert client.get(f"/rotas/{rota_id}/paradas", headers=headers_empresa).json() == []


def test_parada_de_outra_rota_retorna_404(client, headers_empresa):
    rota_a = _criar_rota(client, headers_empresa, "A")
    rota_b = _criar_rota(client, headers_empresa, "B")
    parada_id = _criar_parada(client, headers_empresa, rota_a, "Manaus", 1).json()["id"]

    assert client.patch(f"/rotas/{rota_b}/paradas/{parada_id}", json={"nome": "X"}, headers=headers_empresa).status_code == 404
    assert client.delete(f"/rotas/{rota_b}/paradas/{parada_id}", headers=headers_empresa).status_code == 404


def test_excluir_rota_remove_suas_paradas(client, db_session, headers_empresa):
    rota_id = _criar_rota(client, headers_empresa)
    _criar_parada(client, headers_empresa, rota_id, "Manaus", 1)

    client.delete(f"/rotas/{rota_id}", headers=headers_empresa)

    assert db_session.query(Parada).count() == 0


def test_rota_inexistente_retorna_404(client, headers_empresa):
    assert client.get("/rotas/999", headers=headers_empresa).status_code == 404
    assert _criar_parada(client, headers_empresa, 999, "X", 1).status_code == 404
    assert client.get("/rotas/999/paradas", headers=headers_empresa).status_code == 404


def test_ordem_invalida_retorna_422(client, headers_empresa):
    rota_id = _criar_rota(client, headers_empresa)
    assert _criar_parada(client, headers_empresa, rota_id, "X", 0).status_code == 422


def test_sem_login_retorna_401_em_rotas_e_paradas(client):
    assert client.post("/rotas", json={"nome": "X"}).status_code == 401
    assert client.get("/rotas").status_code == 401
    assert client.get("/rotas/1").status_code == 401
    assert client.patch("/rotas/1", json={"nome": "X"}).status_code == 401
    assert client.delete("/rotas/1").status_code == 401
    assert client.post("/rotas/1/paradas", json={"nome": "X", "ordem": 1}).status_code == 401
    assert client.get("/rotas/1/paradas").status_code == 401
    assert client.patch("/rotas/1/paradas/1", json={"nome": "X"}).status_code == 401
    assert client.delete("/rotas/1/paradas/1").status_code == 401


def test_cliente_nao_acessa_rotas_e_paradas(client, headers_cliente):
    h = headers_cliente
    assert client.post("/rotas", json={"nome": "X"}, headers=h).status_code == 403
    assert client.get("/rotas", headers=h).status_code == 403
    assert client.get("/rotas/1", headers=h).status_code == 403
    assert client.patch("/rotas/1", json={"nome": "X"}, headers=h).status_code == 403
    assert client.delete("/rotas/1", headers=h).status_code == 403
    assert client.post("/rotas/1/paradas", json={"nome": "X", "ordem": 1}, headers=h).status_code == 403
    assert client.get("/rotas/1/paradas", headers=h).status_code == 403
    assert client.patch("/rotas/1/paradas/1", json={"nome": "X"}, headers=h).status_code == 403
    assert client.delete("/rotas/1/paradas/1", headers=h).status_code == 403
