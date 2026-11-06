import pytest

from app.core.security import criar_token_acesso
from app.models.cliente import Cliente
from app.models.encomenda import StatusEncomenda
from app.models.pessoa_autorizada import PessoaAutorizada

CPF_PESSOA = "11122233396"
CPF_PESSOA_MASCARADO = "111.***.***-96"
CPF_DESTINATARIO = "22233344405"  # destinatario criado pela fabrica de encomendas
CPF_DESTINATARIO_MASCARADO = "222.***.***-05"
CPF_OUTRA_PESSOA = "33344455508"


def _headers_do_dono(db_session, encomenda):
    cliente = db_session.get(Cliente, encomenda.cliente_id)
    token = criar_token_acesso({"sub": str(cliente.usuario_id)})

    return {"Authorization": f"Bearer {token}"}


def _url(encomenda):
    return f"/encomendas/{encomenda.id}/pessoa-autorizada"


def _cadastrar(client, headers, encomenda, **corpo):
    corpo.setdefault("nome", "Ana Souza")
    corpo.setdefault("cpf", CPF_PESSOA)
    return client.post(_url(encomenda), json=corpo, headers=headers)


def test_cliente_dono_cadastra_pessoa_autorizada_com_cpf_mascarado(
    client, db_session, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco()
    headers = _headers_do_dono(db_session, encomenda)

    resposta = _cadastrar(client, headers, encomenda)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nome"] == "Ana Souza"
    assert corpo["cpf"] == CPF_PESSOA_MASCARADO
    assert corpo["encomenda_id"] == encomenda.id
    assert CPF_PESSOA not in resposta.text


def test_cpf_fica_completo_no_banco(client, db_session, criar_encomenda_no_banco):
    encomenda = criar_encomenda_no_banco()

    _cadastrar(client, _headers_do_dono(db_session, encomenda), encomenda, cpf="111.222.333-96")

    assert db_session.query(PessoaAutorizada).one().cpf == CPF_PESSOA


def test_destinatario_como_pessoa_autorizada_copia_nome_e_cpf(
    client, db_session, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco()
    headers = _headers_do_dono(db_session, encomenda)

    resposta = client.post(
        _url(encomenda), json={"destinatario_e_a_pessoa": True}, headers=headers
    )

    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "Joao Pereira"
    assert resposta.json()["cpf"] == CPF_DESTINATARIO_MASCARADO
    assert CPF_DESTINATARIO not in resposta.text
    assert db_session.query(PessoaAutorizada).one().cpf == CPF_DESTINATARIO


@pytest.mark.parametrize(
    "corpo",
    [
        {"nome": "Ana Souza"},
        {"cpf": CPF_PESSOA},
        {},
        {"nome": "   ", "cpf": CPF_PESSOA},
        {"destinatario_e_a_pessoa": True, "nome": "Ana Souza"},
        {"destinatario_e_a_pessoa": True, "cpf": CPF_PESSOA},
    ],
)
def test_combinacao_invalida_de_campos_retorna_422(
    client, db_session, criar_encomenda_no_banco, corpo
):
    encomenda = criar_encomenda_no_banco()

    resposta = client.post(
        _url(encomenda), json=corpo, headers=_headers_do_dono(db_session, encomenda)
    )

    assert resposta.status_code == 422
    assert CPF_PESSOA not in resposta.text
    assert db_session.query(PessoaAutorizada).count() == 0


def test_cpf_invalido_retorna_422(client, db_session, criar_encomenda_no_banco):
    encomenda = criar_encomenda_no_banco()

    resposta = _cadastrar(
        client, _headers_do_dono(db_session, encomenda), encomenda, cpf="12345678900"
    )

    assert resposta.status_code == 422
    assert db_session.query(PessoaAutorizada).count() == 0


def test_novo_cadastro_substitui_a_pessoa_anterior(
    client, db_session, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco()
    headers = _headers_do_dono(db_session, encomenda)
    _cadastrar(client, headers, encomenda)

    resposta = _cadastrar(client, headers, encomenda, nome="Carlos Lima", cpf=CPF_OUTRA_PESSOA)

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Carlos Lima"
    assert db_session.query(PessoaAutorizada).count() == 1
    assert db_session.query(PessoaAutorizada).one().cpf == CPF_OUTRA_PESSOA


def test_substituicao_permitida_em_status_anterior_a_retirada(
    client, db_session, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco(StatusEncomenda.EM_TRANSITO)
    headers = _headers_do_dono(db_session, encomenda)
    _cadastrar(client, headers, encomenda)

    assert _cadastrar(client, headers, encomenda, nome="Carlos Lima").status_code == 200


def test_troca_bloqueada_quando_encomenda_esta_a_retirar(
    client, db_session, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco(StatusEncomenda.CHEGOU_AO_DESTINO)
    headers = _headers_do_dono(db_session, encomenda)
    _cadastrar(client, headers, encomenda)
    encomenda.status = StatusEncomenda.A_RETIRAR
    db_session.commit()

    resposta = _cadastrar(client, headers, encomenda, nome="Carlos Lima", cpf=CPF_OUTRA_PESSOA)

    assert resposta.status_code == 409
    atual = db_session.query(PessoaAutorizada).one()
    assert atual.nome == "Ana Souza"
    assert atual.cpf == CPF_PESSOA


def test_primeiro_cadastro_ainda_e_permitido_quando_a_retirar(
    client, db_session, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco(StatusEncomenda.A_RETIRAR)

    resposta = _cadastrar(client, _headers_do_dono(db_session, encomenda), encomenda)

    assert resposta.status_code == 201


def test_cadastro_bloqueado_quando_encomenda_ja_entregue(
    client, db_session, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco(StatusEncomenda.ENTREGUE)

    resposta = _cadastrar(client, _headers_do_dono(db_session, encomenda), encomenda)

    assert resposta.status_code == 409
    assert db_session.query(PessoaAutorizada).count() == 0


def test_outro_cliente_nao_cadastra_na_encomenda_alheia(
    client, db_session, headers_cliente, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco()

    resposta = _cadastrar(client, headers_cliente, encomenda)

    assert resposta.status_code == 404
    assert db_session.query(PessoaAutorizada).count() == 0


def test_empresa_nao_cadastra_pessoa_autorizada(
    client, headers_empresa, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco()

    assert _cadastrar(client, headers_empresa, encomenda).status_code == 403


def test_cadastro_exige_login(client, criar_encomenda_no_banco):
    encomenda = criar_encomenda_no_banco()

    assert _cadastrar(client, {}, encomenda).status_code == 401


def test_encomenda_inexistente_retorna_404(client, headers_cliente):
    resposta = client.post(
        "/encomendas/9999/pessoa-autorizada",
        json={"nome": "Ana Souza", "cpf": CPF_PESSOA},
        headers=headers_cliente,
    )

    assert resposta.status_code == 404


def test_dono_consulta_pessoa_autorizada_com_cpf_mascarado(
    client, db_session, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco()
    headers = _headers_do_dono(db_session, encomenda)
    _cadastrar(client, headers, encomenda)

    resposta = client.get(_url(encomenda), headers=headers)

    assert resposta.status_code == 200
    assert resposta.json()["cpf"] == CPF_PESSOA_MASCARADO
    assert CPF_PESSOA not in resposta.text


def test_empresa_consulta_pessoa_autorizada_com_cpf_mascarado(
    client, db_session, headers_empresa, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco()
    _cadastrar(client, _headers_do_dono(db_session, encomenda), encomenda)

    resposta = client.get(_url(encomenda), headers=headers_empresa)

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Ana Souza"
    assert resposta.json()["cpf"] == CPF_PESSOA_MASCARADO
    assert CPF_PESSOA not in resposta.text


def test_outro_cliente_nao_consulta_pessoa_autorizada_alheia(
    client, db_session, headers_cliente, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco()
    _cadastrar(client, _headers_do_dono(db_session, encomenda), encomenda)

    assert client.get(_url(encomenda), headers=headers_cliente).status_code == 404


def test_consulta_sem_cadastro_retorna_404(
    client, db_session, criar_encomenda_no_banco
):
    encomenda = criar_encomenda_no_banco()

    resposta = client.get(_url(encomenda), headers=_headers_do_dono(db_session, encomenda))

    assert resposta.status_code == 404


def test_schema_de_saida_nunca_devolve_cpf_completo():
    from app.schemas.pessoa_autorizada import PessoaAutorizadaOut

    base = {"id": 1, "encomenda_id": 1, "nome": "Ana", "criado_em": "2026-11-05T10:00:00"}

    assert PessoaAutorizadaOut(**base, cpf=CPF_PESSOA).cpf == CPF_PESSOA_MASCARADO
    assert PessoaAutorizadaOut(**base, cpf=CPF_PESSOA_MASCARADO).cpf == CPF_PESSOA_MASCARADO
    assert PessoaAutorizadaOut(**base, cpf="formato estranho").cpf == "***.***.***-**"
