import pytest
from sqlalchemy import event

from app.models.encomenda import Encomenda, StatusEncomenda
from app.models.movimentacao import Movimentacao


def _criar_rota_com_paradas(client, headers, nome="Manaus - Tefe", paradas=("Manaus", "Codajas", "Tefe")):
    rota_id = client.post("/rotas", json={"nome": nome}, headers=headers).json()["id"]
    ids = []
    for ordem, nome_parada in enumerate(paradas, start=1):
        resposta = client.post(
            f"/rotas/{rota_id}/paradas",
            json={"nome": nome_parada, "ordem": ordem},
            headers=headers,
        )
        ids.append(resposta.json()["id"])

    return rota_id, ids


def _criar_viagem(client, headers, rota_id):
    embarcacao_id = client.post(
        "/embarcacoes", json={"nome": "Rio Negro I", "capacidade": 120}, headers=headers
    ).json()["id"]

    return client.post(
        "/viagens",
        json={"embarcacao_id": embarcacao_id, "rota_id": rota_id, "data_saida": "2026-12-01T08:00:00"},
        headers=headers,
    ).json()["id"]


def _associar(client, headers, viagem_id, encomenda):
    resposta = client.post(
        f"/viagens/{viagem_id}/encomendas", json={"encomenda_id": encomenda.id}, headers=headers
    )
    assert resposta.status_code == 201


def _status_viagem(client, headers, viagem_id, novo):
    resposta = client.patch(f"/viagens/{viagem_id}/status", json={"status": novo}, headers=headers)
    assert resposta.status_code == 200


def _registrar(client, headers, viagem_id, parada_id):
    return client.post(
        f"/viagens/{viagem_id}/localizacao", json={"parada_id": parada_id}, headers=headers
    )


def _historico(db_session, encomenda_id):
    return (
        db_session.query(Movimentacao)
        .filter(Movimentacao.encomenda_id == encomenda_id)
        .order_by(Movimentacao.id)
        .all()
    )


@pytest.fixture()
def viagem_em_andamento(client, headers_empresa):
    rota_id, paradas = _criar_rota_com_paradas(client, headers_empresa)
    viagem_id = _criar_viagem(client, headers_empresa, rota_id)
    _status_viagem(client, headers_empresa, viagem_id, "em_andamento")

    return viagem_id, rota_id, paradas


def test_registrar_localizacao_move_embarcada_para_em_transito_com_parada_e_viagem(
    client, db_session, headers_empresa, criar_encomenda_no_banco, viagem_em_andamento
):
    viagem_id, _, paradas = viagem_em_andamento
    encomenda = criar_encomenda_no_banco(StatusEncomenda.EMBARCADA)
    _associar(client, headers_empresa, viagem_id, encomenda)

    resposta = _registrar(client, headers_empresa, viagem_id, paradas[0])

    assert resposta.status_code == 201
    assert resposta.json() == {
        "viagem_id": viagem_id,
        "parada_id": paradas[0],
        "encomendas_registradas": 1,
    }
    db_session.refresh(encomenda)
    assert encomenda.status == StatusEncomenda.EM_TRANSITO
    historico = _historico(db_session, encomenda.id)
    assert [m.status for m in historico] == [StatusEncomenda.EMBARCADA, StatusEncomenda.EM_TRANSITO]
    assert (historico[-1].parada_id, historico[-1].viagem_id) == (paradas[0], viagem_id)


def test_encomenda_em_transito_ganha_movimentacao_de_localizacao_em_cada_parada(
    client, db_session, headers_empresa, criar_encomenda_no_banco, viagem_em_andamento
):
    viagem_id, _, paradas = viagem_em_andamento
    encomenda = criar_encomenda_no_banco(StatusEncomenda.EMBARCADA)
    _associar(client, headers_empresa, viagem_id, encomenda)

    _registrar(client, headers_empresa, viagem_id, paradas[0])
    _registrar(client, headers_empresa, viagem_id, paradas[1])
    _registrar(client, headers_empresa, viagem_id, paradas[2])

    historico = _historico(db_session, encomenda.id)
    assert [(m.status.value, m.parada_id) for m in historico] == [
        ("embarcada", None),
        ("em_transito", paradas[0]),
        ("em_transito", paradas[1]),
        ("em_transito", paradas[2]),
    ]
    assert all(m.viagem_id == viagem_id for m in historico[1:])
    db_session.refresh(encomenda)
    assert encomenda.status == StatusEncomenda.EM_TRANSITO


def test_so_encomendas_a_bordo_sao_afetadas(
    client, db_session, headers_empresa, criar_encomenda_no_banco, viagem_em_andamento
):
    viagem_id, _, paradas = viagem_em_andamento
    ficam_como_estao = [
        StatusEncomenda.PENDENTE,
        StatusEncomenda.RECEBIDA,
        StatusEncomenda.AGUARDANDO_EMBARQUE,
        StatusEncomenda.CHEGOU_AO_DESTINO,
        StatusEncomenda.A_RETIRAR,
        StatusEncomenda.ENTREGUE,
        StatusEncomenda.IMPREVISTO,
    ]
    nao_afetadas = [criar_encomenda_no_banco(s) for s in ficam_como_estao]
    a_bordo = criar_encomenda_no_banco(StatusEncomenda.EMBARCADA)
    for encomenda in [*nao_afetadas, a_bordo]:
        _associar(client, headers_empresa, viagem_id, encomenda)

    resposta = _registrar(client, headers_empresa, viagem_id, paradas[0])

    assert resposta.json()["encomendas_registradas"] == 1
    db_session.expire_all()
    for encomenda in nao_afetadas:
        assert len(_historico(db_session, encomenda.id)) == 1
    assert [e.status for e in nao_afetadas] == ficam_como_estao


