from app.models.embarcacao import Embarcacao


def test_embarcacao_e_criada_com_ativa_e_data_padrao(db_session):
    embarcacao = Embarcacao(nome="Rio Negro I", capacidade=120)
    db_session.add(embarcacao)
    db_session.commit()
    db_session.refresh(embarcacao)

    assert embarcacao.id is not None
    assert embarcacao.ativa is True
    assert embarcacao.criado_em is not None
