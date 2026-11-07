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


def test_crud_de_rota(client, headers_administrador):
    rota_id = _criar_rota(client, headers_administrador)

    lista = client.get("/rotas", headers=headers_administrador)
    assert [r["id"] for r in lista.json()] == [rota_id]

    editada = client.patch(f"/rotas/{rota_id}", json={"nome": "Manaus - Coari"}, headers=headers_administrador)
    assert editada.status_code == 200
    assert editada.json()["nome"] == "Manaus - Coari"

    assert client.delete(f"/rotas/{rota_id}", headers=headers_administrador).status_code == 204
    assert client.get(f"/rotas/{rota_id}", headers=headers_administrador).status_code == 404


def test_detalhe_da_rota_lista_paradas_ordenadas(client, headers_administrador):
    rota_id = _criar_rota(client, headers_administrador)
    for nome, ordem in [("Tefe", 3), ("Manaus", 1), ("Coari", 2)]:
        assert _criar_parada(client, headers_administrador, rota_id, nome, ordem).status_code == 201

    detalhe = client.get(f"/rotas/{rota_id}", headers=headers_administrador).json()
    assert [p["nome"] for p in detalhe["paradas"]] == ["Manaus", "Coari", "Tefe"]

    paradas = client.get(f"/rotas/{rota_id}/paradas", headers=headers_administrador).json()
    assert [p["ordem"] for p in paradas] == [1, 2, 3]


def test_ordem_repetida_na_rota_retorna_409(client, headers_administrador):
    rota_id = _criar_rota(client, headers_administrador)
    _criar_parada(client, headers_administrador, rota_id, "Manaus", 1)
    _criar_parada(client, headers_administrador, rota_id, "Tefe", 2)

    assert _criar_parada(client, headers_administrador, rota_id, "Coari", 2).status_code == 409

    parada_id = _criar_parada(client, headers_administrador, rota_id, "Coari", 3).json()["id"]
    conflito = client.patch(f"/rotas/{rota_id}/paradas/{parada_id}", json={"ordem": 2}, headers=headers_administrador)
    assert conflito.status_code == 409


def test_editar_e_excluir_parada(client, headers_administrador):
    rota_id = _criar_rota(client, headers_administrador)
    _criar_parada(client, headers_administrador, rota_id, "Manaus", 1)
    parada_id = _criar_parada(client, headers_administrador, rota_id, "Tefe", 2).json()["id"]

    editada = client.patch(f"/rotas/{rota_id}/paradas/{parada_id}", json={"nome": "Porto de Tefe"}, headers=headers_administrador)
    assert editada.status_code == 200
    assert editada.json()["nome"] == "Porto de Tefe"

    assert client.delete(f"/rotas/{rota_id}/paradas/{parada_id}", headers=headers_administrador).status_code == 204
    nomes = [p["nome"] for p in client.get(f"/rotas/{rota_id}/paradas", headers=headers_administrador).json()]
    assert nomes == ["Manaus"]


def test_parada_de_outra_rota_retorna_404(client, headers_administrador):
    rota_a = _criar_rota(client, headers_administrador, "A")
    rota_b = _criar_rota(client, headers_administrador, "B")
    parada_id = _criar_parada(client, headers_administrador, rota_a, "Manaus", 1).json()["id"]

    assert client.patch(f"/rotas/{rota_b}/paradas/{parada_id}", json={"nome": "X"}, headers=headers_administrador).status_code == 404
    assert client.delete(f"/rotas/{rota_b}/paradas/{parada_id}", headers=headers_administrador).status_code == 404


def test_excluir_rota_remove_suas_paradas(client, db_session, headers_administrador):
    rota_id = _criar_rota(client, headers_administrador)
    _criar_parada(client, headers_administrador, rota_id, "Manaus", 1)

    client.delete(f"/rotas/{rota_id}", headers=headers_administrador)

    assert db_session.query(Parada).count() == 0


def test_rota_inexistente_retorna_404(client, headers_administrador):
    assert client.get("/rotas/999", headers=headers_administrador).status_code == 404
    assert _criar_parada(client, headers_administrador, 999, "X", 1).status_code == 404
    assert client.get("/rotas/999/paradas", headers=headers_administrador).status_code == 404


