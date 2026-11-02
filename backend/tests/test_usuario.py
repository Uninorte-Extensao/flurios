import jwt
import pytest

from app.core.config import settings
from app.core.deps import usuario_logado
from app.core.security import criar_token_acesso, gerar_hash_senha, verificar_senha
from app.schemas.usuario import UsuarioCreate
from app.services.usuario import criar_usuario


def test_cadastrar_usuario_sucesso(client):
    response = client.post(
        "/usuarios",
        json={"nome": "Maria", "email": "maria@teste.com", "senha": "123456"},
    )

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["nome"] == "Maria"
    assert corpo["email"] == "maria@teste.com"
    assert corpo["ativo"] is True
    assert "senha" not in corpo
    assert "senha_hash" not in corpo


def test_cadastrar_usuario_email_duplicado(client):
    dados = {"nome": "Maria", "email": "maria@teste.com", "senha": "123456"}

    client.post("/usuarios", json=dados)
    response = client.post("/usuarios", json=dados)

    assert response.status_code == 400


def test_login_sucesso(client):
    client.post(
        "/usuarios",
        json={"nome": "Maria", "email": "maria@teste.com", "senha": "123456"},
    )

    response = client.post(
        "/usuarios/login",
        json={"email": "maria@teste.com", "senha": "123456"},
    )

    assert response.status_code == 200
    corpo = response.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["access_token"]


def test_login_senha_invalida(client):
    client.post(
        "/usuarios",
        json={"nome": "Maria", "email": "maria@teste.com", "senha": "123456"},
    )

    response = client.post(
        "/usuarios/login",
        json={"email": "maria@teste.com", "senha": "errada"},
    )

    assert response.status_code == 401


def test_login_email_inexistente(client):
    response = client.post(
        "/usuarios/login",
        json={"email": "naoexiste@teste.com", "senha": "123456"},
    )

    assert response.status_code == 401


def test_gerar_hash_senha_nao_retorna_senha_em_texto_puro():
    hash_gerado = gerar_hash_senha("123456")

    assert hash_gerado != "123456"


def test_verificar_senha_aceita_senha_correta_e_rejeita_incorreta():
    hash_gerado = gerar_hash_senha("123456")

    assert verificar_senha("123456", hash_gerado) is True
    assert verificar_senha("errada", hash_gerado) is False


def test_criar_token_acesso_gera_jwt_decodificavel_com_claims_esperadas():
    token = criar_token_acesso({"sub": "42"})

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert payload["sub"] == "42"
    assert "exp" in payload


def test_usuario_logado_com_token_valido_retorna_usuario(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Maria", email="maria@teste.com", senha="123456"),
    )
    token = criar_token_acesso({"sub": str(usuario.id)})

    resultado = usuario_logado(token=token, db=db_session)

    assert resultado.id == usuario.id
    assert resultado.email == "maria@teste.com"


def test_usuario_logado_com_token_invalido_levanta_401(db_session):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as excinfo:
        usuario_logado(token="token-invalido", db=db_session)

    assert excinfo.value.status_code == 401


def test_usuario_logado_com_usuario_inexistente_levanta_401(db_session):
    from fastapi import HTTPException

    token = criar_token_acesso({"sub": "999"})

    with pytest.raises(HTTPException) as excinfo:
        usuario_logado(token=token, db=db_session)

    assert excinfo.value.status_code == 401
