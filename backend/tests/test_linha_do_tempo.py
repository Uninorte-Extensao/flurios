"""Linha do tempo (historico) da encomenda, do cadastro a entrega, pela API."""

import json

import pytest

DESTINATARIO = {
    "nome": "Joao Pereira",
    "cpf": "22233344405",
    "telefone": "92988887777",
    "endereco": "Rua das Flores, 123",
    "municipio": "Tefe",
}
CPF_CLIENTE = "11122233396"  # ver headers_cliente em conftest.py


# ---------- helpers ----------


def _criar_encomenda(client, headers_cliente, parada_destino_id, descricao="Caixa de ferramentas"):
    destinatario = client.post("/destinatarios", json=DESTINATARIO, headers=headers_cliente)
    assert destinatario.status_code == 201
    resposta = client.post(
        "/encomendas",
        json={
            "destinatario_id": destinatario.json()["id"],
            "parada_destino_id": parada_destino_id,
            "descricao": descricao,
        },
        headers=headers_cliente,
    )
    assert resposta.status_code == 201
    return resposta.json()


def _status_encomenda(client, headers_empresa, encomenda, novo):
    resposta = client.patch(
        f"/encomendas/{encomenda['id']}/status", json={"status": novo}, headers=headers_empresa
    )
    assert resposta.status_code == 200


def _criar_rota(client, headers, nomes=("Manaus", "Codajas", "Tefe")):
    rota_id = client.post("/rotas", json={"nome": "Manaus - Tefe"}, headers=headers).json()["id"]
    paradas = {}
    for ordem, nome in enumerate(nomes, start=1):
        paradas[nome] = client.post(
            f"/rotas/{rota_id}/paradas", json={"nome": nome, "ordem": ordem}, headers=headers
        ).json()["id"]
    return rota_id, paradas


def _criar_viagem(client, headers, rota_id):
    embarcacao_id = client.post(
        "/embarcacoes", json={"nome": "Rio Negro I", "capacidade": 120}, headers=headers
    ).json()["id"]
    resposta = client.post(
        "/viagens",
        json={"embarcacao_id": embarcacao_id, "rota_id": rota_id, "data_saida": "2026-12-01T08:00:00"},
        headers=headers,
    )
    assert resposta.status_code == 201
    return resposta.json()["id"]


def _status_viagem(client, headers, viagem_id, novo):
    resposta = client.patch(f"/viagens/{viagem_id}/status", json={"status": novo}, headers=headers)
    assert resposta.status_code == 200


def _associar(client, headers, viagem_id, encomenda):
    resposta = client.post(
        f"/viagens/{viagem_id}/encomendas", json={"encomenda_id": encomenda["id"]}, headers=headers
    )
    assert resposta.status_code == 201


def _localizacao(client, headers, viagem_id, parada_id):
    resposta = client.post(
        f"/viagens/{viagem_id}/localizacao", json={"parada_id": parada_id}, headers=headers
    )
    assert resposta.status_code == 201


def _linha_do_tempo(client, headers, encomenda):
    resposta = client.get(f"/encomendas/{encomenda['codigo_rastreio']}/rastreio", headers=headers)
    assert resposta.status_code == 200
    return resposta.json()


def _resumo(corpo):
    """[(status, parada_nome, viagem_id)] na ordem em que o cliente ve."""
    return [(m["status"], m["parada_nome"], m["viagem_id"]) for m in corpo["historico"]]


# ---------- cenarios ----------


def test_encomenda_recem_cadastrada_tem_linha_do_tempo_com_apenas_pendente(
    client, headers_cliente,
    rota_com_paradas
):
    encomenda = _criar_encomenda(client, headers_cliente, rota_com_paradas.destino.id)

    corpo = _linha_do_tempo(client, headers_cliente, encomenda)

    assert corpo["status_atual"] == "pendente"
    assert _resumo(corpo) == [("pendente", None, None)]


