import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.empresa import Empresa, PerfilEmpresa
from app.schemas.usuario import UsuarioCreate
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
