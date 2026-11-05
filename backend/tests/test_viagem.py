from datetime import datetime

import pytest
from sqlalchemy.exc import StatementError

from app.models.embarcacao import Embarcacao
from app.models.rota import Rota
from app.models.viagem import StatusViagem, Viagem

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
    resposta = client.post("/rotas", json={"nome": "Manaus - Parintins"}, headers=headers)
    assert resposta.status_code == 201
    return resposta.json()["id"]


def _dados_viagem(client, headers):
    return {
        "embarcacao_id": _criar_embarcacao_api(client, headers),
        "rota_id": _criar_rota_api(client, headers),
        "data_saida": "2026-12-01T08:00:00",
    }


def test_empresa_cadastra_viagem_programada(client, headers_empresa):
    dados = _dados_viagem(client, headers_empresa)

    resposta = client.post("/viagens", json=dados, headers=headers_empresa)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["embarcacao_id"] == dados["embarcacao_id"]
    assert corpo["rota_id"] == dados["rota_id"]
    assert corpo["data_saida"] == "2026-12-01T08:00:00"
    assert corpo["status"] == "programada"


def test_cadastro_ignora_status_enviado_pelo_cliente_http(client, headers_empresa):
    dados = _dados_viagem(client, headers_empresa)

    resposta = client.post(
        "/viagens", json={**dados, "status": "concluida"}, headers=headers_empresa
    )

    assert resposta.status_code == 201
    assert resposta.json()["status"] == "programada"


def test_cadastro_com_embarcacao_inexistente_retorna_404(client, headers_empresa):
    dados = _dados_viagem(client, headers_empresa)

    resposta = client.post(
        "/viagens", json={**dados, "embarcacao_id": 999}, headers=headers_empresa
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Embarcacao nao encontrada."


def test_cadastro_com_rota_inexistente_retorna_404(client, headers_empresa):
    dados = _dados_viagem(client, headers_empresa)

    resposta = client.post(
        "/viagens", json={**dados, "rota_id": 999}, headers=headers_empresa
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Rota nao encontrada."


def test_cadastro_com_dados_invalidos_retorna_422(client, headers_empresa):
    dados = _dados_viagem(client, headers_empresa)

    sem_data = {k: v for k, v in dados.items() if k != "data_saida"}
    assert client.post("/viagens", json=sem_data, headers=headers_empresa).status_code == 422
    data_ruim = {**dados, "data_saida": "amanha"}
    assert client.post("/viagens", json=data_ruim, headers=headers_empresa).status_code == 422


def test_cadastro_de_viagem_sem_login_retorna_401(client):
    corpo = {"embarcacao_id": 1, "rota_id": 1, "data_saida": "2026-12-01T08:00:00"}

    assert client.post("/viagens", json=corpo).status_code == 401


def test_cliente_nao_cadastra_viagem(client, headers_cliente):
    corpo = {"embarcacao_id": 1, "rota_id": 1, "data_saida": "2026-12-01T08:00:00"}

    assert client.post("/viagens", json=corpo, headers=headers_cliente).status_code == 403
