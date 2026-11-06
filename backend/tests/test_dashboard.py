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
