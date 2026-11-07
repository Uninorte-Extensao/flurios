from datetime import datetime

import pytest
from sqlalchemy import event
from sqlalchemy.exc import StatementError

from app.models.embarcacao import Embarcacao
from app.models.encomenda import Encomenda, StatusEncomenda
from app.models.movimentacao import Movimentacao
from app.models.parada import Parada
from app.models.rota import Rota
from app.models.viagem import StatusViagem, Viagem
from app.services.viagem import atualizar_status_viagem


def test_movimentacao_minima_tem_parada_e_viagem_opcionais(db_session, criar_encomenda_no_banco):
    encomenda = criar_encomenda_no_banco()

    movimentacao = Movimentacao(encomenda_id=encomenda.id, status=StatusEncomenda.RECEBIDA)
    db_session.add(movimentacao)
    db_session.commit()
    db_session.refresh(movimentacao)

    assert movimentacao.id is not None
    assert movimentacao.status == StatusEncomenda.RECEBIDA
    assert movimentacao.parada_id is None
    assert movimentacao.viagem_id is None
    assert movimentacao.criado_em is not None


def test_movimentacao_aceita_parada_e_viagem(db_session, criar_encomenda_no_banco):
    encomenda = criar_encomenda_no_banco()
    embarcacao = Embarcacao(nome="Rio Negro I", capacidade=120)
    rota = Rota(nome="Manaus - Tefe")
    db_session.add_all([embarcacao, rota])
    db_session.commit()
    parada = Parada(rota_id=rota.id, nome="Manaus", ordem=1)
    viagem = Viagem(
        embarcacao_id=embarcacao.id, rota_id=rota.id, data_saida=datetime(2026, 12, 1, 8, 0)
    )
    db_session.add_all([parada, viagem])
    db_session.commit()

    movimentacao = Movimentacao(
        encomenda_id=encomenda.id,
        status=StatusEncomenda.EM_TRANSITO,
        parada_id=parada.id,
        viagem_id=viagem.id,
    )
    db_session.add(movimentacao)
    db_session.commit()
    db_session.refresh(movimentacao)

    assert movimentacao.parada_id == parada.id
    assert movimentacao.viagem_id == viagem.id


def test_movimentacao_aceita_todos_os_status_da_encomenda(db_session, criar_encomenda_no_banco):
    encomenda = criar_encomenda_no_banco()
    ja_existentes = db_session.query(Movimentacao).count()

    for status_encomenda in StatusEncomenda:
        db_session.add(Movimentacao(encomenda_id=encomenda.id, status=status_encomenda))
    db_session.commit()

    assert db_session.query(Movimentacao).count() == ja_existentes + len(StatusEncomenda)


def test_movimentacao_rejeita_status_invalido(db_session, criar_encomenda_no_banco):
    encomenda = criar_encomenda_no_banco()

    db_session.add(Movimentacao(encomenda_id=encomenda.id, status="inexistente"))

    with pytest.raises((StatementError, LookupError)):
        db_session.commit()


# ---------- T6.2: movimentacao automatica ----------


def _historico(db_session, encomenda_id):
    return (
        db_session.query(Movimentacao)
        .filter(Movimentacao.encomenda_id == encomenda_id)
        .order_by(Movimentacao.id)
        .all()
    )


def _criar_viagem_com_encomendas(
    client, headers, criar_encomenda_no_banco, status_das_encomendas, associar_a_viagem, rota_com_paradas
):
    embarcacao_id = client.post(
        "/embarcacoes", json={"nome": "Rio Negro I", "capacidade": 120}, headers=headers
    ).json()["id"]
    viagem_id = client.post(
        "/viagens",
        json={
            "embarcacao_id": embarcacao_id,
            "rota_id": rota_com_paradas.rota.id,
            "data_saida": "2026-12-01T08:00:00",
        },
        headers=headers,
    ).json()["id"]
    encomendas = []
    for status_encomenda in status_das_encomendas:
        encomenda = criar_encomenda_no_banco(status_encomenda)
        associar_a_viagem(headers, viagem_id, encomenda)
        encomendas.append(encomenda)

    return viagem_id, encomendas


def test_cadastro_de_encomenda_registra_movimentacao_pendente(
    client, db_session, headers_cliente, rota_com_paradas
):
    destinatario = client.post(
        "/destinatarios",
        json={
            "nome": "Joao Pereira",
            "cpf": "22233344405",
            "telefone": "92988887777",
            "endereco": "Rua das Flores, 123",
            "municipio": "Tefe",
        },
        headers=headers_cliente,
    ).json()

    resposta = client.post(
        "/encomendas",
        json={
            "destinatario_id": destinatario["id"],
            "parada_destino_id": rota_com_paradas.destino.id,
            "descricao": "Caixa",
        },
        headers=headers_cliente,
    )

    assert resposta.status_code == 201
    historico = _historico(db_session, resposta.json()["id"])
    assert [m.status for m in historico] == [StatusEncomenda.PENDENTE]
    assert historico[0].viagem_id is None
    assert historico[0].parada_id is None