def test_ordem_invalida_retorna_422(client, headers_administrador):
    rota_id = _criar_rota(client, headers_administrador)
    assert _criar_parada(client, headers_administrador, rota_id, "X", 0).status_code == 422


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


def test_nao_exclui_rota_que_ja_possui_viagens(client, db_session, headers_administrador):
    from datetime import datetime

    from app.models.embarcacao import Embarcacao
    from app.models.viagem import Viagem

    rota_id = _criar_rota(client, headers_administrador)
    assert _criar_parada(client, headers_administrador, rota_id, "Manaus", 1).status_code == 201
    embarcacao = Embarcacao(nome="Rio Negro I", capacidade=120)
    db_session.add(embarcacao)
    db_session.commit()
    db_session.add(
        Viagem(embarcacao_id=embarcacao.id, rota_id=rota_id, data_saida=datetime(2026, 12, 1, 8, 0))
    )
    db_session.commit()

    resposta = client.delete(f"/rotas/{rota_id}", headers=headers_administrador)

    assert resposta.status_code == 409
    assert "viagens" in resposta.json()["detail"]
    detalhe = client.get(f"/rotas/{rota_id}", headers=headers_administrador)
    assert detalhe.status_code == 200
    assert [p["nome"] for p in detalhe.json()["paradas"]] == ["Manaus"]


# ---------- Permissoes: so administrador altera rotas e paradas ----------


def _chamadas_de_escrita(client, h):
    return [
        client.post("/rotas", json={"nome": "X"}, headers=h),
        client.patch("/rotas/1", json={"nome": "X"}, headers=h),
        client.delete("/rotas/1", headers=h),
        client.post("/rotas/1/paradas", json={"nome": "Manaus", "ordem": 1}, headers=h),
        client.patch("/rotas/1/paradas/1", json={"nome": "X"}, headers=h),
        client.delete("/rotas/1/paradas/1", headers=h),
    ]


def test_atendente_nao_altera_rotas_e_paradas(client, headers_atendente):
    for resposta in _chamadas_de_escrita(client, headers_atendente):
        assert resposta.status_code == 403
        assert resposta.json()["detail"] == "Acao restrita a administradores."


def test_operador_nao_altera_rotas_e_paradas(client, headers_empresa):
    for resposta in _chamadas_de_escrita(client, headers_empresa):
        assert resposta.status_code == 403


def test_atendente_nao_altera_nada_mesmo_com_rota_existente(
    client, headers_administrador, headers_atendente
):
    rota_id = _criar_rota(client, headers_administrador)
    parada_id = _criar_parada(client, headers_administrador, rota_id, "Manaus", 1).json()["id"]
    h = headers_atendente

    assert client.patch(f"/rotas/{rota_id}", json={"nome": "Outro"}, headers=h).status_code == 403
    assert client.post(f"/rotas/{rota_id}/paradas", json={"nome": "Tefe", "ordem": 2}, headers=h).status_code == 403
    assert client.patch(f"/rotas/{rota_id}/paradas/{parada_id}", json={"nome": "Manaus"}, headers=h).status_code == 403
    assert client.delete(f"/rotas/{rota_id}/paradas/{parada_id}", headers=h).status_code == 403
    assert client.delete(f"/rotas/{rota_id}", headers=h).status_code == 403

    detalhe = client.get(f"/rotas/{rota_id}", headers=h).json()
    assert detalhe["nome"] == "Manaus - Tefe"
    assert [p["nome"] for p in detalhe["paradas"]] == ["Manaus"]


def test_leituras_de_rotas_continuam_abertas_a_qualquer_perfil_da_empresa(
    client, headers_administrador, headers_atendente, headers_empresa
):
    rota_id = _criar_rota(client, headers_administrador)
    _criar_parada(client, headers_administrador, rota_id, "Manaus", 1)

    for h in (headers_atendente, headers_empresa):
        assert [r["id"] for r in client.get("/rotas", headers=h).json()] == [rota_id]
        assert client.get(f"/rotas/{rota_id}", headers=h).status_code == 200
        assert len(client.get(f"/rotas/{rota_id}/paradas", headers=h).json()) == 1


# ---------- Parada de ordem 1 deve ser Manaus ----------


