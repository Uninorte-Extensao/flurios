from app.models.encomenda import StatusEncomenda


def test_resumo_exige_autenticacao(client):
    assert client.get("/dashboard/resumo").status_code == 401


def test_resumo_nega_acesso_a_cliente(client, headers_cliente):
    resposta = client.get("/dashboard/resumo", headers=headers_cliente)

    assert resposta.status_code == 403


def test_resumo_sem_encomendas_retorna_todos_os_status_zerados(client, headers_empresa):
    resposta = client.get("/dashboard/resumo", headers=headers_empresa)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 0
    assert corpo["por_status"] == {s.value: 0 for s in StatusEncomenda}


def test_resumo_conta_encomendas_por_status(
    client, headers_empresa, criar_encomenda_no_banco
):
    criar_encomenda_no_banco(StatusEncomenda.PENDENTE)
    criar_encomenda_no_banco(StatusEncomenda.PENDENTE)
    criar_encomenda_no_banco(StatusEncomenda.EM_TRANSITO)
    criar_encomenda_no_banco(StatusEncomenda.IMPREVISTO)

    resposta = client.get("/dashboard/resumo", headers=headers_empresa)

    corpo = resposta.json()
    assert corpo["total"] == 4
    assert corpo["por_status"]["pendente"] == 2
    assert corpo["por_status"]["em_transito"] == 1
    assert corpo["por_status"]["imprevisto"] == 1
    assert corpo["por_status"]["entregue"] == 0
    assert sum(corpo["por_status"].values()) == corpo["total"]


def _criar_viagens(db_session, *status_viagens):
    from datetime import datetime

    from app.models.embarcacao import Embarcacao
    from app.models.rota import Rota
    from app.models.viagem import Viagem

    embarcacao = Embarcacao(nome="Rio Negro I", capacidade=120)
    rota = Rota(nome="Manaus - Parintins")
    db_session.add_all([embarcacao, rota])
    db_session.commit()

    for status_viagem in status_viagens:
        db_session.add(
            Viagem(
                embarcacao_id=embarcacao.id,
                rota_id=rota.id,
                data_saida=datetime(2026, 12, 1, 8, 0),
                status=status_viagem,
            )
        )
    db_session.commit()


def test_viagens_exige_autenticacao(client):
    assert client.get("/dashboard/viagens").status_code == 401


def test_viagens_nega_acesso_a_cliente(client, headers_cliente):
    assert client.get("/dashboard/viagens", headers=headers_cliente).status_code == 403


def test_viagens_sem_viagens_retorna_zeros(client, headers_empresa):
    from app.models.viagem import StatusViagem

    resposta = client.get("/dashboard/viagens", headers=headers_empresa)

    assert resposta.status_code == 200
    assert resposta.json() == {
        "em_andamento": 0,
        "total": 0,
        "por_status": {s.value: 0 for s in StatusViagem},
    }


def test_viagens_conta_em_andamento_e_por_status(client, headers_empresa, db_session):
    from app.models.viagem import StatusViagem

    _criar_viagens(
        db_session,
        StatusViagem.EM_ANDAMENTO,
        StatusViagem.EM_ANDAMENTO,
        StatusViagem.PROGRAMADA,
        StatusViagem.CONCLUIDA,
        StatusViagem.CANCELADA,
    )

    corpo = client.get("/dashboard/viagens", headers=headers_empresa).json()

    assert corpo["em_andamento"] == 2
    assert corpo["total"] == 5
    assert corpo["por_status"] == {
        "programada": 1,
        "em_andamento": 2,
        "concluida": 1,
        "cancelada": 1,
    }
