import logging

import pytest

from app.core.security import criar_token_acesso
from app.models.empresa import Empresa, PerfilEmpresa
from app.models.encomenda import StatusEncomenda
from app.models.movimentacao import Movimentacao
from app.models.pessoa_autorizada import PessoaAutorizada
from app.models.retirada import Retirada
from app.schemas.usuario import UsuarioCreate
from app.services.empresa import completar_cadastro_empresa
from app.services.usuario import criar_usuario

CPF_AUTORIZADO = "11122233396"
CPF_OUTRO = "33344455508"


def _url(encomenda):
    return f"/encomendas/{encomenda.id}/retirada"


def _headers_empresa_com_perfil(db_session, perfil):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome=perfil.value, email=f"{perfil.value}@teste.com", senha="123456"),
    )
    completar_cadastro_empresa(db_session, usuario, perfil)
    token = criar_token_acesso({"sub": str(usuario.id)})

    return {"Authorization": f"Bearer {token}"}


def _encomenda_a_retirar(db_session, criar_encomenda_no_banco, com_pessoa=True):
    encomenda = criar_encomenda_no_banco(StatusEncomenda.A_RETIRAR)

    if com_pessoa:
        db_session.add(
            PessoaAutorizada(encomenda_id=encomenda.id, nome="Ana Souza", cpf=CPF_AUTORIZADO)
        )
        db_session.commit()

    return encomenda


def _retirar(client, headers, encomenda, cpf=CPF_AUTORIZADO, **extra):
    corpo = {"cpf_retirante": cpf, "termo_aceito": True}
    corpo.update(extra)
    return client.post(_url(encomenda), json=corpo, headers=headers)


def _historico(db_session, encomenda):
    return [
        m.status
        for m in db_session.query(Movimentacao)
        .filter(Movimentacao.encomenda_id == encomenda.id)
        .order_by(Movimentacao.id)
        .all()
    ]


def test_retirada_marca_encomenda_como_entregue_e_gera_movimentacao(
    client, db_session, headers_empresa, criar_encomenda_no_banco
):
    encomenda = _encomenda_a_retirar(db_session, criar_encomenda_no_banco)

    resposta = _retirar(client, headers_empresa, encomenda)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["encomenda_id"] == encomenda.id
    assert corpo["termo_aceito"] is True
    assert corpo["status_encomenda"] == "entregue"

    db_session.refresh(encomenda)
    assert encomenda.status == StatusEncomenda.ENTREGUE
    assert _historico(db_session, encomenda) == [
        StatusEncomenda.A_RETIRAR,
        StatusEncomenda.ENTREGUE,
    ]


def test_retirada_guarda_cpf_completo_e_a_empresa_que_registrou(
    client, db_session, headers_empresa, criar_encomenda_no_banco
):
    encomenda = _encomenda_a_retirar(db_session, criar_encomenda_no_banco)

    _retirar(client, headers_empresa, encomenda, cpf="111.222.333-96")

    retirada = db_session.query(Retirada).one()
    assert retirada.cpf_retirante == CPF_AUTORIZADO
    assert retirada.empresa_id == db_session.query(Empresa).one().id
    assert retirada.termo_aceito is True


@pytest.mark.parametrize("perfil", list(PerfilEmpresa))
def test_qualquer_perfil_da_empresa_registra_retirada(
    client, db_session, criar_encomenda_no_banco, perfil
):
    encomenda = _encomenda_a_retirar(db_session, criar_encomenda_no_banco)
    headers = _headers_empresa_com_perfil(db_session, perfil)

    assert _retirar(client, headers, encomenda).status_code == 201


def test_termo_nao_aceito_retorna_422_e_nao_altera_nada(
    client, db_session, headers_empresa, criar_encomenda_no_banco
):
    encomenda = _encomenda_a_retirar(db_session, criar_encomenda_no_banco)

    resposta = _retirar(client, headers_empresa, encomenda, termo_aceito=False)

    assert resposta.status_code == 422
    assert CPF_AUTORIZADO not in resposta.text
    _assert_nada_mudou(db_session, encomenda)


def test_termo_ausente_conta_como_nao_aceito(
    client, db_session, headers_empresa, criar_encomenda_no_banco
):
    encomenda = _encomenda_a_retirar(db_session, criar_encomenda_no_banco)

    resposta = client.post(
        _url(encomenda), json={"cpf_retirante": CPF_AUTORIZADO}, headers=headers_empresa
    )

    assert resposta.status_code == 422
    assert CPF_AUTORIZADO not in resposta.text
    _assert_nada_mudou(db_session, encomenda)


