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


def _encomendas_para_destino(db_session, cliente_id, destinatario_id, destino, n, rota_nome=None):
    """n encomendas cujo destino real e uma parada nova chamada `destino`.

    O municipio do destinatario e o `Tefe` da fixture e nao precisa coincidir
    com o destino: e justamente isso que o dashboard nao deve usar.
    """
    from app.models.encomenda import Encomenda
    from app.models.parada import Parada
    from app.models.rota import Rota

    rota = Rota(nome=rota_nome or f"Manaus - {destino}")
    db_session.add(rota)
    db_session.flush()
    parada = Parada(rota_id=rota.id, nome=destino, ordem=2)
    db_session.add(parada)
    db_session.flush()

    for i in range(n):
        db_session.add(
            Encomenda(
                cliente_id=cliente_id,
                destinatario_id=destinatario_id,
                parada_destino_id=parada.id,
                codigo_rastreio=f"FLU-{destino[:3].upper()}-{rota.id}-{i:03d}",
                descricao="Caixa",
            )
        )
    db_session.commit()


def _encomendas_sem_destino(db_session, cliente_id, destinatario_id, n):
    from app.models.encomenda import Encomenda

    for i in range(n):
        db_session.add(
            Encomenda(
                cliente_id=cliente_id,
                destinatario_id=destinatario_id,
                parada_destino_id=None,
                codigo_rastreio=f"FLU-ANTIGA-{i:03d}",
                descricao="Caixa antiga",
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


def test_municipios_conta_pelo_destino_da_encomenda_e_ordena_do_maior_para_o_menor(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    primeira = criar_encomenda_no_banco()  # destino Tefe (1 encomenda)
    cliente_id, destinatario_id = primeira.cliente_id, primeira.destinatario_id
    _encomendas_para_destino(db_session, cliente_id, destinatario_id, "Parintins", 3)
    _encomendas_para_destino(db_session, cliente_id, destinatario_id, "Coari", 2)

    corpo = client.get("/dashboard/municipios", headers=headers_empresa).json()

    assert corpo["total"] == 6
    assert corpo["municipios"] == [
        {"municipio": "Parintins", "total": 3},
        {"municipio": "Coari", "total": 2},
        {"municipio": "Tefe", "total": 1},
    ]


def test_municipios_ignora_o_municipio_do_destinatario(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    """Destinatario de Tefe com encomenda cujo destino e Coari conta em Coari."""
    base = criar_encomenda_no_banco()
    _encomendas_para_destino(db_session, base.cliente_id, base.destinatario_id, "Coari", 2)

    municipios = {
        m["municipio"]: m["total"]
        for m in client.get("/dashboard/municipios", headers=headers_empresa).json()["municipios"]
    }

    assert municipios == {"Tefe": 1, "Coari": 2}
    assert db_session.get(type(base.destinatario), base.destinatario_id).municipio == "Tefe"


def test_municipios_agrupa_paradas_de_rotas_diferentes_com_o_mesmo_nome(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    base = criar_encomenda_no_banco()  # Tefe (1)
    _encomendas_para_destino(
        db_session, base.cliente_id, base.destinatario_id, "Tefe", 2, rota_nome="Manaus - Tefe (rapida)"
    )

    corpo = client.get("/dashboard/municipios", headers=headers_empresa).json()

    assert corpo["municipios"] == [{"municipio": "Tefe", "total": 3}]


def test_municipios_agrupa_encomendas_antigas_sem_destino_em_grupo_proprio(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    base = criar_encomenda_no_banco()  # Tefe (1)
    _encomendas_sem_destino(db_session, base.cliente_id, base.destinatario_id, 4)

    corpo = client.get("/dashboard/municipios", headers=headers_empresa).json()

    assert corpo["total"] == 5
    # o grupo sem destino sai por ultimo mesmo sendo o maior
    assert corpo["municipios"] == [
        {"municipio": "Tefe", "total": 1},
        {"municipio": "Sem destino definido", "total": 4},
    ]


def test_municipios_so_com_encomendas_antigas(client, headers_empresa, db_session, criar_encomenda_no_banco):
    base = criar_encomenda_no_banco()
    db_session.query(type(base)).update({"parada_destino_id": None})
    db_session.commit()

    corpo = client.get("/dashboard/municipios", headers=headers_empresa).json()

    assert corpo == {"total": 1, "municipios": [{"municipio": "Sem destino definido", "total": 1}]}


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


def test_envios_ativos_municipio_destino_e_o_destino_real_da_encomenda(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    """Destinatario de Tefe com encomenda cujo destino e Coari aparece como Coari."""
    base = criar_encomenda_no_banco()  # destino Tefe, destinatario de Tefe
    _encomendas_para_destino(db_session, base.cliente_id, base.destinatario_id, "Coari", 1)

    envios = client.get("/dashboard/envios-ativos", headers=headers_empresa).json()["envios"]

    por_codigo = {e["codigo_rastreio"]: e["municipio_destino"] for e in envios}
    assert por_codigo.pop(base.codigo_rastreio) == "Tefe"
    assert list(por_codigo.values()) == ["Coari"]
    assert db_session.get(type(base.destinatario), base.destinatario_id).municipio == "Tefe"


def test_envios_ativos_encomenda_antiga_sem_destino_vira_sem_destino_definido(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    base = criar_encomenda_no_banco()
    _encomendas_sem_destino(db_session, base.cliente_id, base.destinatario_id, 1)

    envios = client.get("/dashboard/envios-ativos", headers=headers_empresa).json()["envios"]

    por_codigo = {e["codigo_rastreio"]: e["municipio_destino"] for e in envios}
    assert por_codigo["FLU-ANTIGA-000"] == "Sem destino definido"
    assert por_codigo[base.codigo_rastreio] == "Tefe"


def test_envios_ativos_e_municipios_usam_o_mesmo_rotulo_para_sem_destino(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    base = criar_encomenda_no_banco()
    _encomendas_sem_destino(db_session, base.cliente_id, base.destinatario_id, 2)

    envios = client.get("/dashboard/envios-ativos", headers=headers_empresa).json()["envios"]
    municipios = client.get("/dashboard/municipios", headers=headers_empresa).json()["municipios"]

    sem_destino_envios = [e for e in envios if e["municipio_destino"] == "Sem destino definido"]
    sem_destino_municipios = [m for m in municipios if m["municipio"] == "Sem destino definido"]
    assert len(sem_destino_envios) == sem_destino_municipios[0]["total"] == 2


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


def _encomenda_na_viagem(db_session, criar_encomenda_no_banco, destino, status, viagem):
    """Encomenda cujo destino e `destino` (parada da rota da viagem), ja associada a viagem."""
    encomenda = criar_encomenda_no_banco(status)
    encomenda.parada_destino_id = destino.id
    db_session.commit()
    _associar(db_session, viagem, encomenda)

    return encomenda


def test_envios_ativos_progresso_e_proxima_parada_seguem_o_destino_da_encomenda(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    """Rota Manaus, Itacoatiara, Parintins; encomenda para Itacoatiara (D-1)."""
    from app.services.viagem import registrar_localizacao

    viagem, paradas = _viagem_com_rota(db_session)
    _encomenda_na_viagem(
        db_session, criar_encomenda_no_banco, paradas[1], StatusEncomenda.EMBARCADA, viagem
    )

    def _envio():
        return client.get("/dashboard/envios-ativos", headers=headers_empresa).json()["envios"][0]

    assert (_envio()["progresso"], _envio()["proxima_parada"]) == (0.0, "Manaus")

    registrar_localizacao(db_session, viagem, paradas[0])
    assert (_envio()["progresso"], _envio()["proxima_parada"]) == (0.5, "Itacoatiara")

    # chegou ao destino da encomenda: 100% e sem proxima parada, mesmo faltando Parintins na rota
    registrar_localizacao(db_session, viagem, paradas[1])
    envio = _envio()
    assert envio["municipio_destino"] == "Itacoatiara"
    assert (envio["progresso"], envio["proxima_parada"]) == (1.0, None)

    # a viagem segue para alem do destino: a encomenda continua concluida, nao "volta"
    registrar_localizacao(db_session, viagem, paradas[2])
    assert (_envio()["progresso"], _envio()["proxima_parada"]) == (1.0, None)


def test_envios_ativos_duas_encomendas_da_mesma_viagem_tem_progresso_proprio(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    from app.services.viagem import registrar_localizacao

    viagem, paradas = _viagem_com_rota(db_session)
    perto = _encomenda_na_viagem(
        db_session, criar_encomenda_no_banco, paradas[1], StatusEncomenda.EMBARCADA, viagem
    )
    longe = _encomenda_na_viagem(
        db_session, criar_encomenda_no_banco, paradas[2], StatusEncomenda.EMBARCADA, viagem
    )

    registrar_localizacao(db_session, viagem, paradas[0])
    registrar_localizacao(db_session, viagem, paradas[1])

    envios = {
        e["codigo_rastreio"]: e
        for e in client.get("/dashboard/envios-ativos", headers=headers_empresa).json()["envios"]
    }
    assert (envios[perto.codigo_rastreio]["progresso"], envios[perto.codigo_rastreio]["proxima_parada"]) == (1.0, None)
    assert (envios[longe.codigo_rastreio]["progresso"], envios[longe.codigo_rastreio]["proxima_parada"]) == (
        0.6667,
        "Parintins",
    )


def test_envios_ativos_status_chegou_ao_destino_conta_como_chegada(
    client, headers_empresa, db_session, criar_encomenda_no_banco
):
    viagem, paradas = _viagem_com_rota(db_session)
    _encomenda_na_viagem(
        db_session, criar_encomenda_no_banco, paradas[2], StatusEncomenda.A_RETIRAR, viagem
    )

    envio = client.get("/dashboard/envios-ativos", headers=headers_empresa).json()["envios"][0]

    assert (envio["progresso"], envio["proxima_parada"]) == (1.0, None)


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
