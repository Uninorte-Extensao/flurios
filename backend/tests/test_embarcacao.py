from app.models.embarcacao import Embarcacao


def test_embarcacao_e_criada_com_ativa_e_data_padrao(db_session):
    embarcacao = Embarcacao(nome="Rio Negro I", capacidade=120)
    db_session.add(embarcacao)
    db_session.commit()
    db_session.refresh(embarcacao)

    assert embarcacao.id is not None
    assert embarcacao.ativa is True
    assert embarcacao.criado_em is not None


DADOS = {"nome": "Rio Negro I", "capacidade": 120}


def test_crud_completo_de_embarcacao(client, headers_empresa):
    criada = client.post("/embarcacoes", json=DADOS, headers=headers_empresa)
    assert criada.status_code == 201
    embarcacao_id = criada.json()["id"]
    assert criada.json()["ativa"] is True

    lista = client.get("/embarcacoes", headers=headers_empresa)
    assert lista.status_code == 200
    assert [e["id"] for e in lista.json()] == [embarcacao_id]

    detalhe = client.get(f"/embarcacoes/{embarcacao_id}", headers=headers_empresa)
    assert detalhe.status_code == 200
    assert detalhe.json()["nome"] == "Rio Negro I"

    editada = client.patch(
        f"/embarcacoes/{embarcacao_id}",
        json={"capacidade": 150, "ativa": False},
        headers=headers_empresa,
    )
    assert editada.status_code == 200
    assert editada.json()["capacidade"] == 150
    assert editada.json()["ativa"] is False
    assert editada.json()["nome"] == "Rio Negro I"

    removida = client.delete(f"/embarcacoes/{embarcacao_id}", headers=headers_empresa)
    assert removida.status_code == 204
    assert client.get(f"/embarcacoes/{embarcacao_id}", headers=headers_empresa).status_code == 404


def test_embarcacao_inexistente_retorna_404(client, headers_empresa):
    assert client.get("/embarcacoes/999", headers=headers_empresa).status_code == 404
    assert client.patch("/embarcacoes/999", json={"nome": "X"}, headers=headers_empresa).status_code == 404
    assert client.delete("/embarcacoes/999", headers=headers_empresa).status_code == 404


def test_capacidade_invalida_retorna_422(client, headers_empresa):
    resposta = client.post(
        "/embarcacoes", json={"nome": "Barco", "capacidade": 0}, headers=headers_empresa
    )
    assert resposta.status_code == 422


def test_sem_login_retorna_401_em_todos_os_endpoints(client):
    assert client.post("/embarcacoes", json=DADOS).status_code == 401
    assert client.get("/embarcacoes").status_code == 401
    assert client.get("/embarcacoes/1").status_code == 401
    assert client.patch("/embarcacoes/1", json={"nome": "X"}).status_code == 401
    assert client.delete("/embarcacoes/1").status_code == 401


def test_cliente_nao_acessa_embarcacoes(client, headers_cliente):
    assert client.post("/embarcacoes", json=DADOS, headers=headers_cliente).status_code == 403
    assert client.get("/embarcacoes", headers=headers_cliente).status_code == 403
    assert client.get("/embarcacoes/1", headers=headers_cliente).status_code == 403
    assert client.patch("/embarcacoes/1", json={"nome": "X"}, headers=headers_cliente).status_code == 403
    assert client.delete("/embarcacoes/1", headers=headers_cliente).status_code == 403
