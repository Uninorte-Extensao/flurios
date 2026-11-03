import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.deps import empresa_administrador, empresa_logado, usuario_logado
from app.core.security import criar_token_acesso
from app.models.empresa import Empresa, PerfilEmpresa
from app.schemas.cliente import ClienteCreate
from app.schemas.usuario import UsuarioCreate
from app.services.cliente import completar_cadastro_cliente
from app.services.empresa import buscar_empresa_por_usuario, completar_cadastro_empresa
from app.services.usuario import criar_usuario


def test_lista_fixa_de_perfis_empresa():
    assert [perfil.value for perfil in PerfilEmpresa] == [
        "administrador",
        "atendente",
        "operador_embarcacao",
        "funcionario_retirada",
    ]


def test_banco_rejeita_perfil_fora_da_lista_fixa(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Maria", email="maria@teste.com", senha="123456"),
    )

    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                "INSERT INTO empresas (usuario_id, perfil, criado_em) "
                "VALUES (:usuario_id, 'perfil_que_nao_existe', '2026-01-01')"
            ),
            {"usuario_id": usuario.id},
        )
        db_session.commit()


def test_criar_empresa_com_perfil_valido(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Maria", email="maria@teste.com", senha="123456"),
    )

    empresa = Empresa(usuario_id=usuario.id, perfil=PerfilEmpresa.ADMINISTRADOR)
    db_session.add(empresa)
    db_session.commit()

    assert empresa.id is not None
    assert empresa.perfil == PerfilEmpresa.ADMINISTRADOR


def test_completar_cadastro_empresa_sucesso(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )

    empresa = completar_cadastro_empresa(db_session, usuario, PerfilEmpresa.ATENDENTE)

    assert empresa.usuario_id == usuario.id
    assert empresa.perfil == PerfilEmpresa.ATENDENTE
    assert buscar_empresa_por_usuario(db_session, usuario.id).id == empresa.id


def test_completar_cadastro_empresa_duplicado_levanta_erro(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )
    completar_cadastro_empresa(db_session, usuario, PerfilEmpresa.ATENDENTE)

    with pytest.raises(ValueError):
        completar_cadastro_empresa(db_session, usuario, PerfilEmpresa.ADMINISTRADOR)


def test_usuario_que_ja_e_cliente_nao_pode_se_tornar_empresa(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )
    completar_cadastro_cliente(
        db_session, usuario, ClienteCreate(cpf="11122233396", telefone="92999990000")
    )

    with pytest.raises(ValueError):
        completar_cadastro_empresa(db_session, usuario, PerfilEmpresa.ADMINISTRADOR)


def test_usuario_que_ja_e_empresa_nao_pode_se_tornar_cliente(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )
    completar_cadastro_empresa(db_session, usuario, PerfilEmpresa.ADMINISTRADOR)

    with pytest.raises(ValueError):
        completar_cadastro_cliente(
            db_session, usuario, ClienteCreate(cpf="11122233396", telefone="92999990000")
        )


def test_empresa_logado_sem_cadastro_de_empresa_levanta_403(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )
    token = criar_token_acesso({"sub": str(usuario.id)})
    usuario_resolvido = usuario_logado(token=token, db=db_session)

    with pytest.raises(HTTPException) as excinfo:
        empresa_logado(usuario=usuario_resolvido, db=db_session)

    assert excinfo.value.status_code == 403


def test_empresa_logado_com_cadastro_retorna_empresa(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )
    completar_cadastro_empresa(db_session, usuario, PerfilEmpresa.OPERADOR_EMBARCACAO)
    token = criar_token_acesso({"sub": str(usuario.id)})
    usuario_resolvido = usuario_logado(token=token, db=db_session)

    resultado = empresa_logado(usuario=usuario_resolvido, db=db_session)

    assert resultado.usuario_id == usuario.id


def test_empresa_administrador_rejeita_perfil_nao_administrador(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )
    empresa = completar_cadastro_empresa(
        db_session, usuario, PerfilEmpresa.FUNCIONARIO_RETIRADA
    )

    with pytest.raises(HTTPException) as excinfo:
        empresa_administrador(empresa=empresa)

    assert excinfo.value.status_code == 403


def test_empresa_administrador_aceita_perfil_administrador(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )
    empresa = completar_cadastro_empresa(db_session, usuario, PerfilEmpresa.ADMINISTRADOR)

    resultado = empresa_administrador(empresa=empresa)

    assert resultado.id == empresa.id
