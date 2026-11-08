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


@pytest.mark.parametrize("senha", ["", "1", "12345"])
def test_cadastrar_usuario_com_senha_curta_retorna_422_e_nao_cria_usuario(client, db_session, senha):
    from app.models.usuario import Usuario

    response = client.post(
        "/usuarios",
        json={"nome": "Maria", "email": "maria@teste.com", "senha": senha},
    )

    assert response.status_code == 422
    erro = response.json()["detail"][0]
    assert erro["loc"][-1] == "senha"
    assert "A senha deve ter pelo menos 6 caracteres." in erro["msg"]
    assert db_session.query(Usuario).count() == 0


@pytest.mark.parametrize("senha", ["123456", "1234567", "a" * 100])
def test_cadastrar_usuario_aceita_senha_a_partir_do_minimo(client, senha):
    response = client.post(
        "/usuarios",
        json={"nome": "Maria", "email": "maria@teste.com", "senha": senha},
    )

    assert response.status_code == 201


def test_senha_curta_nao_vai_para_a_resposta_de_erro(client):
    response = client.post(
        "/usuarios",
        json={"nome": "Maria", "email": "maria@teste.com", "senha": "abc12"},
    )

    assert response.status_code == 422
    assert "abc12" not in response.text


def test_login_continua_aceitando_conta_antiga_com_senha_curta(client, db_session):
    """O minimo vale so para novos cadastros: quem ja tem senha curta nao fica sem acesso."""
    from app.models.usuario import Usuario

    db_session.add(
        Usuario(nome="Antiga", email="antiga@teste.com", senha_hash=gerar_hash_senha("abc"))
    )
    db_session.commit()

    response = client.post(
        "/usuarios/login", json={"email": "antiga@teste.com", "senha": "abc"}
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_schema_usuario_create_exige_senha_minima():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        UsuarioCreate(nome="Maria", email="maria@teste.com", senha="12345")

    assert UsuarioCreate(nome="Maria", email="maria@teste.com", senha="123456").senha == "123456"


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


def test_token_formulario_sucesso(client):
    client.post(
        "/usuarios",
        json={"nome": "Maria", "email": "maria@teste.com", "senha": "123456"},
    )

    response = client.post(
        "/usuarios/token",
        data={"username": "maria@teste.com", "password": "123456"},
    )

    assert response.status_code == 200
    corpo = response.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["access_token"]


def test_token_formulario_senha_invalida(client):
    client.post(
        "/usuarios",
        json={"nome": "Maria", "email": "maria@teste.com", "senha": "123456"},
    )

    response = client.post(
        "/usuarios/token",
        data={"username": "maria@teste.com", "password": "errada"},
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


def test_me_sem_token_retorna_401(client):
    response = client.get("/usuarios/me")

    assert response.status_code == 401


def test_me_cliente(client, headers_cliente):
    response = client.get("/usuarios/me", headers=headers_cliente)

    assert response.status_code == 200
    corpo = response.json()
    assert corpo["tipo"] == "cliente"
    assert corpo["perfil"] is None
    assert corpo["nome"] == "Maria"
    assert corpo["email"] == "maria@teste.com"


def test_me_empresa_devolve_perfil(client, headers_empresa):
    response = client.get("/usuarios/me", headers=headers_empresa)

    assert response.status_code == 200
    corpo = response.json()
    assert corpo["tipo"] == "empresa"
    assert corpo["perfil"] == "operador_embarcacao"


def test_me_usuario_sem_cadastro_completo(client, db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Novo", email="novo@teste.com", senha="123456"),
    )
    token = criar_token_acesso({"sub": str(usuario.id)})

    response = client.get("/usuarios/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["tipo"] is None
    assert response.json()["perfil"] is None


def test_me_nao_expoe_dados_sensiveis(client, headers_cliente):
    corpo = client.get("/usuarios/me", headers=headers_cliente).json()

    assert "senha_hash" not in corpo
    assert "senha" not in corpo
    assert "cpf" not in corpo
    assert "11122233396" not in str(corpo)


def test_cors_libera_origem_do_frontend(client):
    response = client.options(
        "/usuarios/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_nao_libera_origem_desconhecida(client):
    response = client.options(
        "/usuarios/login",
        headers={
            "Origin": "http://site-qualquer.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert "access-control-allow-origin" not in response.headers
