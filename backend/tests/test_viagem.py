from datetime import datetime

import pytest
from sqlalchemy.exc import StatementError

from app.models.embarcacao import Embarcacao
from app.models.encomenda import StatusEncomenda
from app.models.movimentacao import Movimentacao
from app.models.parada import Parada
from app.models.rota import Rota
from app.models.viagem import StatusViagem, Viagem
from app.models.viagem_encomenda import ViagemEncomenda

SAIDA = datetime(2026, 12, 1, 8, 0)


def _embarcacao_e_rota(db_session):
    embarcacao = Embarcacao(nome="Rio Negro I", capacidade=120)
    rota = Rota(nome="Manaus - Parintins")
    db_session.add_all([embarcacao, rota])
    db_session.commit()

    return embarcacao, rota


def test_viagem_e_criada_com_status_programada_e_data_padrao(db_session):
    embarcacao, rota = _embarcacao_e_rota(db_session)

    viagem = Viagem(embarcacao_id=embarcacao.id, rota_id=rota.id, data_saida=SAIDA)
    db_session.add(viagem)
    db_session.commit()
    db_session.refresh(viagem)

    assert viagem.id is not None
    assert viagem.status == StatusViagem.PROGRAMADA
    assert viagem.data_saida == SAIDA
    assert viagem.criado_em is not None


def test_viagem_aceita_todos_os_status_do_dominio(db_session):
    embarcacao, rota = _embarcacao_e_rota(db_session)

    for status_viagem in StatusViagem:
        viagem = Viagem(
            embarcacao_id=embarcacao.id,
            rota_id=rota.id,
            data_saida=SAIDA,
            status=status_viagem,
        )
        db_session.add(viagem)
        db_session.commit()
        db_session.refresh(viagem)

        assert viagem.status == status_viagem

    assert {s.value for s in StatusViagem} == {
        "programada",
        "em_andamento",
        "concluida",
        "cancelada",
    }


def test_viagem_rejeita_status_invalido(db_session):
    embarcacao, rota = _embarcacao_e_rota(db_session)

    viagem = Viagem(
        embarcacao_id=embarcacao.id,
        rota_id=rota.id,
        data_saida=SAIDA,
        status="inexistente",
    )
    db_session.add(viagem)

    with pytest.raises((StatementError, LookupError)):
        db_session.commit()


# ---------- T5.2: POST /viagens ----------


def _criar_embarcacao_api(client, headers):
    resposta = client.post(
        "/embarcacoes", json={"nome": "Rio Negro I", "capacidade": 120}, headers=headers
    )
    assert resposta.status_code == 201
    return resposta.json()["id"]


def _criar_rota_api(client, headers):
    """Rota "Manaus - Coari" com paradas (Manaus, Tefe, Coari).

    E a mesma rota da fixture rota_com_paradas, que guarda o destino das
    encomendas de criar_encomenda_no_banco: se ela ja existe, e reaproveitada.
    """
    for rota in client.get("/rotas", headers=headers).json():
        if rota["nome"] == "Manaus - Coari":
            return rota["id"]

    resposta = client.post("/rotas", json={"nome": "Manaus - Coari"}, headers=headers)
    assert resposta.status_code == 201
    rota_id = resposta.json()["id"]
    for ordem, nome in enumerate(["Manaus", "Tefe", "Coari"], start=1):
        parada = client.post(
            f"/rotas/{rota_id}/paradas", json={"nome": nome, "ordem": ordem}, headers=headers
        )
        assert parada.status_code == 201
    return rota_id


def _dados_viagem(client, headers):
    return {
        "embarcacao_id": _criar_embarcacao_api(client, headers),
        "rota_id": _criar_rota_api(client, headers),
        "data_saida": "2026-12-01T08:00:00",
    }


def test_empresa_cadastra_viagem_programada(client, headers_administrador):
    dados = _dados_viagem(client, headers_administrador)

    resposta = client.post("/viagens", json=dados, headers=headers_administrador)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["embarcacao_id"] == dados["embarcacao_id"]
    assert corpo["rota_id"] == dados["rota_id"]
    assert corpo["data_saida"] == "2026-12-01T08:00:00"
    assert corpo["status"] == "programada"


def test_cadastro_ignora_status_enviado_pelo_cliente_http(client, headers_administrador):
    dados = _dados_viagem(client, headers_administrador)

    resposta = client.post(
        "/viagens", json={**dados, "status": "concluida"}, headers=headers_administrador
    )

    assert resposta.status_code == 201
    assert resposta.json()["status"] == "programada"