def test_encomenda_de_outra_viagem_nao_e_afetada(
    client, db_session, headers_empresa, criar_encomenda_no_banco, viagem_em_andamento
):
    viagem_id, rota_id, paradas = viagem_em_andamento
    outra_viagem = _criar_viagem(client, headers_empresa, rota_id)
    _status_viagem(client, headers_empresa, outra_viagem, "em_andamento")
    da_outra = criar_encomenda_no_banco(StatusEncomenda.EMBARCADA)
    _associar(client, headers_empresa, outra_viagem, da_outra)

    resposta = _registrar(client, headers_empresa, viagem_id, paradas[0])

    assert resposta.status_code == 201
    assert resposta.json()["encomendas_registradas"] == 0
    db_session.refresh(da_outra)
    assert da_outra.status == StatusEncomenda.EMBARCADA
    assert len(_historico(db_session, da_outra.id)) == 1


def test_viagem_sem_encomendas_a_bordo_retorna_zero(client, headers_empresa, viagem_em_andamento):
    viagem_id, _, paradas = viagem_em_andamento

    resposta = _registrar(client, headers_empresa, viagem_id, paradas[0])

    assert resposta.status_code == 201
    assert resposta.json()["encomendas_registradas"] == 0


@pytest.mark.parametrize("caminho", [[], ["em_andamento", "concluida"], ["cancelada"]])
def test_viagem_fora_de_andamento_retorna_409_sem_registrar_nada(
    client, db_session, headers_empresa, criar_encomenda_no_banco, caminho
):
    rota_id, paradas = _criar_rota_com_paradas(client, headers_empresa)
    viagem_id = _criar_viagem(client, headers_empresa, rota_id)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.EMBARCADA)
    _associar(client, headers_empresa, viagem_id, encomenda)
    for passo in caminho:
        _status_viagem(client, headers_empresa, viagem_id, passo)
    movimentacoes_antes = db_session.query(Movimentacao).count()
    status_antes = db_session.get(Encomenda, encomenda.id).status

    resposta = _registrar(client, headers_empresa, viagem_id, paradas[0])

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "So e possivel registrar localizacao em viagem em andamento."
    assert db_session.query(Movimentacao).count() == movimentacoes_antes
    db_session.expire_all()
    assert db_session.get(Encomenda, encomenda.id).status == status_antes


def test_parada_de_outra_rota_retorna_409_sem_registrar_nada(
    client, db_session, headers_empresa, criar_encomenda_no_banco, viagem_em_andamento
):
    viagem_id, _, _ = viagem_em_andamento
    _, paradas_outra_rota = _criar_rota_com_paradas(
        client, headers_empresa, nome="Manaus - Parintins", paradas=("Manaus", "Parintins")
    )
    encomenda = criar_encomenda_no_banco(StatusEncomenda.EMBARCADA)
    _associar(client, headers_empresa, viagem_id, encomenda)

    resposta = _registrar(client, headers_empresa, viagem_id, paradas_outra_rota[1])

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "A parada nao pertence a rota da viagem."
    db_session.refresh(encomenda)
    assert encomenda.status == StatusEncomenda.EMBARCADA
    assert len(_historico(db_session, encomenda.id)) == 1


def test_viagem_ou_parada_inexistente_retorna_404(client, headers_empresa, viagem_em_andamento):
    viagem_id, _, paradas = viagem_em_andamento

    sem_viagem = _registrar(client, headers_empresa, 999, paradas[0])
    sem_parada = _registrar(client, headers_empresa, viagem_id, 999)

    assert (sem_viagem.status_code, sem_viagem.json()["detail"]) == (404, "Viagem nao encontrada.")
    assert (sem_parada.status_code, sem_parada.json()["detail"]) == (404, "Parada nao encontrada.")


def test_parada_id_ausente_retorna_422(client, headers_empresa, viagem_em_andamento):
    viagem_id, _, _ = viagem_em_andamento

    resposta = client.post(f"/viagens/{viagem_id}/localizacao", json={}, headers=headers_empresa)

    assert resposta.status_code == 422


def test_registro_de_localizacao_exige_empresa_logada(client, headers_cliente):
    corpo = {"parada_id": 1}

    assert client.post("/viagens/1/localizacao", json=corpo).status_code == 401
    assert client.post("/viagens/1/localizacao", json=corpo, headers=headers_cliente).status_code == 403


def test_localizacao_de_varias_encomendas_e_gravada_em_um_unico_commit(
    client, db_session, headers_empresa, criar_encomenda_no_banco, viagem_em_andamento
):
    viagem_id, _, paradas = viagem_em_andamento
    for status_encomenda in [
        StatusEncomenda.EMBARCADA,
        StatusEncomenda.EMBARCADA,
        StatusEncomenda.EM_TRANSITO,
    ]:
        _associar(client, headers_empresa, viagem_id, criar_encomenda_no_banco(status_encomenda))
    commits = []
    event.listen(db_session, "after_commit", lambda sessao: commits.append(1))

    resposta = _registrar(client, headers_empresa, viagem_id, paradas[0])

    assert resposta.json()["encomendas_registradas"] == 3
    assert len(commits) == 1
