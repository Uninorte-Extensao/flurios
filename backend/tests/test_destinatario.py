from app.core.security import criar_token_acesso
from app.schemas.usuario import UsuarioCreate
from app.services.usuario import criar_usuario


def _cadastrar_e_logar(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Maria", email="maria@teste.com", senha="123456"),
    )
    token = criar_token_acesso({"sub": str(usuario.id)})

    return usuario, token


def test_cadastrar_destinatario_sucesso(client, db_session):
    _, token = _cadastrar_e_logar(db_session)

    response = client.post(
        "/destinatarios",
        json={
            "nome": "Joao Pereira",
            "cpf": "11122233344",
            "telefone": "92988887777",
            "endereco": "Rua das Flores, 123",
            "municipio": "Tefe",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["nome"] == "Joao Pereira"
    assert corpo["cpf"] == "11122233344"
    assert corpo["municipio"] == "Tefe"


def test_cadastrar_destinatario_sem_token_retorna_401(client):
    response = client.post(
        "/destinatarios",
        json={
            "nome": "Joao Pereira",
            "cpf": "11122233344",
            "telefone": "92988887777",
            "endereco": "Rua das Flores, 123",
            "municipio": "Tefe",
        },
    )

    assert response.status_code == 401


def test_cadastrar_destinatario_permite_mesmo_cpf_em_mais_de_um_cadastro(client, db_session):
    _, token = _cadastrar_e_logar(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    dados = {
        "nome": "Joao Pereira",
        "cpf": "11122233344",
        "telefone": "92988887777",
        "endereco": "Rua das Flores, 123",
        "municipio": "Tefe",
    }

    primeira = client.post("/destinatarios", json=dados, headers=headers)
    segunda = client.post("/destinatarios", json=dados, headers=headers)

    assert primeira.status_code == 201
    assert segunda.status_code == 201
    assert primeira.json()["id"] != segunda.json()["id"]