def test_patch_de_status_registra_movimentacao(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco()

    for novo in ["recebida", "aguardando_embarque"]:
        resposta = client.patch(
            f"/encomendas/{encomenda.id}/status", json={"status": novo}, headers=headers_administrador
        )
        assert resposta.status_code == 200

    assert [m.status.value for m in _historico(db_session, encomenda.id)] == [
        "pendente",
        "recebida",
        "aguardando_embarque",
    ]


def test_patch_com_o_mesmo_status_nao_registra_movimentacao(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco()

    resposta = client.patch(
        f"/encomendas/{encomenda.id}/status", json={"status": "pendente"}, headers=headers_administrador
    )

    assert resposta.status_code == 200
    assert len(_historico(db_session, encomenda.id)) == 1


def test_patch_de_status_invalido_nao_registra_movimentacao(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco()

    resposta = client.patch(
        f"/encomendas/{encomenda.id}/status", json={"status": "voando"}, headers=headers_administrador
    )

    assert resposta.status_code == 422
    assert len(_historico(db_session, encomenda.id)) == 1


def test_cancelar_viagem_registra_movimentacao_imprevisto_com_viagem(
    client, db_session, headers_administrador, criar_encomenda_no_banco,
    associar_a_viagem, rota_com_paradas
):
    viagem_id, (a, b) = _criar_viagem_com_encomendas(
        client,
        headers_administrador,
        criar_encomenda_no_banco,
        [StatusEncomenda.EMBARCADA, StatusEncomenda.EM_TRANSITO],
        associar_a_viagem,
        rota_com_paradas,
    )

    resposta = client.patch(
        f"/viagens/{viagem_id}/status", json={"status": "cancelada"}, headers=headers_administrador
    )

    assert resposta.status_code == 200
    for encomenda, status_anterior in [(a, "embarcada"), (b, "em_transito")]:
        historico = _historico(db_session, encomenda.id)
        assert [m.status.value for m in historico] == [status_anterior, "imprevisto"]
        assert historico[-1].viagem_id == viagem_id


def test_cancelar_viagem_nao_registra_movimentacao_para_entregue_nem_imprevisto(
    client, db_session, headers_administrador, criar_encomenda_no_banco,
    associar_a_viagem, rota_com_paradas
):
    viagem_id, (entregue, ja_imprevisto) = _criar_viagem_com_encomendas(
        client,
        headers_administrador,
        criar_encomenda_no_banco,
        [StatusEncomenda.ENTREGUE, StatusEncomenda.IMPREVISTO],
        associar_a_viagem,
        rota_com_paradas,
    )

    client.patch(
        f"/viagens/{viagem_id}/status", json={"status": "cancelada"}, headers=headers_administrador
    )

    assert len(_historico(db_session, entregue.id)) == 1
    assert len(_historico(db_session, ja_imprevisto.id)) == 1


def test_cancelamento_grava_viagem_encomendas_e_movimentacoes_em_um_unico_commit(
    client, db_session, headers_administrador, criar_encomenda_no_banco,
    associar_a_viagem, rota_com_paradas
):
    viagem_id, encomendas = _criar_viagem_com_encomendas(
        client,
        headers_administrador,
        criar_encomenda_no_banco,
        [StatusEncomenda.RECEBIDA] * 3,
        associar_a_viagem,
        rota_com_paradas,
    )
    commits = []
    event.listen(db_session, "after_commit", lambda sessao: commits.append(1))

    client.patch(
        f"/viagens/{viagem_id}/status", json={"status": "cancelada"}, headers=headers_administrador
    )

    assert len(commits) == 1


def test_falha_ao_registrar_movimentacao_desfaz_o_cancelamento(
    client, db_session, headers_administrador, criar_encomenda_no_banco, monkeypatch,
    associar_a_viagem, rota_com_paradas
):
    viagem_id, encomendas = _criar_viagem_com_encomendas(
        client,
        headers_administrador,
        criar_encomenda_no_banco,
        [StatusEncomenda.RECEBIDA] * 2,
        associar_a_viagem,
        rota_com_paradas,
    )
    chamadas = []

    def registrar_que_falha_na_segunda(*args, **kwargs):
        chamadas.append(1)
        if len(chamadas) == 2:
            raise RuntimeError("falha simulada")
        return Movimentacao(encomenda_id=args[1], status=args[2])

    monkeypatch.setattr(
        "app.services.encomenda.registrar_movimentacao", registrar_que_falha_na_segunda
    )
    viagem = db_session.get(Viagem, viagem_id)

    with pytest.raises(RuntimeError):
        atualizar_status_viagem(db_session, viagem, StatusViagem.CANCELADA)
    db_session.rollback()

    db_session.expire_all()
    assert db_session.get(Viagem, viagem_id).status == StatusViagem.PROGRAMADA
    assert [db_session.get(Encomenda, e.id).status for e in encomendas] == [
        StatusEncomenda.RECEBIDA
    ] * 2
    assert all(len(_historico(db_session, e.id)) == 1 for e in encomendas)
