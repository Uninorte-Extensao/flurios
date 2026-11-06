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


def _encomenda_para_municipio(db_session, cliente_id, municipio, n):
    from app.models.destinatario import Destinatario
    from app.models.encomenda import Encomenda

    destinatario = Destinatario(
        cliente_id=cliente_id,
        nome=f"Dest {municipio}",
        cpf="22233344405",
        telefone="92988887777",
        endereco="Rua A, 1",
        municipio=municipio,
    )
    db_session.add(destinatario)
    db_session.flush()

    for i in range(n):
        db_session.add(
            Encomenda(
                cliente_id=cliente_id,
                destinatario_id=destinatario.id,
                codigo_rastreio=f"FLU-{municipio[:3].upper()}-{i:04d}",
                descricao="Caixa",
            )
        )
    db_session.commit()


def test_municipios_exige_autenticacao(client):
    assert client.get("/dashboard/municipios").status_code == 401


def test_municipios_nega_acesso_a_cliente(client, headers_cliente):
    assert client.get("/dashboard/municipios", headers=headers_cliente).status_code == 403


def test_municipios_sem_encomendas_retorna_lista_vazia(client, headers_empresa):
    resposta = client.get("/dashboard/municipios", headers=headers_empresa)

    assert resposta.status_code == 200
    assert resposta.json() == {"total": 0, "municipios": []}


