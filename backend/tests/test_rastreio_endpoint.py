import pytest

from app.core.security import criar_token_acesso
from app.models.encomenda import StatusEncomenda
from app.schemas.cliente import ClienteCreate
from app.schemas.usuario import UsuarioCreate
from app.services.cliente import completar_cadastro_cliente
from app.services.usuario import criar_usuario

DESTINATARIO = {
    "nome": "Joao Pereira",
    "cpf": "22233344405",
    "telefone": "92988887777",
    "endereco": "Rua das Flores, 123",
    "municipio": "Tefe",
}


@pytest.fixture()
def headers_outro_cliente(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Carlos", email="carlos@teste.com", senha="123456"),
    )
    completar_cadastro_cliente(
        db_session, usuario, ClienteCreate(cpf="33344455508", telefone="92999991111")
    )

    return {"Authorization": f"Bearer {criar_token_acesso({'sub': str(usuario.id)})}"}


@pytest.fixture()
def headers_usuario_sem_perfil(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Sem Perfil", email="semperfil@teste.com", senha="123456"),
    )

    return {"Authorization": f"Bearer {criar_token_acesso({'sub': str(usuario.id)})}"}


@pytest.fixture()
def encomenda_do_cliente(client, headers_cliente):
    """Encomenda cadastrada pela API pela cliente Maria (headers_cliente)."""
    destinatario = client.post("/destinatarios", json=DESTINATARIO, headers=headers_cliente).json()
    resposta = client.post(
        "/encomendas",
        json={"destinatario_id": destinatario["id"], "descricao": "Caixa de ferramentas"},
        headers=headers_cliente,
    )
    assert resposta.status_code == 201

    return resposta.json()


def _mudar_status(client, headers_empresa, encomenda_id, novo):
    resposta = client.patch(
        f"/encomendas/{encomenda_id}/status", json={"status": novo}, headers=headers_empresa
    )
    assert resposta.status_code == 200


def test_cliente_ve_o_historico_da_propria_encomenda(
    client, headers_cliente, headers_empresa, encomenda_do_cliente
):
    codigo = encomenda_do_cliente["codigo_rastreio"]
    _mudar_status(client, headers_empresa, encomenda_do_cliente["id"], "recebida")
    _mudar_status(client, headers_empresa, encomenda_do_cliente["id"], "aguardando_embarque")

    resposta = client.get(f"/encomendas/{codigo}/rastreio", headers=headers_cliente)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["codigo_rastreio"] == codigo
    assert corpo["status_atual"] == "aguardando_embarque"
    assert [m["status"] for m in corpo["historico"]] == [
        "pendente",
        "recebida",
        "aguardando_embarque",
    ]


def test_historico_vem_do_mais_antigo_para_o_mais_recente(
    client, headers_cliente, headers_empresa, encomenda_do_cliente
):
    for novo in ["recebida", "aguardando_embarque", "embarcada"]:
        _mudar_status(client, headers_empresa, encomenda_do_cliente["id"], novo)

    corpo = client.get(
        f"/encomendas/{encomenda_do_cliente['codigo_rastreio']}/rastreio", headers=headers_cliente
    ).json()

    datas = [m["criado_em"] for m in corpo["historico"]]
    ids = [m["id"] for m in corpo["historico"]]
    assert datas == sorted(datas)
    assert ids == sorted(ids)


def test_cada_item_do_historico_tem_apenas_os_campos_da_linha_do_tempo(
    client, headers_cliente, encomenda_do_cliente
):
    corpo = client.get(
        f"/encomendas/{encomenda_do_cliente['codigo_rastreio']}/rastreio", headers=headers_cliente
    ).json()

    assert set(corpo) == {"codigo_rastreio", "status_atual", "historico"}
    assert set(corpo["historico"][0]) == {
        "id",
        "status",
        "parada_id",
        "parada_nome",
        "viagem_id",
        "criado_em",
    }
    assert corpo["historico"][0]["parada_id"] is None
    assert corpo["historico"][0]["parada_nome"] is None
    assert corpo["historico"][0]["viagem_id"] is None


def test_empresa_ve_o_historico_de_qualquer_encomenda(
    client, headers_empresa, encomenda_do_cliente
):
    resposta = client.get(
        f"/encomendas/{encomenda_do_cliente['codigo_rastreio']}/rastreio", headers=headers_empresa
    )

    assert resposta.status_code == 200
    assert resposta.json()["status_atual"] == "pendente"


def test_cliente_nao_ve_encomenda_de_outro_cliente(
    client, headers_outro_cliente, encomenda_do_cliente
):
    resposta = client.get(
        f"/encomendas/{encomenda_do_cliente['codigo_rastreio']}/rastreio",
        headers=headers_outro_cliente,
    )

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Encomenda nao encontrada."


def test_codigo_de_outro_cliente_e_codigo_inexistente_respondem_igual(
    client, headers_outro_cliente, encomenda_do_cliente
):
    de_outro = client.get(
        f"/encomendas/{encomenda_do_cliente['codigo_rastreio']}/rastreio",
        headers=headers_outro_cliente,
    )
    inexistente = client.get("/encomendas/FLXNAOEXISTE/rastreio", headers=headers_outro_cliente)

    assert (de_outro.status_code, de_outro.json()) == (inexistente.status_code, inexistente.json())


def test_codigo_inexistente_retorna_404_para_empresa(client, headers_empresa):
    resposta = client.get("/encomendas/FLXNAOEXISTE/rastreio", headers=headers_empresa)

    assert resposta.status_code == 404


def test_rastreio_sem_login_retorna_401(client, encomenda_do_cliente):
    resposta = client.get(f"/encomendas/{encomenda_do_cliente['codigo_rastreio']}/rastreio")

    assert resposta.status_code == 401


def test_usuario_sem_cadastro_de_cliente_ou_empresa_retorna_403(
    client, headers_usuario_sem_perfil, encomenda_do_cliente
):
    resposta = client.get(
        f"/encomendas/{encomenda_do_cliente['codigo_rastreio']}/rastreio",
        headers=headers_usuario_sem_perfil,
    )

    assert resposta.status_code == 403


def test_status_atual_acompanha_a_encomenda(
    client, headers_cliente, headers_empresa, encomenda_do_cliente
):
    _mudar_status(client, headers_empresa, encomenda_do_cliente["id"], "imprevisto")

    corpo = client.get(
        f"/encomendas/{encomenda_do_cliente['codigo_rastreio']}/rastreio", headers=headers_cliente
    ).json()

    assert corpo["status_atual"] == StatusEncomenda.IMPREVISTO.value
    assert corpo["historico"][-1]["status"] == "imprevisto"
