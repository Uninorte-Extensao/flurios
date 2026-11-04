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