def test_linha_do_tempo_completa_do_cadastro_a_entrega(client, headers_cliente, headers_empresa, rota_com_paradas):
    encomenda = _criar_encomenda(client, headers_cliente, rota_com_paradas.destino.id)
    rota_id, paradas = _criar_rota(client, headers_empresa)
    viagem_id = _criar_viagem(client, headers_empresa, rota_id)

    _status_encomenda(client, headers_empresa, encomenda, "recebida")
    _status_encomenda(client, headers_empresa, encomenda, "aguardando_embarque")
    _associar(client, headers_empresa, viagem_id, encomenda)
    _status_encomenda(client, headers_empresa, encomenda, "embarcada")
    _status_viagem(client, headers_empresa, viagem_id, "em_andamento")
    _localizacao(client, headers_empresa, viagem_id, paradas["Manaus"])
    _localizacao(client, headers_empresa, viagem_id, paradas["Codajas"])
    _localizacao(client, headers_empresa, viagem_id, paradas["Tefe"])
    _status_encomenda(client, headers_empresa, encomenda, "chegou_ao_destino")
    _status_encomenda(client, headers_empresa, encomenda, "a_retirar")
    _status_encomenda(client, headers_empresa, encomenda, "entregue")

    corpo = _linha_do_tempo(client, headers_cliente, encomenda)

    assert corpo["status_atual"] == "entregue"
    assert _resumo(corpo) == [
        ("pendente", None, None),
        ("recebida", None, None),
        ("aguardando_embarque", None, None),
        ("embarcada", None, None),
        ("em_transito", "Manaus", viagem_id),
        ("em_transito", "Codajas", viagem_id),
        ("em_transito", "Tefe", viagem_id),
        ("chegou_ao_destino", None, None),
        ("a_retirar", None, None),
        ("entregue", None, None),
    ]


def test_empresa_e_cliente_veem_a_mesma_linha_do_tempo(client, headers_cliente, headers_empresa, rota_com_paradas):
    encomenda = _criar_encomenda(client, headers_cliente, rota_com_paradas.destino.id)
    _status_encomenda(client, headers_empresa, encomenda, "recebida")

    do_cliente = _linha_do_tempo(client, headers_cliente, encomenda)
    da_empresa = _linha_do_tempo(client, headers_empresa, encomenda)

    assert do_cliente == da_empresa


def test_cancelamento_de_viagem_aparece_como_imprevisto_com_a_viagem(
    client, headers_cliente, headers_empresa,
    rota_com_paradas
):
    encomenda = _criar_encomenda(client, headers_cliente, rota_com_paradas.destino.id)
    rota_id, paradas = _criar_rota(client, headers_empresa)
    viagem_id = _criar_viagem(client, headers_empresa, rota_id)
    _status_encomenda(client, headers_empresa, encomenda, "recebida")
    _associar(client, headers_empresa, viagem_id, encomenda)

    _status_viagem(client, headers_empresa, viagem_id, "cancelada")

    corpo = _linha_do_tempo(client, headers_cliente, encomenda)
    assert corpo["status_atual"] == "imprevisto"
    assert _resumo(corpo) == [
        ("pendente", None, None),
        ("recebida", None, None),
        ("imprevisto", None, viagem_id),
    ]


def test_encomenda_realocada_apos_cancelamento_segue_na_nova_viagem(
    client, headers_cliente, headers_empresa,
    rota_com_paradas
):
    encomenda = _criar_encomenda(client, headers_cliente, rota_com_paradas.destino.id)
    rota_id, paradas = _criar_rota(client, headers_empresa)
    viagem_cancelada = _criar_viagem(client, headers_empresa, rota_id)
    nova_viagem = _criar_viagem(client, headers_empresa, rota_id)
    _status_encomenda(client, headers_empresa, encomenda, "embarcada")
    _associar(client, headers_empresa, viagem_cancelada, encomenda)
    _status_viagem(client, headers_empresa, viagem_cancelada, "cancelada")

    _associar(client, headers_empresa, nova_viagem, encomenda)
    _status_encomenda(client, headers_empresa, encomenda, "embarcada")
    _status_viagem(client, headers_empresa, nova_viagem, "em_andamento")
    _localizacao(client, headers_empresa, nova_viagem, paradas["Manaus"])

    corpo = _linha_do_tempo(client, headers_cliente, encomenda)
    assert corpo["status_atual"] == "em_transito"
    assert _resumo(corpo) == [
        ("pendente", None, None),
        ("embarcada", None, None),
        ("imprevisto", None, viagem_cancelada),
        ("embarcada", None, None),
        ("em_transito", "Manaus", nova_viagem),
    ]