def _assert_nada_mudou(db_session, encomenda):
    db_session.refresh(encomenda)
    assert db_session.query(Retirada).count() == 0
    assert encomenda.status == StatusEncomenda.A_RETIRAR
    assert _historico(db_session, encomenda) == [StatusEncomenda.A_RETIRAR]


@pytest.mark.parametrize(
    "status_inicial",
    [s for s in StatusEncomenda if s != StatusEncomenda.A_RETIRAR],
)
def test_so_permite_retirada_de_encomenda_a_retirar(
    client, db_session, headers_empresa, criar_encomenda_no_banco, status_inicial
):
    encomenda = criar_encomenda_no_banco(status_inicial)
    db_session.add(
        PessoaAutorizada(encomenda_id=encomenda.id, nome="Ana Souza", cpf=CPF_AUTORIZADO)
    )
    db_session.commit()

    resposta = _retirar(client, headers_empresa, encomenda)

    assert resposta.status_code == 409
    db_session.refresh(encomenda)
    assert encomenda.status == status_inicial
    assert db_session.query(Retirada).count() == 0


def test_sem_pessoa_autorizada_a_retirada_e_recusada(
    client, db_session, headers_empresa, criar_encomenda_no_banco
):
    encomenda = _encomenda_a_retirar(db_session, criar_encomenda_no_banco, com_pessoa=False)

    resposta = _retirar(client, headers_empresa, encomenda)

    assert resposta.status_code == 409
    _assert_nada_mudou(db_session, encomenda)


def test_cpf_diferente_da_pessoa_autorizada_retorna_403(
    client, db_session, headers_empresa, criar_encomenda_no_banco
):
    encomenda = _encomenda_a_retirar(db_session, criar_encomenda_no_banco)

    resposta = _retirar(client, headers_empresa, encomenda, cpf=CPF_OUTRO)

    assert resposta.status_code == 403
    assert CPF_OUTRO not in resposta.text
    assert CPF_AUTORIZADO not in resposta.text
    _assert_nada_mudou(db_session, encomenda)


def test_cpf_invalido_retorna_422(
    client, db_session, headers_empresa, criar_encomenda_no_banco
):
    encomenda = _encomenda_a_retirar(db_session, criar_encomenda_no_banco)

    resposta = _retirar(client, headers_empresa, encomenda, cpf="12345678900")

    assert resposta.status_code == 422
    _assert_nada_mudou(db_session, encomenda)


def test_segunda_retirada_da_mesma_encomenda_e_recusada(
    client, db_session, headers_empresa, criar_encomenda_no_banco
):
    encomenda = _encomenda_a_retirar(db_session, criar_encomenda_no_banco)
    _retirar(client, headers_empresa, encomenda)

    resposta = _retirar(client, headers_empresa, encomenda)

    assert resposta.status_code == 409
    assert db_session.query(Retirada).count() == 1
    assert _historico(db_session, encomenda).count(StatusEncomenda.ENTREGUE) == 1


def test_cliente_nao_registra_retirada(
    client, db_session, headers_cliente, criar_encomenda_no_banco
):
    encomenda = _encomenda_a_retirar(db_session, criar_encomenda_no_banco)

    assert _retirar(client, headers_cliente, encomenda).status_code == 403
    _assert_nada_mudou(db_session, encomenda)


def test_retirada_exige_login(client, db_session, criar_encomenda_no_banco):
    encomenda = _encomenda_a_retirar(db_session, criar_encomenda_no_banco)

    assert _retirar(client, {}, encomenda).status_code == 401


def test_encomenda_inexistente_retorna_404(client, headers_empresa):
    resposta = client.post(
        "/encomendas/9999/retirada",
        json={"cpf_retirante": CPF_AUTORIZADO, "termo_aceito": True},
        headers=headers_empresa,
    )

    assert resposta.status_code == 404


def test_cpf_nao_vai_para_o_log(
    client, db_session, headers_empresa, criar_encomenda_no_banco, caplog
):
    encomenda = _encomenda_a_retirar(db_session, criar_encomenda_no_banco)

    with caplog.at_level(logging.DEBUG):
        _retirar(client, headers_empresa, encomenda, cpf=CPF_OUTRO)
        _retirar(client, headers_empresa, encomenda)

    assert CPF_AUTORIZADO not in caplog.text
    assert CPF_OUTRO not in caplog.text