def test_municipios_conta_e_ordena_do_maior_para_o_menor(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    primeira = criar_encomenda_no_banco()  # destino Tefe (1 encomenda)
    cliente_id = primeira.cliente_id
    _encomenda_para_municipio(db_session, cliente_id, "Parintins", 3)
    _encomenda_para_municipio(db_session, cliente_id, "Coari", 2)

    corpo = client.get("/dashboard/municipios", headers=headers_empresa).json()

    assert corpo["total"] == 6
    assert corpo["municipios"] == [
        {"municipio": "Parintins", "total": 3},
        {"municipio": "Coari", "total": 2},
        {"municipio": "Tefe", "total": 1},
    ]


def _viagem_com_encomendas(db_session, criar_encomenda_no_banco, status_viagem, capacidade, status_encomendas, nome="Rio Negro I"):
    from datetime import datetime

    from app.models.embarcacao import Embarcacao
    from app.models.rota import Rota
    from app.models.viagem import Viagem
    from app.models.viagem_encomenda import ViagemEncomenda

    embarcacao = Embarcacao(nome=nome, capacidade=capacidade)
    rota = Rota(nome="Manaus - Parintins")
    db_session.add_all([embarcacao, rota])
    db_session.flush()
    viagem = Viagem(
        embarcacao_id=embarcacao.id,
        rota_id=rota.id,
        data_saida=datetime(2026, 12, 1, 8, 0),
        status=status_viagem,
    )
    db_session.add(viagem)
    db_session.flush()

    for status in status_encomendas:
        encomenda = criar_encomenda_no_banco(status)
        db_session.add(ViagemEncomenda(viagem_id=viagem.id, encomenda_id=encomenda.id))
    db_session.commit()

    return viagem


def test_ocupacao_exige_autenticacao(client):
    assert client.get("/dashboard/ocupacao").status_code == 401


def test_ocupacao_nega_acesso_a_cliente(client, headers_cliente):
    assert client.get("/dashboard/ocupacao", headers=headers_cliente).status_code == 403


def test_ocupacao_sem_viagens_em_andamento_retorna_lista_vazia(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    from app.models.viagem import StatusViagem

    resposta = client.get("/dashboard/ocupacao", headers=headers_empresa)

    assert resposta.status_code == 200
    assert resposta.json() == {"total": 0, "viagens": []}

    # viagens que nao estao em andamento tambem ficam de fora
    _viagem_com_encomendas(
        db_session, criar_encomenda_no_banco, StatusViagem.PROGRAMADA, 10,
        [StatusEncomenda.AGUARDANDO_EMBARQUE],
    )
    assert client.get("/dashboard/ocupacao", headers=headers_empresa).json()["total"] == 0


def test_ocupacao_conta_apenas_encomendas_ativas(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    from app.models.viagem import StatusViagem

    viagem = _viagem_com_encomendas(
        db_session, criar_encomenda_no_banco, StatusViagem.EM_ANDAMENTO, 8,
        [
            StatusEncomenda.EMBARCADA,
            StatusEncomenda.EM_TRANSITO,
            StatusEncomenda.EM_TRANSITO,
            StatusEncomenda.ENTREGUE,
            StatusEncomenda.IMPREVISTO,
        ],
    )

    corpo = client.get("/dashboard/ocupacao", headers=headers_empresa).json()

    assert corpo["total"] == 1
    item = corpo["viagens"][0]
    assert item["viagem_id"] == viagem.id
    assert item["embarcacao_nome"] == "Rio Negro I"
    assert item["capacidade"] == 8
    assert item["encomendas_ativas"] == 3
    assert item["ocupacao"] == 0.375


def test_ocupacao_viagem_sem_encomendas_e_zero(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    from app.models.viagem import StatusViagem

    _viagem_com_encomendas(
        db_session, criar_encomenda_no_banco, StatusViagem.EM_ANDAMENTO, 50, []
    )

    item = client.get("/dashboard/ocupacao", headers=headers_empresa).json()["viagens"][0]

    assert item["encomendas_ativas"] == 0
    assert item["ocupacao"] == 0.0


def test_ocupacao_varias_viagens_nao_misturam_contagens(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    from app.models.viagem import StatusViagem

    _viagem_com_encomendas(
        db_session, criar_encomenda_no_banco, StatusViagem.EM_ANDAMENTO, 4,
        [StatusEncomenda.EM_TRANSITO, StatusEncomenda.EM_TRANSITO], nome="Barco A",
    )
    _viagem_com_encomendas(
        db_session, criar_encomenda_no_banco, StatusViagem.EM_ANDAMENTO, 10,
        [StatusEncomenda.EMBARCADA], nome="Barco B",
    )

    corpo = client.get("/dashboard/ocupacao", headers=headers_empresa).json()

    por_nome = {v["embarcacao_nome"]: v for v in corpo["viagens"]}
    assert corpo["total"] == 2
    assert (por_nome["Barco A"]["encomendas_ativas"], por_nome["Barco A"]["ocupacao"]) == (2, 0.5)
    assert (por_nome["Barco B"]["encomendas_ativas"], por_nome["Barco B"]["ocupacao"]) == (1, 0.1)


def _viagem_com_rota(db_session, status_viagem=None, paradas=("Manaus", "Itacoatiara", "Parintins")):
    from datetime import datetime

    from app.models.embarcacao import Embarcacao
    from app.models.parada import Parada
    from app.models.rota import Rota
    from app.models.viagem import StatusViagem, Viagem

    embarcacao = Embarcacao(nome="Rio Negro I", capacidade=10)
    rota = Rota(nome="Manaus - Parintins")
    db_session.add_all([embarcacao, rota])
    db_session.flush()
    lista = [Parada(rota_id=rota.id, nome=n, ordem=i + 1) for i, n in enumerate(paradas)]
    db_session.add_all(lista)
    viagem = Viagem(
        embarcacao_id=embarcacao.id,
        rota_id=rota.id,
        data_saida=datetime(2026, 12, 1, 8, 0),
        status=status_viagem or StatusViagem.EM_ANDAMENTO,
    )
    db_session.add(viagem)
    db_session.commit()

    return viagem, lista


def _associar(db_session, viagem, encomenda):
    from app.models.viagem_encomenda import ViagemEncomenda

    db_session.add(ViagemEncomenda(viagem_id=viagem.id, encomenda_id=encomenda.id))
    db_session.commit()


def test_envios_ativos_exige_autenticacao(client):
    assert client.get("/dashboard/envios-ativos").status_code == 401


def test_envios_ativos_nega_acesso_a_cliente(client, headers_cliente):
    assert client.get("/dashboard/envios-ativos", headers=headers_cliente).status_code == 403


def test_envios_ativos_sem_encomendas_retorna_lista_vazia(client, headers_empresa):
    resposta = client.get("/dashboard/envios-ativos", headers=headers_empresa)

    assert resposta.status_code == 200
    assert resposta.json() == {"total": 0, "envios": []}


def test_envios_ativos_exclui_entregues_e_conta_corretamente(
    client, headers_empresa, criar_encomenda_no_banco
):
    criar_encomenda_no_banco(StatusEncomenda.PENDENTE)
    criar_encomenda_no_banco(StatusEncomenda.IMPREVISTO)
    criar_encomenda_no_banco(StatusEncomenda.A_RETIRAR)
    criar_encomenda_no_banco(StatusEncomenda.ENTREGUE)

    corpo = client.get("/dashboard/envios-ativos", headers=headers_empresa).json()

    assert corpo["total"] == 3
    assert {e["status"] for e in corpo["envios"]} == {"pendente", "imprevisto", "a_retirar"}


def test_envios_ativos_sem_viagem_tem_progresso_zero_e_sem_proxima_parada(
    client, headers_empresa, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco(StatusEncomenda.PENDENTE)

    envio = client.get("/dashboard/envios-ativos", headers=headers_empresa).json()["envios"][0]

    assert envio == {
        "codigo_rastreio": encomenda.codigo_rastreio,
        "destinatario": "Joao Pereira",
        "municipio_destino": "Tefe",
        "proxima_parada": None,
        "status": "pendente",
        "progresso": 0.0,
    }


def test_envios_ativos_calcula_progresso_e_proxima_parada(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    from app.services.viagem import registrar_localizacao

    viagem, paradas = _viagem_com_rota(db_session)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.EMBARCADA)
    _associar(db_session, viagem, encomenda)

    def _envio():
        return client.get("/dashboard/envios-ativos", headers=headers_empresa).json()["envios"][0]

    assert (_envio()["progresso"], _envio()["proxima_parada"]) == (0.0, "Manaus")

    registrar_localizacao(db_session, viagem, paradas[0])
    envio = _envio()
    assert envio["status"] == "em_transito"
    assert envio["progresso"] == 0.3333
    assert envio["proxima_parada"] == "Itacoatiara"

    registrar_localizacao(db_session, viagem, paradas[1])
    registrar_localizacao(db_session, viagem, paradas[2])
    envio = _envio()
    assert envio["progresso"] == 1.0
    assert envio["proxima_parada"] is None


def test_envios_ativos_viagem_cancelada_nao_conta_progresso(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    from app.models.viagem import StatusViagem

    viagem, _ = _viagem_com_rota(db_session, StatusViagem.CANCELADA)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.IMPREVISTO)
    _associar(db_session, viagem, encomenda)

    envio = client.get("/dashboard/envios-ativos", headers=headers_empresa).json()["envios"][0]

    assert envio["status"] == "imprevisto"
    assert envio["progresso"] == 0.0
    assert envio["proxima_parada"] is None


def test_movimentacoes_recentes_exige_autenticacao(client):
    assert client.get("/dashboard/movimentacoes-recentes").status_code == 401


def test_movimentacoes_recentes_nega_acesso_a_cliente(client, headers_cliente):
    resposta = client.get("/dashboard/movimentacoes-recentes", headers=headers_cliente)

    assert resposta.status_code == 403


def test_movimentacoes_recentes_sem_movimentacoes_retorna_lista_vazia(client, headers_empresa):
    resposta = client.get("/dashboard/movimentacoes-recentes", headers=headers_empresa)

    assert resposta.status_code == 200
    assert resposta.json() == {"total": 0, "movimentacoes": []}


def test_movimentacoes_recentes_padrao_10_mais_recentes_primeiro(
    client, headers_empresa, criar_encomenda_no_banco
):
    for _ in range(12):
        criar_encomenda_no_banco()

    corpo = client.get("/dashboard/movimentacoes-recentes", headers=headers_empresa).json()

    assert corpo["total"] == 10
    codigos = [m["codigo_rastreio"] for m in corpo["movimentacoes"]]
    assert codigos[0] == "FLU-TESTE-0012"
    assert codigos[-1] == "FLU-TESTE-0003"
    assert corpo["movimentacoes"][0]["status"] == "pendente"
    assert corpo["movimentacoes"][0]["parada"] is None


def test_movimentacoes_recentes_respeita_o_limite(
    client, headers_empresa, criar_encomenda_no_banco
):
    for _ in range(5):
        criar_encomenda_no_banco()

    corpo = client.get(
        "/dashboard/movimentacoes-recentes?limite=3", headers=headers_empresa
    ).json()
    assert [m["codigo_rastreio"] for m in corpo["movimentacoes"]] == [
        "FLU-TESTE-0005",
        "FLU-TESTE-0004",
        "FLU-TESTE-0003",
    ]

    corpo = client.get(
        "/dashboard/movimentacoes-recentes?limite=50", headers=headers_empresa
    ).json()
    assert corpo["total"] == 5


def test_movimentacoes_recentes_rejeita_limite_invalido(client, headers_empresa):
    for limite in (0, -1, 101, "abc"):
        resposta = client.get(
            f"/dashboard/movimentacoes-recentes?limite={limite}", headers=headers_empresa
        )
        assert resposta.status_code == 422


def test_movimentacoes_recentes_traz_nome_da_parada(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    from app.services.viagem import registrar_localizacao

    viagem, paradas = _viagem_com_rota(db_session)
    encomenda = criar_encomenda_no_banco(StatusEncomenda.EMBARCADA)
    _associar(db_session, viagem, encomenda)
    registrar_localizacao(db_session, viagem, paradas[1])

    primeira = client.get(
        "/dashboard/movimentacoes-recentes", headers=headers_empresa
    ).json()["movimentacoes"][0]

    assert primeira["codigo_rastreio"] == encomenda.codigo_rastreio
    assert primeira["status"] == "em_transito"
    assert primeira["parada"] == "Itacoatiara"
    assert primeira["data"]