def test_parada_de_ordem_1_que_nao_e_manaus_retorna_422(client, headers_administrador):
    rota_id = _criar_rota(client, headers_administrador)

    resposta = _criar_parada(client, headers_administrador, rota_id, "Coari", 1)

    assert resposta.status_code == 422
    assert resposta.json()["detail"] == "A parada de ordem 1 de uma rota deve ser Manaus."
    assert client.get(f"/rotas/{rota_id}/paradas", headers=headers_administrador).json() == []


def test_parada_de_ordem_1_aceita_manaus_com_qualquer_caixa_e_espacos(client, headers_administrador):
    rota_id = _criar_rota(client, headers_administrador)

    assert _criar_parada(client, headers_administrador, rota_id, "  MANAUS ", 1).status_code == 201


def test_outras_ordens_nao_precisam_ser_manaus(client, headers_administrador):
    rota_id = _criar_rota(client, headers_administrador)

    assert _criar_parada(client, headers_administrador, rota_id, "Coari", 2).status_code == 201


def test_editar_para_ordem_1_ou_renomear_a_origem_exige_manaus(client, headers_administrador):
    rota_id = _criar_rota(client, headers_administrador)
    origem_id = _criar_parada(client, headers_administrador, rota_id, "Manaus", 1).json()["id"]
    outra_id = _criar_parada(client, headers_administrador, rota_id, "Tefe", 2).json()["id"]
    url = f"/rotas/{rota_id}/paradas"

    renomear = client.patch(f"{url}/{origem_id}", json={"nome": "Coari"}, headers=headers_administrador)
    assert renomear.status_code == 422
    assert renomear.json()["detail"] == "A parada de ordem 1 de uma rota deve ser Manaus."

    mover = client.patch(f"{url}/{outra_id}", json={"ordem": 1}, headers=headers_administrador)
    assert mover.status_code == 422

    nomes = [p["nome"] for p in client.get(url, headers=headers_administrador).json()]
    assert nomes == ["Manaus", "Tefe"]


def test_editar_parada_que_nao_e_origem_continua_funcionando(client, headers_administrador):
    rota_id = _criar_rota(client, headers_administrador)
    _criar_parada(client, headers_administrador, rota_id, "Manaus", 1)
    outra_id = _criar_parada(client, headers_administrador, rota_id, "Tefe", 2).json()["id"]

    resposta = client.patch(
        f"/rotas/{rota_id}/paradas/{outra_id}", json={"ordem": 5}, headers=headers_administrador
    )

    assert resposta.status_code == 200
    assert resposta.json()["ordem"] == 5


# ---------- Parada que e destino de encomenda nao pode ser removida ----------


def test_nao_remove_parada_que_e_destino_de_encomenda(
    client, db_session, headers_administrador, rota_com_paradas, criar_encomenda_no_banco
):
    criar_encomenda_no_banco()
    rota_id = rota_com_paradas.rota.id
    destino_id = rota_com_paradas.destino.id

    resposta = client.delete(f"/rotas/{rota_id}/paradas/{destino_id}", headers=headers_administrador)

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Nao e possivel remover uma parada que e destino de encomendas."
    assert db_session.get(Parada, destino_id) is not None


def test_remove_parada_sem_encomendas_mesmo_havendo_encomendas_em_outra_parada(
    client, db_session, headers_administrador, rota_com_paradas, criar_encomenda_no_banco
):
    criar_encomenda_no_banco()  # destino: Tefe
    rota_id = rota_com_paradas.rota.id
    final_id = rota_com_paradas.final.id

    resposta = client.delete(f"/rotas/{rota_id}/paradas/{final_id}", headers=headers_administrador)

    assert resposta.status_code == 204
    assert db_session.get(Parada, final_id) is None


def test_nao_exclui_rota_com_parada_que_e_destino_de_encomenda(
    client, db_session, headers_administrador, rota_com_paradas, criar_encomenda_no_banco
):
    criar_encomenda_no_banco()
    rota_id = rota_com_paradas.rota.id

    resposta = client.delete(f"/rotas/{rota_id}", headers=headers_administrador)

    assert resposta.status_code == 409
    assert "destino de encomendas" in resposta.json()["detail"]
    assert db_session.query(Parada).filter(Parada.rota_id == rota_id).count() == 3
