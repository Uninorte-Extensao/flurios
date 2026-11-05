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
