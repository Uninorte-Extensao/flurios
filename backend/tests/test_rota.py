from app.models.rota import Rota


def test_rota_e_criada_com_data_padrao(db_session):
    rota = Rota(nome="Manaus - Tefe")
    db_session.add(rota)
    db_session.commit()
    db_session.refresh(rota)

    assert rota.id is not None
    assert rota.criado_em is not None
