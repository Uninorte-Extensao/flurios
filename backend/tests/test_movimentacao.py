from datetime import datetime

import pytest
from sqlalchemy.exc import StatementError

from app.models.embarcacao import Embarcacao
from app.models.encomenda import StatusEncomenda
from app.models.movimentacao import Movimentacao
from app.models.parada import Parada
from app.models.rota import Rota
from app.models.viagem import Viagem


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

    for status_encomenda in StatusEncomenda:
        db_session.add(Movimentacao(encomenda_id=encomenda.id, status=status_encomenda))
    db_session.commit()

    assert db_session.query(Movimentacao).count() == len(StatusEncomenda)


def test_movimentacao_rejeita_status_invalido(db_session, criar_encomenda_no_banco):
    encomenda = criar_encomenda_no_banco()

    db_session.add(Movimentacao(encomenda_id=encomenda.id, status="inexistente"))

    with pytest.raises((StatementError, LookupError)):
        db_session.commit()