def test_localizacao_aparece_na_linha_do_tempo_de_cada_encomenda_a_bordo(
    client, headers_cliente, headers_empresa,
    rota_com_paradas
):
    a_bordo_1 = _criar_encomenda(client, headers_cliente, rota_com_paradas.destino.id, "Caixa 1")
    a_bordo_2 = _criar_encomenda(client, headers_cliente, rota_com_paradas.destino.id, "Caixa 2")
    em_terra = _criar_encomenda(client, headers_cliente, rota_com_paradas.destino.id, "Caixa 3")
    rota_id, paradas = _criar_rota(client, headers_empresa)
    viagem_id = _criar_viagem(client, headers_empresa, rota_id)
    for encomenda in (a_bordo_1, a_bordo_2):
        _status_encomenda(client, headers_empresa, encomenda, "embarcada")
        _associar(client, headers_empresa, viagem_id, encomenda)
    _associar(client, headers_empresa, viagem_id, em_terra)
    _status_viagem(client, headers_empresa, viagem_id, "em_andamento")

    _localizacao(client, headers_empresa, viagem_id, paradas["Codajas"])

    for encomenda in (a_bordo_1, a_bordo_2):
        assert _resumo(_linha_do_tempo(client, headers_cliente, encomenda))[-1] == (
            "em_transito",
            "Codajas",
            viagem_id,
        )
    assert _resumo(_linha_do_tempo(client, headers_cliente, em_terra)) == [("pendente", None, None)]


def test_linhas_do_tempo_de_encomendas_diferentes_nao_se_misturam(
    client, headers_cliente, headers_empresa,
    rota_com_paradas
):
    primeira = _criar_encomenda(client, headers_cliente, rota_com_paradas.destino.id, "Caixa 1")
    segunda = _criar_encomenda(client, headers_cliente, rota_com_paradas.destino.id, "Caixa 2")

    _status_encomenda(client, headers_empresa, primeira, "recebida")

    assert _resumo(_linha_do_tempo(client, headers_cliente, primeira)) == [
        ("pendente", None, None),
        ("recebida", None, None),
    ]
    assert _resumo(_linha_do_tempo(client, headers_cliente, segunda)) == [("pendente", None, None)]


def test_repetir_o_mesmo_status_nao_duplica_item_na_linha_do_tempo(
    client, headers_cliente, headers_empresa,
    rota_com_paradas
):
    encomenda = _criar_encomenda(client, headers_cliente, rota_com_paradas.destino.id)

    _status_encomenda(client, headers_empresa, encomenda, "recebida")
    _status_encomenda(client, headers_empresa, encomenda, "recebida")

    assert _resumo(_linha_do_tempo(client, headers_cliente, encomenda)) == [
        ("pendente", None, None),
        ("recebida", None, None),
    ]


def test_ordem_e_estavel_com_muitas_movimentacoes(client, headers_cliente, headers_empresa, rota_com_paradas):
    encomenda = _criar_encomenda(client, headers_cliente, rota_com_paradas.destino.id)
    sequencia = ["recebida", "aguardando_embarque", "imprevisto"] * 4
    for novo in sequencia:
        _status_encomenda(client, headers_empresa, encomenda, novo)

    corpo = _linha_do_tempo(client, headers_cliente, encomenda)

    assert [m["status"] for m in corpo["historico"]] == ["pendente", *sequencia]
    assert [m["id"] for m in corpo["historico"]] == sorted(m["id"] for m in corpo["historico"])


def test_linha_do_tempo_nao_expoe_dados_pessoais(client, headers_cliente, headers_empresa, rota_com_paradas):
    encomenda = _criar_encomenda(client, headers_cliente, rota_com_paradas.destino.id)
    rota_id, paradas = _criar_rota(client, headers_empresa)
    viagem_id = _criar_viagem(client, headers_empresa, rota_id)
    _status_encomenda(client, headers_empresa, encomenda, "embarcada")
    _associar(client, headers_empresa, viagem_id, encomenda)
    _status_viagem(client, headers_empresa, viagem_id, "em_andamento")
    _localizacao(client, headers_empresa, viagem_id, paradas["Manaus"])

    for headers in (headers_cliente, headers_empresa):
        texto = json.dumps(_linha_do_tempo(client, headers, encomenda))
        for dado_pessoal in (
            DESTINATARIO["cpf"],
            DESTINATARIO["telefone"],
            DESTINATARIO["endereco"],
            DESTINATARIO["nome"],
            CPF_CLIENTE,
            "maria@teste.com",
        ):
            assert dado_pessoal not in texto


@pytest.mark.parametrize("headers_nome", ["headers_cliente", "headers_empresa"])
def test_rastreio_exige_login_mesmo_com_codigo_valido(
    request, client, headers_cliente, headers_nome,
    rota_com_paradas
):
    encomenda = _criar_encomenda(client, headers_cliente, rota_com_paradas.destino.id)

    sem_login = client.get(f"/encomendas/{encomenda['codigo_rastreio']}/rastreio")
    com_login = client.get(
        f"/encomendas/{encomenda['codigo_rastreio']}/rastreio",
        headers=request.getfixturevalue(headers_nome),
    )

    assert sem_login.status_code == 401
    assert com_login.status_code == 200
