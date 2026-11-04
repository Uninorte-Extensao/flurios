from app.models.parada import Parada
from app.models.rota import Rota


def test_parada_e_vinculada_a_rota_com_ordem(db_session):
    rota = Rota(nome="Manaus - Tefe")
    db_session.add(rota)
    db_session.commit()

    parada = Parada(rota_id=rota.id, nome="Manaus", ordem=1)
    db_session.add(parada)
    db_session.commit()
    db_session.refresh(parada)

    assert parada.id is not None
    assert parada.rota_id == rota.id
    assert parada.ordem == 1


import pytest
from sqlalchemy.exc import IntegrityError

from app.schemas.parada import ParadaCreate, ParadaUpdate
from app.services.parada import atualizar_parada, criar_parada


def _criar_rota(db_session, nome="Manaus - Tefe"):
    rota = Rota(nome=nome)
    db_session.add(rota)
    db_session.commit()
    return rota


def test_criar_parada_com_ordem_repetida_na_mesma_rota_falha(db_session):
    rota = _criar_rota(db_session)
    criar_parada(db_session, rota.id, ParadaCreate(nome="Manaus", ordem=1))

    with pytest.raises(ValueError):
        criar_parada(db_session, rota.id, ParadaCreate(nome="Manacapuru", ordem=1))


def test_mesma_ordem_em_rotas_diferentes_e_permitida(db_session):
    rota_a = _criar_rota(db_session, "Rota A")
    rota_b = _criar_rota(db_session, "Rota B")

    criar_parada(db_session, rota_a.id, ParadaCreate(nome="Manaus", ordem=1))
    parada_b = criar_parada(db_session, rota_b.id, ParadaCreate(nome="Manaus", ordem=1))

    assert parada_b.ordem == 1


def test_atualizar_parada_para_ordem_ocupada_falha(db_session):
    rota = _criar_rota(db_session)
    criar_parada(db_session, rota.id, ParadaCreate(nome="Manaus", ordem=1))
    segunda = criar_parada(db_session, rota.id, ParadaCreate(nome="Manacapuru", ordem=2))

    with pytest.raises(ValueError):
        atualizar_parada(db_session, segunda, ParadaUpdate(ordem=1))


def test_atualizar_parada_mantendo_a_propria_ordem_e_permitido(db_session):
    rota = _criar_rota(db_session)
    parada = criar_parada(db_session, rota.id, ParadaCreate(nome="Manaus", ordem=1))

    atualizada = atualizar_parada(db_session, parada, ParadaUpdate(nome="Manaus Porto", ordem=1))

    assert atualizada.nome == "Manaus Porto"


def test_banco_rejeita_ordem_repetida_na_mesma_rota(db_session):
    rota = _criar_rota(db_session)
    db_session.add(Parada(rota_id=rota.id, nome="A", ordem=1))
    db_session.commit()

    db_session.add(Parada(rota_id=rota.id, nome="B", ordem=1))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