def test_cadastro_com_embarcacao_inexistente_retorna_404(client, headers_administrador):
    dados = _dados_viagem(client, headers_administrador)

    resposta = client.post(
        "/viagens", json={**dados, "embarcacao_id": 999}, headers=headers_administrador
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Embarcacao nao encontrada."


def test_cadastro_com_rota_inexistente_retorna_404(client, headers_administrador):
    dados = _dados_viagem(client, headers_administrador)

    resposta = client.post(
        "/viagens", json={**dados, "rota_id": 999}, headers=headers_administrador
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Rota nao encontrada."


def test_cadastro_com_dados_invalidos_retorna_422(client, headers_administrador):
    dados = _dados_viagem(client, headers_administrador)

    sem_data = {k: v for k, v in dados.items() if k != "data_saida"}
    assert client.post("/viagens", json=sem_data, headers=headers_administrador).status_code == 422
    data_ruim = {**dados, "data_saida": "amanha"}
    assert client.post("/viagens", json=data_ruim, headers=headers_administrador).status_code == 422


def test_cadastro_de_viagem_sem_login_retorna_401(client):
    corpo = {"embarcacao_id": 1, "rota_id": 1, "data_saida": "2026-12-01T08:00:00"}

    assert client.post("/viagens", json=corpo).status_code == 401


def test_cliente_nao_cadastra_viagem(client, headers_cliente):
    corpo = {"embarcacao_id": 1, "rota_id": 1, "data_saida": "2026-12-01T08:00:00"}

    assert client.post("/viagens", json=corpo, headers=headers_cliente).status_code == 403


# ---------- T5.3: POST /viagens/{id}/encomendas ----------


def _criar_viagem_api(client, headers, **alteracoes):
    resposta = client.post("/viagens", json={**_dados_viagem(client, headers), **alteracoes}, headers=headers)
    assert resposta.status_code == 201
    return resposta.json()["id"]


def _definir_status_viagem(db_session, viagem_id, novo_status):
    viagem = db_session.get(Viagem, viagem_id)
    viagem.status = novo_status
    db_session.commit()


def test_empresa_associa_encomenda_a_viagem(client, headers_administrador, criar_encomenda_no_banco):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)

    resposta = client.post(
        f"/viagens/{viagem_id}/encomendas",
        json={"encomenda_id": encomenda.id},
        headers=headers_administrador,
    )

    assert resposta.status_code == 201
    assert resposta.json()["viagem_id"] == viagem_id
    assert resposta.json()["encomenda_id"] == encomenda.id


def test_associar_leva_encomenda_a_aguardando_embarque_com_movimentacao(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)

    resposta = _associar_http(client, headers_administrador, viagem_id, encomenda)

    assert resposta.status_code == 201
    db_session.refresh(encomenda)
    assert encomenda.status == StatusEncomenda.AGUARDANDO_EMBARQUE
    historico = _historico_de(db_session, encomenda.id)
    assert [m.status for m in historico] == [
        StatusEncomenda.RECEBIDA,
        StatusEncomenda.AGUARDANDO_EMBARQUE,
    ]
    assert historico[-1].viagem_id == viagem_id


def test_associar_encomenda_ja_aguardando_embarque_nao_duplica_movimentacao(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.AGUARDANDO_EMBARQUE)

    assert _associar_http(client, headers_administrador, viagem_id, encomenda).status_code == 201

    db_session.refresh(encomenda)
    assert encomenda.status == StatusEncomenda.AGUARDANDO_EMBARQUE
    assert len(_historico_de(db_session, encomenda.id)) == 1


def test_associar_recusado_nao_altera_status_nem_movimentacao(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    _definir_status_viagem(db_session, viagem_id, StatusViagem.CONCLUIDA)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)

    resposta = _associar_http(client, headers_administrador, viagem_id, encomenda)

    assert resposta.status_code == 409
    db_session.refresh(encomenda)
    assert encomenda.status == StatusEncomenda.RECEBIDA
    assert len(_historico_de(db_session, encomenda.id)) == 1


def test_associar_e_desassociar_fecha_o_ciclo_recebida_aguardando_recebida(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)

    _associar_http(client, headers_administrador, viagem_id, encomenda)
    assert _remover(client, headers_administrador, viagem_id, encomenda.id).status_code == 204

    db_session.refresh(encomenda)
    assert encomenda.status == StatusEncomenda.RECEBIDA
    assert [m.status for m in _historico_de(db_session, encomenda.id)] == [
        StatusEncomenda.RECEBIDA,
        StatusEncomenda.AGUARDANDO_EMBARQUE,
        StatusEncomenda.RECEBIDA,
    ]


def test_viagem_em_andamento_aceita_encomenda(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    _definir_status_viagem(db_session, viagem_id, StatusViagem.EM_ANDAMENTO)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)

    resposta = client.post(
        f"/viagens/{viagem_id}/encomendas",
        json={"encomenda_id": encomenda.id},
        headers=headers_administrador,
    )

    assert resposta.status_code == 201


def test_varias_encomendas_na_mesma_viagem(client, headers_administrador, criar_encomenda_no_banco):
    viagem_id = _criar_viagem_api(client, headers_administrador)

    for _ in range(2):
        encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
        resposta = client.post(
            f"/viagens/{viagem_id}/encomendas",
            json={"encomenda_id": encomenda.id},
            headers=headers_administrador,
        )
        assert resposta.status_code == 201


def test_mesma_encomenda_nao_entra_em_duas_viagens_ativas(
    client, headers_administrador, criar_encomenda_no_banco
):
    viagem_a = _criar_viagem_api(client, headers_administrador)
    viagem_b = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    corpo = {"encomenda_id": encomenda.id}

    assert client.post(f"/viagens/{viagem_a}/encomendas", json=corpo, headers=headers_administrador).status_code == 201

    outra_viagem = client.post(f"/viagens/{viagem_b}/encomendas", json=corpo, headers=headers_administrador)
    assert outra_viagem.status_code == 409
    assert outra_viagem.json()["detail"] == "Encomenda ja esta associada a uma viagem ativa."

    mesma_viagem = client.post(f"/viagens/{viagem_a}/encomendas", json=corpo, headers=headers_administrador)
    assert mesma_viagem.status_code == 409


def test_encomenda_pode_ser_realocada_apos_viagem_deixar_de_estar_ativa(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    viagem_a = _criar_viagem_api(client, headers_administrador)
    viagem_b = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    corpo = {"encomenda_id": encomenda.id}
    client.post(f"/viagens/{viagem_a}/encomendas", json=corpo, headers=headers_administrador)

    _definir_status_viagem(db_session, viagem_a, StatusViagem.CANCELADA)

    resposta = client.post(f"/viagens/{viagem_b}/encomendas", json=corpo, headers=headers_administrador)
    assert resposta.status_code == 201


@pytest.mark.parametrize("status_final", [StatusViagem.CONCLUIDA, StatusViagem.CANCELADA])
def test_viagem_concluida_ou_cancelada_nao_aceita_encomenda(
    client, db_session, headers_administrador, criar_encomenda_no_banco, status_final
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    _definir_status_viagem(db_session, viagem_id, status_final)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)

    resposta = client.post(
        f"/viagens/{viagem_id}/encomendas",
        json={"encomenda_id": encomenda.id},
        headers=headers_administrador,
    )

    assert resposta.status_code == 409


def test_associar_com_viagem_ou_encomenda_inexistente_retorna_404(
    client, headers_administrador, criar_encomenda_no_banco
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)

    sem_viagem = client.post("/viagens/999/encomendas", json={"encomenda_id": encomenda.id}, headers=headers_administrador)
    assert sem_viagem.status_code == 404
    assert sem_viagem.json()["detail"] == "Viagem nao encontrada."

    sem_encomenda = client.post(f"/viagens/{viagem_id}/encomendas", json={"encomenda_id": 999}, headers=headers_administrador)
    assert sem_encomenda.status_code == 404
    assert sem_encomenda.json()["detail"] == "Encomenda nao encontrada."


def test_associar_encomenda_exige_empresa_logada(client, headers_cliente):
    corpo = {"encomenda_id": 1}

    assert client.post("/viagens/1/encomendas", json=corpo).status_code == 401
    assert client.post("/viagens/1/encomendas", json=corpo, headers=headers_cliente).status_code == 403


# ---------- T5.4: PATCH /viagens/{id}/status ----------


def _patch_status(client, headers, viagem_id, novo_status):
    return client.patch(
        f"/viagens/{viagem_id}/status", json={"status": novo_status}, headers=headers
    )


def test_fluxo_completo_programada_em_andamento_concluida(client, headers_administrador):
    viagem_id = _criar_viagem_api(client, headers_administrador)

    em_andamento = _patch_status(client, headers_administrador, viagem_id, "em_andamento")
    assert em_andamento.status_code == 200
    assert em_andamento.json()["status"] == "em_andamento"

    concluida = _patch_status(client, headers_administrador, viagem_id, "concluida")
    assert concluida.status_code == 200
    assert concluida.json()["status"] == "concluida"


@pytest.mark.parametrize("passos", [[], ["em_andamento"]])
def test_viagem_pode_ser_cancelada_se_programada_ou_em_andamento(client, headers_administrador, passos):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    for passo in passos:
        assert _patch_status(client, headers_administrador, viagem_id, passo).status_code == 200

    resposta = _patch_status(client, headers_administrador, viagem_id, "cancelada")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "cancelada"


@pytest.mark.parametrize(
    "caminho, destino",
    [
        ([], "concluida"),  # programada -> concluida (pula etapa)
        ([], "programada"),  # mesmo status
        (["em_andamento"], "programada"),  # volta
        (["em_andamento", "concluida"], "cancelada"),  # final
        (["em_andamento", "concluida"], "em_andamento"),  # final
        (["cancelada"], "programada"),  # final
        (["cancelada"], "em_andamento"),  # final
    ],
)
def test_transicoes_invalidas_retornam_409_e_nao_alteram_a_viagem(
    client, db_session, headers_administrador, caminho, destino
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    for passo in caminho:
        assert _patch_status(client, headers_administrador, viagem_id, passo).status_code == 200
    status_antes = caminho[-1] if caminho else "programada"

    resposta = _patch_status(client, headers_administrador, viagem_id, destino)

    assert resposta.status_code == 409
    assert "Transicao de status invalida" in resposta.json()["detail"]
    db_session.expire_all()
    assert db_session.get(Viagem, viagem_id).status.value == status_antes


def test_status_desconhecido_retorna_422(client, headers_administrador):
    viagem_id = _criar_viagem_api(client, headers_administrador)

    assert _patch_status(client, headers_administrador, viagem_id, "voando").status_code == 422


def test_atualizar_status_de_viagem_inexistente_retorna_404(client, headers_administrador):
    resposta = _patch_status(client, headers_administrador, 999, "em_andamento")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Viagem nao encontrada."


def test_atualizar_status_da_viagem_exige_empresa_logada(client, headers_cliente):
    corpo = {"status": "em_andamento"}

    assert client.patch("/viagens/1/status", json=corpo).status_code == 401
    assert client.patch("/viagens/1/status", json=corpo, headers=headers_cliente).status_code == 403


# ---------- T5.5: cancelamento -> encomendas viram imprevisto ----------


def test_cancelar_viagem_marca_encomendas_associadas_como_imprevisto(
    client, db_session, headers_administrador, criar_encomenda_no_banco,
    associar_a_viagem
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomendas = [
        criar_encomenda_no_banco(StatusEncomenda.PENDENTE),
        criar_encomenda_no_banco(StatusEncomenda.EMBARCADA),
        criar_encomenda_no_banco(StatusEncomenda.EM_TRANSITO),
    ]
    for encomenda in encomendas:
        associar_a_viagem(headers_administrador, viagem_id, encomenda)

    resposta = _patch_status(client, headers_administrador, viagem_id, "cancelada")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "cancelada"
    db_session.expire_all()
    assert [e.status for e in encomendas] == [StatusEncomenda.IMPREVISTO] * 3


def test_cancelar_viagem_em_andamento_tambem_marca_imprevisto(
    client, db_session, headers_administrador, criar_encomenda_no_banco,
    associar_a_viagem
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.EM_TRANSITO)
    associar_a_viagem(headers_administrador, viagem_id, encomenda)
    _patch_status(client, headers_administrador, viagem_id, "em_andamento")

    assert _patch_status(client, headers_administrador, viagem_id, "cancelada").status_code == 200

    db_session.refresh(encomenda)
    assert encomenda.status == StatusEncomenda.IMPREVISTO


def test_cancelar_viagem_nao_altera_encomenda_ja_entregue(
    client, db_session, headers_administrador, criar_encomenda_no_banco,
    associar_a_viagem
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    entregue = criar_encomenda_no_banco(StatusEncomenda.ENTREGUE)
    pendente = criar_encomenda_no_banco(StatusEncomenda.PENDENTE)
    associar_a_viagem(headers_administrador, viagem_id, entregue)
    associar_a_viagem(headers_administrador, viagem_id, pendente)

    _patch_status(client, headers_administrador, viagem_id, "cancelada")

    db_session.expire_all()
    assert entregue.status == StatusEncomenda.ENTREGUE
    assert pendente.status == StatusEncomenda.IMPREVISTO


def test_cancelar_viagem_nao_afeta_encomendas_de_outras_viagens_nem_sem_viagem(
    client, db_session, headers_administrador, criar_encomenda_no_banco,
    associar_a_viagem
):
    viagem_cancelada = _criar_viagem_api(client, headers_administrador)
    outra_viagem = _criar_viagem_api(client, headers_administrador)
    da_cancelada = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    da_outra = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    sem_viagem = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    associar_a_viagem(headers_administrador, viagem_cancelada, da_cancelada)
    associar_a_viagem(headers_administrador, outra_viagem, da_outra)

    _patch_status(client, headers_administrador, viagem_cancelada, "cancelada")

    db_session.expire_all()
    assert da_cancelada.status == StatusEncomenda.IMPREVISTO
    assert da_outra.status == StatusEncomenda.RECEBIDA
    assert sem_viagem.status == StatusEncomenda.RECEBIDA


@pytest.mark.parametrize("novo_status", ["em_andamento", "concluida"])
def test_outras_transicoes_nao_alteram_status_das_encomendas(
    client, db_session, headers_administrador, criar_encomenda_no_banco, novo_status,
    associar_a_viagem
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.EMBARCADA)
    associar_a_viagem(headers_administrador, viagem_id, encomenda)
    if novo_status == "concluida":
        _patch_status(client, headers_administrador, viagem_id, "em_andamento")

    assert _patch_status(client, headers_administrador, viagem_id, novo_status).status_code == 200

    db_session.refresh(encomenda)
    assert encomenda.status == StatusEncomenda.EMBARCADA


def test_cancelamento_invalido_nao_altera_encomendas(
    client, db_session, headers_administrador, criar_encomenda_no_banco,
    associar_a_viagem
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.EMBARCADA)
    associar_a_viagem(headers_administrador, viagem_id, encomenda)
    _patch_status(client, headers_administrador, viagem_id, "em_andamento")
    _patch_status(client, headers_administrador, viagem_id, "concluida")

    assert _patch_status(client, headers_administrador, viagem_id, "cancelada").status_code == 409

    db_session.refresh(encomenda)
    assert encomenda.status == StatusEncomenda.EMBARCADA


def test_encomenda_imprevisto_so_e_realocada_depois_de_voltar_a_recebida(
    client, db_session, headers_administrador, criar_encomenda_no_banco, associar_a_viagem
):
    viagem_cancelada = _criar_viagem_api(client, headers_administrador)
    nova_viagem = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    associar_a_viagem(headers_administrador, viagem_cancelada, encomenda)
    _patch_status(client, headers_administrador, viagem_cancelada, "cancelada")
    corpo = {"encomenda_id": encomenda.id}

    db_session.refresh(encomenda)
    assert encomenda.status == StatusEncomenda.IMPREVISTO
    recusada = client.post(f"/viagens/{nova_viagem}/encomendas", json=corpo, headers=headers_administrador)
    assert recusada.status_code == 409

    client.patch(
        f"/encomendas/{encomenda.id}/status", json={"status": "recebida"}, headers=headers_administrador
    )
    aceita = client.post(f"/viagens/{nova_viagem}/encomendas", json=corpo, headers=headers_administrador)
    assert aceita.status_code == 201


# ---------- T5.6: GET /viagens (filtro por status) ----------


def test_lista_vazia_quando_nao_ha_viagens(client, headers_administrador):
    resposta = client.get("/viagens", headers=headers_administrador)

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_lista_todas_as_viagens_da_mais_recente_para_a_mais_antiga(client, headers_administrador):
    antiga = _criar_viagem_api(client, headers_administrador, data_saida="2026-12-01T08:00:00")
    recente = _criar_viagem_api(client, headers_administrador, data_saida="2026-12-20T08:00:00")
    meio = _criar_viagem_api(client, headers_administrador, data_saida="2026-12-10T08:00:00")

    resposta = client.get("/viagens", headers=headers_administrador)

    assert resposta.status_code == 200
    assert [v["id"] for v in resposta.json()] == [recente, meio, antiga]


def test_filtra_viagens_por_status(client, headers_administrador):
    programada = _criar_viagem_api(client, headers_administrador)
    em_andamento = _criar_viagem_api(client, headers_administrador)
    cancelada = _criar_viagem_api(client, headers_administrador)
    _patch_status(client, headers_administrador, em_andamento, "em_andamento")
    _patch_status(client, headers_administrador, cancelada, "cancelada")

    def ids(filtro):
        resposta = client.get(f"/viagens?status={filtro}", headers=headers_administrador)
        assert resposta.status_code == 200
        return {v["id"] for v in resposta.json()}

    assert ids("programada") == {programada}
    assert ids("em_andamento") == {em_andamento}
    assert ids("cancelada") == {cancelada}
    assert ids("concluida") == set()


def test_filtro_com_status_invalido_retorna_422(client, headers_administrador):
    assert client.get("/viagens?status=voando", headers=headers_administrador).status_code == 422


def test_listagem_de_viagens_exige_empresa_logada(client, headers_cliente):
    assert client.get("/viagens").status_code == 401
    assert client.get("/viagens", headers=headers_cliente).status_code == 403


# ---------- T5.7: GET /viagens/{id} ----------


def test_detalhe_da_viagem_traz_embarcacao_e_rota_com_paradas(client, headers_administrador):
    dados = {
        "embarcacao_id": _criar_embarcacao_api(client, headers_administrador),
        "rota_id": client.post(
            "/rotas", json={"nome": "Manaus - Parintins"}, headers=headers_administrador
        ).json()["id"],
        "data_saida": "2026-12-01T08:00:00",
    }
    for nome, ordem in [("Parintins", 2), ("Manaus", 1)]:
        client.post(
            f"/rotas/{dados['rota_id']}/paradas",
            json={"nome": nome, "ordem": ordem},
            headers=headers_administrador,
        )
    viagem_id = client.post("/viagens", json=dados, headers=headers_administrador).json()["id"]

    resposta = client.get(f"/viagens/{viagem_id}", headers=headers_administrador)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["id"] == viagem_id
    assert corpo["status"] == "programada"
    assert corpo["data_saida"] == "2026-12-01T08:00:00"
    assert corpo["embarcacao"]["id"] == dados["embarcacao_id"]
    assert corpo["embarcacao"]["nome"] == "Rio Negro I"
    assert corpo["embarcacao"]["capacidade"] == 120
    assert corpo["rota"]["id"] == dados["rota_id"]
    assert corpo["rota"]["nome"] == "Manaus - Parintins"
    assert [p["nome"] for p in corpo["rota"]["paradas"]] == ["Manaus", "Parintins"]


def test_detalhe_de_viagem_inexistente_retorna_404(client, headers_administrador):
    resposta = client.get("/viagens/999", headers=headers_administrador)

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Viagem nao encontrada."


def test_detalhe_da_viagem_exige_empresa_logada(client, headers_cliente):
    assert client.get("/viagens/1").status_code == 401
    assert client.get("/viagens/1", headers=headers_cliente).status_code == 403


# ---------- T5.8: GET /viagens/{id}/encomendas ----------


def test_lista_apenas_as_encomendas_associadas_a_viagem(
    client, headers_administrador, criar_encomenda_no_banco,
    associar_a_viagem
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    outra_viagem = _criar_viagem_api(client, headers_administrador)
    primeira = criar_encomenda_no_banco()
    segunda = criar_encomenda_no_banco()
    de_outra = criar_encomenda_no_banco()
    criar_encomenda_no_banco()  # sem viagem
    associar_a_viagem(headers_administrador, viagem_id, segunda)
    associar_a_viagem(headers_administrador, viagem_id, primeira)
    associar_a_viagem(headers_administrador, outra_viagem, de_outra)

    resposta = client.get(f"/viagens/{viagem_id}/encomendas", headers=headers_administrador)

    assert resposta.status_code == 200
    assert [e["id"] for e in resposta.json()] == [segunda.id, primeira.id]
    assert resposta.json()[0]["codigo_rastreio"] == segunda.codigo_rastreio
    assert resposta.json()[0]["status"] == "pendente"


def test_viagem_sem_encomendas_retorna_lista_vazia(client, headers_administrador):
    viagem_id = _criar_viagem_api(client, headers_administrador)

    resposta = client.get(f"/viagens/{viagem_id}/encomendas", headers=headers_administrador)

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_viagem_cancelada_continua_listando_suas_encomendas(
    client, headers_administrador, criar_encomenda_no_banco,
    associar_a_viagem
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco()
    associar_a_viagem(headers_administrador, viagem_id, encomenda)
    _patch_status(client, headers_administrador, viagem_id, "cancelada")

    resposta = client.get(f"/viagens/{viagem_id}/encomendas", headers=headers_administrador)

    assert [(e["id"], e["status"]) for e in resposta.json()] == [(encomenda.id, "imprevisto")]


def test_listar_encomendas_de_viagem_inexistente_retorna_404(client, headers_administrador):
    resposta = client.get("/viagens/999/encomendas", headers=headers_administrador)

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Viagem nao encontrada."


def test_listar_encomendas_da_viagem_exige_empresa_logada(client, headers_cliente):
    assert client.get("/viagens/1/encomendas").status_code == 401
    assert client.get("/viagens/1/encomendas", headers=headers_cliente).status_code == 403


# ---------- regras de associacao e programacao de viagem ----------


def _associar_http(client, headers, viagem_id, encomenda):
    return client.post(
        f"/viagens/{viagem_id}/encomendas",
        json={"encomenda_id": encomenda.id},
        headers=headers,
    )


def _vinculos(db_session, viagem_id):
    db_session.expire_all()
    return db_session.query(ViagemEncomenda).filter_by(viagem_id=viagem_id).count()


def _viagem_com_capacidade(client, headers, capacidade):
    embarcacao_id = client.post(
        "/embarcacoes", json={"nome": "Barco Pequeno", "capacidade": capacidade}, headers=headers
    ).json()["id"]

    return _criar_viagem_api(client, headers, embarcacao_id=embarcacao_id)


@pytest.mark.parametrize(
    "status_encomenda",
    [StatusEncomenda.RECEBIDA, StatusEncomenda.AGUARDANDO_EMBARQUE],
)
def test_associar_aceita_encomenda_recebida_ou_aguardando_embarque(
    client, headers_administrador, criar_encomenda_no_banco, status_encomenda
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(status_encomenda)

    assert _associar_http(client, headers_administrador, viagem_id, encomenda).status_code == 201


@pytest.mark.parametrize(
    "status_encomenda",
    [
        StatusEncomenda.PENDENTE,
        StatusEncomenda.EMBARCADA,
        StatusEncomenda.EM_TRANSITO,
        StatusEncomenda.CHEGOU_AO_DESTINO,
        StatusEncomenda.A_RETIRAR,
        StatusEncomenda.ENTREGUE,
        StatusEncomenda.IMPREVISTO,
    ],
)
def test_associar_recusa_encomenda_em_outros_status(
    client, db_session, headers_administrador, criar_encomenda_no_banco, status_encomenda
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(status_encomenda)

    resposta = _associar_http(client, headers_administrador, viagem_id, encomenda)

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == (
        "So e possivel associar encomendas com status recebida ou aguardando_embarque."
    )
    assert _vinculos(db_session, viagem_id) == 0


def test_associar_recusa_encomenda_cujo_destino_nao_esta_na_rota_da_viagem(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    outra_rota = Rota(nome="Manaus - Parintins")
    db_session.add(outra_rota)
    db_session.flush()
    parada_de_fora = Parada(rota_id=outra_rota.id, nome="Parintins", ordem=2)
    db_session.add(parada_de_fora)
    db_session.commit()
    encomenda.parada_destino_id = parada_de_fora.id
    db_session.commit()

    resposta = _associar_http(client, headers_administrador, viagem_id, encomenda)

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "O destino da encomenda nao pertence a rota da viagem."
    assert _vinculos(db_session, viagem_id) == 0


def test_associar_recusa_encomenda_sem_destino(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    encomenda.parada_destino_id = None
    db_session.commit()

    resposta = _associar_http(client, headers_administrador, viagem_id, encomenda)

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "A encomenda nao tem destino definido."
    assert _vinculos(db_session, viagem_id) == 0


def test_associar_respeita_a_capacidade_da_embarcacao(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    viagem_id = _viagem_com_capacidade(client, headers_administrador, capacidade=2)
    primeira, segunda, terceira = (
        criar_encomenda_no_banco(StatusEncomenda.RECEBIDA) for _ in range(3)
    )

    assert _associar_http(client, headers_administrador, viagem_id, primeira).status_code == 201
    assert _associar_http(client, headers_administrador, viagem_id, segunda).status_code == 201
    resposta = _associar_http(client, headers_administrador, viagem_id, terceira)

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "A embarcacao da viagem nao tem capacidade para mais encomendas."
    assert _vinculos(db_session, viagem_id) == 2


@pytest.mark.parametrize(
    "status_liberado", [StatusEncomenda.ENTREGUE, StatusEncomenda.IMPREVISTO]
)
def test_encomenda_entregue_ou_imprevisto_nao_ocupa_capacidade(
    client, db_session, headers_administrador, criar_encomenda_no_banco, associar_a_viagem, status_liberado
):
    viagem_id = _viagem_com_capacidade(client, headers_administrador, capacidade=1)
    ocupando = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    nova = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    associar_a_viagem(headers_administrador, viagem_id, ocupando)
    assert _associar_http(client, headers_administrador, viagem_id, nova).status_code == 409

    ocupando.status = status_liberado
    db_session.commit()

    assert _associar_http(client, headers_administrador, viagem_id, nova).status_code == 201


def test_capacidade_so_conta_encomendas_da_propria_viagem(
    client, headers_administrador, criar_encomenda_no_banco
):
    viagem_cheia = _viagem_com_capacidade(client, headers_administrador, capacidade=1)
    outra_viagem = _viagem_com_capacidade(client, headers_administrador, capacidade=1)
    primeira = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    segunda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)

    assert _associar_http(client, headers_administrador, viagem_cheia, primeira).status_code == 201
    assert _associar_http(client, headers_administrador, outra_viagem, segunda).status_code == 201


def test_programar_viagem_recusa_embarcacao_inativa(client, headers_administrador):
    dados = _dados_viagem(client, headers_administrador)
    client.patch(
        f"/embarcacoes/{dados['embarcacao_id']}", json={"ativa": False}, headers=headers_administrador
    )

    resposta = client.post("/viagens", json=dados, headers=headers_administrador)

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Nao e possivel programar viagem com embarcacao inativa."
    assert client.get("/viagens", headers=headers_administrador).json() == []


def test_programar_viagem_recusa_rota_sem_paradas(client, headers_administrador):
    dados = _dados_viagem(client, headers_administrador)
    rota_vazia = client.post("/rotas", json={"nome": "Rota Vazia"}, headers=headers_administrador)
    dados["rota_id"] = rota_vazia.json()["id"]

    resposta = client.post("/viagens", json=dados, headers=headers_administrador)

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Nao e possivel programar viagem com rota sem paradas."
    assert client.get("/viagens", headers=headers_administrador).json() == []


# ---------- DELETE /viagens/{id}/encomendas/{encomenda_id} ----------


def _remover(client, headers, viagem_id, encomenda_id):
    return client.delete(f"/viagens/{viagem_id}/encomendas/{encomenda_id}", headers=headers)


def _historico_de(db_session, encomenda_id):
    db_session.expire_all()
    return (
        db_session.query(Movimentacao)
        .filter_by(encomenda_id=encomenda_id)
        .order_by(Movimentacao.id)
        .all()
    )


def test_remover_encomenda_de_viagem_programada_devolve_status_recebida_e_registra_movimentacao(
    client, db_session, headers_administrador, criar_encomenda_no_banco, associar_a_viagem
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.AGUARDANDO_EMBARQUE)
    associar_a_viagem(headers_administrador, viagem_id, encomenda)

    resposta = _remover(client, headers_administrador, viagem_id, encomenda.id)

    assert resposta.status_code == 204
    assert _vinculos(db_session, viagem_id) == 0
    db_session.refresh(encomenda)
    assert encomenda.status == StatusEncomenda.RECEBIDA
    historico = _historico_de(db_session, encomenda.id)
    assert [m.status for m in historico] == [
        StatusEncomenda.AGUARDANDO_EMBARQUE,
        StatusEncomenda.RECEBIDA,
    ]
    assert historico[-1].viagem_id == viagem_id
    assert client.get(f"/viagens/{viagem_id}/encomendas", headers=headers_administrador).json() == []


def test_remover_encomenda_ja_recebida_nao_duplica_movimentacao(
    client, db_session, headers_administrador, criar_encomenda_no_banco, associar_a_viagem
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    associar_a_viagem(headers_administrador, viagem_id, encomenda)

    assert _remover(client, headers_administrador, viagem_id, encomenda.id).status_code == 204

    db_session.refresh(encomenda)
    assert encomenda.status == StatusEncomenda.RECEBIDA
    assert len(_historico_de(db_session, encomenda.id)) == 1


def test_encomenda_removida_libera_capacidade_e_pode_ser_associada_de_novo(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    viagem_id = _viagem_com_capacidade(client, headers_administrador, capacidade=1)
    primeira = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    segunda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    _associar_http(client, headers_administrador, viagem_id, primeira)
    assert _associar_http(client, headers_administrador, viagem_id, segunda).status_code == 409

    _remover(client, headers_administrador, viagem_id, primeira.id)

    assert _associar_http(client, headers_administrador, viagem_id, segunda).status_code == 201
    assert _associar_http(client, headers_administrador, viagem_id, primeira).status_code == 409
    assert _vinculos(db_session, viagem_id) == 1


@pytest.mark.parametrize(
    "status_viagem",
    [StatusViagem.EM_ANDAMENTO, StatusViagem.CONCLUIDA, StatusViagem.CANCELADA],
)
def test_remover_so_funciona_com_viagem_programada(
    client, db_session, headers_administrador, criar_encomenda_no_banco, associar_a_viagem, status_viagem
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    associar_a_viagem(headers_administrador, viagem_id, encomenda)
    _definir_status_viagem(db_session, viagem_id, status_viagem)
    movimentacoes_antes = len(_historico_de(db_session, encomenda.id))

    resposta = _remover(client, headers_administrador, viagem_id, encomenda.id)

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "So e possivel remover encomendas de viagens programadas."
    assert _vinculos(db_session, viagem_id) == 1
    assert len(_historico_de(db_session, encomenda.id)) == movimentacoes_antes


def test_remover_encomenda_que_nao_esta_na_viagem_retorna_404(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    outra_viagem = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    _associar_http(client, headers_administrador, outra_viagem, encomenda)

    resposta = _remover(client, headers_administrador, viagem_id, encomenda.id)

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "A encomenda nao esta associada a esta viagem."
    assert _vinculos(db_session, outra_viagem) == 1


def test_remover_com_viagem_ou_encomenda_inexistente_retorna_404(
    client, headers_administrador, criar_encomenda_no_banco
):
    viagem_id = _criar_viagem_api(client, headers_administrador)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)

    sem_viagem = _remover(client, headers_administrador, 999, encomenda.id)
    sem_encomenda = _remover(client, headers_administrador, viagem_id, 999)

    assert (sem_viagem.status_code, sem_viagem.json()["detail"]) == (404, "Viagem nao encontrada.")
    assert (sem_encomenda.status_code, sem_encomenda.json()["detail"]) == (
        404,
        "Encomenda nao encontrada.",
    )


def test_remover_encomenda_da_viagem_exige_empresa_logada(client, headers_cliente):
    assert client.delete("/viagens/1/encomendas/1").status_code == 401
    assert client.delete("/viagens/1/encomendas/1", headers=headers_cliente).status_code == 403
