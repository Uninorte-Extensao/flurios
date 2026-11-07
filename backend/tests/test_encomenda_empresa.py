"""T4.8: GET /empresa/encomendas (listagem de encomendas para a empresa)."""

import pytest

from app.models.encomenda import StatusEncomenda
from app.models.parada import Parada
from app.models.viagem import StatusViagem, Viagem

URL = "/empresa/encomendas"
CPF_DESTINATARIO_COMPLETO = "22233344405"
CPF_MASCARADO = "222.***.***-05"


def _criar_viagem_api(client, headers):
    embarcacao = client.post(
        "/embarcacoes", json={"nome": "Rio Negro I", "capacidade": 50}, headers=headers
    ).json()["id"]
    rota_id = client.get("/rotas", headers=headers).json()[0]["id"]
    resposta = client.post(
        "/viagens",
        json={
            "embarcacao_id": embarcacao,
            "rota_id": rota_id,
            "data_saida": "2030-01-01T08:00:00",
        },
        headers=headers,
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


def _associar(client, headers, viagem_id, encomenda):
    resposta = client.post(
        f"/viagens/{viagem_id}/encomendas",
        json={"encomenda_id": encomenda.id},
        headers=headers,
    )
    assert resposta.status_code == 201, resposta.text


def test_listagem_exige_login(client):
    assert client.get(URL).status_code == 401


def test_cliente_nao_acessa_a_listagem_da_empresa(client, headers_cliente):
    assert client.get(URL, headers=headers_cliente).status_code == 403


def test_get_encomendas_do_cliente_continua_separado_da_empresa(
    client, headers_cliente, headers_administrador
):
    assert client.get("/encomendas", headers=headers_cliente).status_code == 200
    assert client.get("/encomendas", headers=headers_administrador).status_code == 403


def test_lista_vazia(client, headers_administrador):
    resposta = client.get(URL, headers=headers_administrador)

    assert resposta.status_code == 200
    assert resposta.json() == {"itens": [], "total": 0, "limite": 20, "deslocamento": 0}


def test_item_traz_os_campos_esperados_com_cpf_mascarado(
    client, headers_administrador, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)

    item = client.get(URL, headers=headers_administrador).json()["itens"][0]

    assert item["id"] == encomenda.id
    assert item["codigo_rastreio"] == encomenda.codigo_rastreio
    assert item["status"] == "recebida"
    assert item["descricao"] == "Caixa de ferramentas"
    assert item["destinatario"] == {"nome": "Joao Pereira", "cpf": CPF_MASCARADO}
    assert item["destino_nome"] == "Tefe"
    assert item["parada_destino_id"] == encomenda.parada_destino_id
    assert item["criado_em"]
    assert item["viagem_ativa"] is None


def test_cpf_completo_nunca_aparece_na_resposta(
    client, headers_administrador, criar_encomenda_no_banco
):
    criar_encomenda_no_banco()

    resposta = client.get(URL, headers=headers_administrador)

    assert CPF_DESTINATARIO_COMPLETO not in resposta.text


def test_lista_da_mais_recente_para_a_mais_antiga(
    client, headers_administrador, criar_encomenda_no_banco
):
    primeira = criar_encomenda_no_banco()
    segunda = criar_encomenda_no_banco()

    ids = [i["id"] for i in client.get(URL, headers=headers_administrador).json()["itens"]]

    assert ids == [segunda.id, primeira.id]


def test_filtra_por_status(client, headers_administrador, criar_encomenda_no_banco):
    recebida = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    criar_encomenda_no_banco(StatusEncomenda.PENDENTE)

    corpo = client.get(
        URL, params={"status": "recebida"}, headers=headers_administrador
    ).json()

    assert [i["id"] for i in corpo["itens"]] == [recebida.id]
    assert corpo["total"] == 1


def test_filtra_por_mais_de_um_status(client, headers_administrador, criar_encomenda_no_banco):
    recebida = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    aguardando = criar_encomenda_no_banco(StatusEncomenda.AGUARDANDO_EMBARQUE)
    criar_encomenda_no_banco(StatusEncomenda.PENDENTE)

    corpo = client.get(
        URL,
        params=[("status", "recebida"), ("status", "aguardando_embarque")],
        headers=headers_administrador,
    ).json()

    assert {i["id"] for i in corpo["itens"]} == {recebida.id, aguardando.id}


def test_status_invalido_retorna_422(client, headers_administrador):
    resposta = client.get(URL, params={"status": "voando"}, headers=headers_administrador)

    assert resposta.status_code == 422


def test_filtra_por_destino(
    client, db_session, headers_administrador, criar_encomenda_no_banco, rota_com_paradas
):
    criar_encomenda_no_banco()
    em_coari = criar_encomenda_no_banco()
    em_coari.parada_destino_id = rota_com_paradas.final.id
    db_session.commit()

    corpo = client.get(
        URL,
        params={"parada_destino_id": rota_com_paradas.final.id},
        headers=headers_administrador,
    ).json()

    assert [i["id"] for i in corpo["itens"]] == [em_coari.id]


def test_filtra_por_rota_do_destino(
    client, db_session, headers_administrador, criar_encomenda_no_banco, rota_com_paradas
):
    na_rota = criar_encomenda_no_banco()
    fora = criar_encomenda_no_banco()
    outra_rota = client.post(
        "/rotas", json={"nome": "Outra"}, headers=headers_administrador
    ).json()
    parada = Parada(rota_id=outra_rota["id"], nome="Parintins", ordem=2)
    db_session.add(parada)
    db_session.commit()
    fora.parada_destino_id = parada.id
    db_session.commit()

    corpo = client.get(
        URL, params={"rota_id": rota_com_paradas.rota.id}, headers=headers_administrador
    ).json()

    assert [i["id"] for i in corpo["itens"]] == [na_rota.id]


def test_sem_viagem_ativa_exclui_encomendas_em_viagem_programada_ou_em_andamento(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    livre = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    em_viagem = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    viagem_id = _criar_viagem_api(client, headers_administrador)
    _associar(client, headers_administrador, viagem_id, em_viagem)

    corpo = client.get(
        URL, params={"sem_viagem_ativa": "true"}, headers=headers_administrador
    ).json()
    assert [i["id"] for i in corpo["itens"]] == [livre.id]

    db_session.get(Viagem, viagem_id).status = StatusViagem.EM_ANDAMENTO
    db_session.commit()
    corpo = client.get(
        URL, params={"sem_viagem_ativa": "true"}, headers=headers_administrador
    ).json()
    assert [i["id"] for i in corpo["itens"]] == [livre.id]


def test_encomenda_de_viagem_encerrada_conta_como_sem_viagem_ativa(
    client, db_session, headers_administrador, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    viagem_id = _criar_viagem_api(client, headers_administrador)
    _associar(client, headers_administrador, viagem_id, encomenda)
    db_session.get(Viagem, viagem_id).status = StatusViagem.CANCELADA
    db_session.commit()

    corpo = client.get(
        URL, params={"sem_viagem_ativa": "true"}, headers=headers_administrador
    ).json()

    assert [i["id"] for i in corpo["itens"]] == [encomenda.id]
    assert corpo["itens"][0]["viagem_ativa"] is None


def test_item_traz_a_viagem_ativa(client, headers_administrador, criar_encomenda_no_banco):
    encomenda = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    viagem_id = _criar_viagem_api(client, headers_administrador)
    _associar(client, headers_administrador, viagem_id, encomenda)

    item = client.get(URL, headers=headers_administrador).json()["itens"][0]

    assert item["viagem_ativa"] == {
        "id": viagem_id,
        "status": "programada",
        "data_saida": "2030-01-01T08:00:00",
    }


def test_busca_por_codigo_parcial_sem_diferenciar_maiusculas(
    client, headers_administrador, criar_encomenda_no_banco
):
    primeira = criar_encomenda_no_banco()
    criar_encomenda_no_banco()

    corpo = client.get(
        URL,
        params={"busca": primeira.codigo_rastreio.lower()},
        headers=headers_administrador,
    ).json()

    assert [i["id"] for i in corpo["itens"]] == [primeira.id]


def test_busca_trata_curingas_como_texto(client, headers_administrador, criar_encomenda_no_banco):
    criar_encomenda_no_banco()

    corpo = client.get(URL, params={"busca": "%"}, headers=headers_administrador).json()

    assert corpo["total"] == 0


def test_filtros_se_combinam(client, headers_administrador, criar_encomenda_no_banco):
    alvo = criar_encomenda_no_banco(StatusEncomenda.RECEBIDA)
    criar_encomenda_no_banco(StatusEncomenda.PENDENTE)

    corpo = client.get(
        URL,
        params={
            "status": "recebida",
            "sem_viagem_ativa": "true",
            "busca": alvo.codigo_rastreio,
        },
        headers=headers_administrador,
    ).json()

    assert [i["id"] for i in corpo["itens"]] == [alvo.id]


def test_paginacao_com_limite_e_deslocamento(
    client, headers_administrador, criar_encomenda_no_banco
):
    ids = [criar_encomenda_no_banco().id for _ in range(5)]
    esperados = list(reversed(ids))

    pagina_1 = client.get(
        URL, params={"limite": 2, "deslocamento": 0}, headers=headers_administrador
    ).json()
    pagina_3 = client.get(
        URL, params={"limite": 2, "deslocamento": 4}, headers=headers_administrador
    ).json()

    assert [i["id"] for i in pagina_1["itens"]] == esperados[:2]
    assert pagina_1["total"] == 5
    assert pagina_1["limite"] == 2
    assert [i["id"] for i in pagina_3["itens"]] == esperados[4:]
    assert pagina_3["deslocamento"] == 4


@pytest.mark.parametrize("params", [{"limite": 0}, {"limite": 101}, {"deslocamento": -1}])
def test_paginacao_invalida_retorna_422(client, headers_administrador, params):
    assert client.get(URL, params=params, headers=headers_administrador).status_code == 422
