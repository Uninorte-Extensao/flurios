"""GET /rotas/destinos: paradas que o cliente pode escolher como destino (exceto a origem)."""


def _criar_rota(client, headers_administrador, nome, paradas):
    rota = client.post("/rotas", json={"nome": nome}, headers=headers_administrador).json()
    for ordem, nome_parada in enumerate(paradas, start=1):
        resposta = client.post(
            f"/rotas/{rota['id']}/paradas",
            json={"nome": nome_parada, "ordem": ordem},
            headers=headers_administrador,
        )
        assert resposta.status_code == 201
    return rota


def test_destinos_exige_login(client):
    assert client.get("/rotas/destinos").status_code == 401


def test_cliente_logado_lista_destinos(client, headers_cliente, rota_com_paradas):
    resposta = client.get("/rotas/destinos", headers=headers_cliente)

    assert resposta.status_code == 200
    assert resposta.json() == [
        {"id": rota_com_paradas.destino.id, "nome": "Tefe", "rota_nome": "Manaus - Coari"},
        {"id": rota_com_paradas.final.id, "nome": "Coari", "rota_nome": "Manaus - Coari"},
    ]


def test_empresa_tambem_lista_destinos(client, headers_administrador, rota_com_paradas):
    assert client.get("/rotas/destinos", headers=headers_administrador).status_code == 200


def test_destinos_nunca_inclui_a_parada_de_ordem_1(client, headers_cliente, rota_com_paradas):
    ids = [d["id"] for d in client.get("/rotas/destinos", headers=headers_cliente).json()]

    assert rota_com_paradas.origem.id not in ids


def test_destinos_reune_paradas_de_todas_as_rotas(client, headers_cliente, headers_administrador):
    _criar_rota(client, headers_administrador, "Manaus - Parintins", ["Manaus", "Parintins"])
    _criar_rota(client, headers_administrador, "Manaus - Tefe", ["Manaus", "Careiro", "Tefe"])

    resposta = client.get("/rotas/destinos", headers=headers_cliente).json()

    assert [(d["rota_nome"], d["nome"]) for d in resposta] == [
        ("Manaus - Parintins", "Parintins"),
        ("Manaus - Tefe", "Careiro"),
        ("Manaus - Tefe", "Tefe"),
    ]


def test_destinos_sem_paradas_alem_da_origem_retorna_lista_vazia(
    client, headers_cliente, headers_administrador
):
    _criar_rota(client, headers_administrador, "Rota so com origem", ["Manaus"])

    assert client.get("/rotas/destinos", headers=headers_cliente).json() == []


def test_destinos_nao_conflita_com_detalhe_da_rota(client, headers_administrador, rota_com_paradas):
    resposta = client.get(f"/rotas/{rota_com_paradas.rota.id}", headers=headers_administrador)

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Manaus - Coari"


def test_destinos_de_uma_rota_vem_na_ordem_das_paradas_mesmo_criadas_fora_de_ordem(
    client, headers_cliente, headers_administrador
):
    """O frontend do cliente calcula a proxima parada contando com esta ordem (rota, depois ordem)."""
    rota = client.post("/rotas", json={"nome": "Manaus - Coari"}, headers=headers_administrador).json()
    for nome, ordem in [("Coari", 4), ("Manaus", 1), ("Tefe", 3), ("Careiro", 2)]:
        client.post(
            f"/rotas/{rota['id']}/paradas",
            json={"nome": nome, "ordem": ordem},
            headers=headers_administrador,
        )

    resposta = client.get("/rotas/destinos", headers=headers_cliente).json()

    assert [d["nome"] for d in resposta] == ["Careiro", "Tefe", "Coari"]
