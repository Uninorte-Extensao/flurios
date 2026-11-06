import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.security import criar_token_acesso
from app.models.empresa import PerfilEmpresa
from app.models.encomenda import Encomenda, StatusEncomenda
from app.schemas.cliente import ClienteCreate
from app.schemas.destinatario import DestinatarioCreate
from app.schemas.usuario import UsuarioCreate
from app.services.cliente import completar_cadastro_cliente
from app.services.destinatario import criar_destinatario
from app.services.empresa import completar_cadastro_empresa
from app.services.encomenda import gerar_codigo_rastreio_unico
from app.services.usuario import criar_usuario

CPF_CLIENTE_1 = "11122233396"
CPF_CLIENTE_2 = "33344455508"
CPF_DESTINATARIO = "22233344405"

DADOS_ENCOMENDA = {"descricao": "Caixa de ferramentas"}


def _cadastrar_cliente_com_destinatario(
    db_session, email="maria@teste.com", cpf_cliente=CPF_CLIENTE_1
):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Maria", email=email, senha="123456"),
    )
    cliente = completar_cadastro_cliente(
        db_session,
        usuario,
        ClienteCreate(cpf=cpf_cliente, telefone="92999990000"),
    )
    destinatario = criar_destinatario(
        db_session,
        cliente.id,
        DestinatarioCreate(
            nome="Joao Pereira",
            cpf=CPF_DESTINATARIO,
            telefone="92988887777",
            endereco="Rua das Flores, 123",
            municipio="Tefe",
        ),
    )

    return cliente, destinatario


def _cadastrar_cliente_logado_com_destinatario(db_session, email="maria@teste.com", cpf_cliente=CPF_CLIENTE_1):
    cliente, destinatario = _cadastrar_cliente_com_destinatario(db_session, email, cpf_cliente)
    token = criar_token_acesso({"sub": str(cliente.usuario_id)})

    return cliente, destinatario, token


def _cadastrar_empresa_logada(db_session, email="operador@teste.com", perfil=PerfilEmpresa.OPERADOR_EMBARCACAO):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Operador", email=email, senha="123456"),
    )
    empresa = completar_cadastro_empresa(db_session, usuario, perfil)
    token = criar_token_acesso({"sub": str(usuario.id)})

    return empresa, token


def _criar_encomenda_sem_status(db_session, cliente_id, destinatario_id):
    encomenda = Encomenda(
        cliente_id=cliente_id,
        destinatario_id=destinatario_id,
        codigo_rastreio="FLXSEMSTATUS",
        descricao="Caixa de teste",
    )
    db_session.add(encomenda)
    db_session.commit()

    return encomenda


def _criar_encomenda_direto(db_session, cliente_id, destinatario_id, codigo):
    encomenda = Encomenda(
        cliente_id=cliente_id,
        destinatario_id=destinatario_id,
        codigo_rastreio=codigo,
        descricao="Caixa de teste",
        status="pendente",
    )
    db_session.add(encomenda)
    db_session.commit()

    return encomenda


def test_gerar_codigo_rastreio_unico_ignora_codigo_ja_em_uso(db_session, monkeypatch):
    cliente, destinatario = _cadastrar_cliente_com_destinatario(db_session)

    codigo_existente = "FLX0000000001"
    codigo_livre = "FLX0000000002"
    codigos = iter([codigo_existente, codigo_livre])

    monkeypatch.setattr(
        "app.services.encomenda.gerar_codigo_rastreio",
        lambda: next(codigos),
    )

    _criar_encomenda_direto(db_session, cliente.id, destinatario.id, codigo_existente)

    novo_codigo = gerar_codigo_rastreio_unico(db_session)

    assert novo_codigo == codigo_livre


def test_gerar_codigo_rastreio_unico_levanta_erro_apos_esgotar_tentativas(
    db_session, monkeypatch
):
    cliente, destinatario = _cadastrar_cliente_com_destinatario(db_session)

    codigo_repetido = "FLX0000000003"
    monkeypatch.setattr(
        "app.services.encomenda.gerar_codigo_rastreio",
        lambda: codigo_repetido,
    )

    _criar_encomenda_direto(db_session, cliente.id, destinatario.id, codigo_repetido)

    with pytest.raises(RuntimeError):
        gerar_codigo_rastreio_unico(db_session)


def test_lista_fixa_de_status_segue_ordem_definida():
    assert [status.value for status in StatusEncomenda] == [
        "pendente",
        "recebida",
        "aguardando_embarque",
        "embarcada",
        "em_transito",
        "chegou_ao_destino",
        "a_retirar",
        "entregue",
        "imprevisto",
    ]


def test_encomenda_usa_status_pendente_como_padrao(db_session):
    cliente, destinatario = _cadastrar_cliente_com_destinatario(db_session)

    encomenda = _criar_encomenda_sem_status(db_session, cliente.id, destinatario.id)

    assert encomenda.status == StatusEncomenda.PENDENTE


def test_banco_rejeita_status_fora_da_lista_fixa(db_session):
    cliente, destinatario = _cadastrar_cliente_com_destinatario(db_session)

    with pytest.raises(IntegrityError):
        db_session.execute(
            text(
                "INSERT INTO encomendas "
                "(cliente_id, destinatario_id, codigo_rastreio, descricao, status, criado_em) "
                "VALUES (:cliente_id, :destinatario_id, 'FLXINVALIDO01', 'caixa', "
                "'status_que_nao_existe', '2026-01-01')"
            ),
            {"cliente_id": cliente.id, "destinatario_id": destinatario.id},
        )
        db_session.commit()


def test_cadastrar_encomenda_sucesso(client, db_session, rota_com_paradas):
    cliente, destinatario, token = _cadastrar_cliente_logado_com_destinatario(db_session)
    dados = {**DADOS_ENCOMENDA, "destinatario_id": destinatario.id, "parada_destino_id": rota_com_paradas.destino.id}

    response = client.post(
        "/encomendas",
        json=dados,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["cliente_id"] == cliente.id
    assert corpo["destinatario_id"] == destinatario.id
    assert corpo["descricao"] == DADOS_ENCOMENDA["descricao"]
    assert corpo["status"] == "pendente"
    assert corpo["codigo_rastreio"]
    assert corpo["parada_destino_id"] == rota_com_paradas.destino.id
    assert corpo["destino_nome"] == "Tefe"


def test_cadastrar_encomenda_sem_token_retorna_401(client, db_session, rota_com_paradas):
    _, destinatario = _cadastrar_cliente_com_destinatario(db_session)
    dados = {**DADOS_ENCOMENDA, "destinatario_id": destinatario.id, "parada_destino_id": rota_com_paradas.destino.id}

    response = client.post("/encomendas", json=dados)

    assert response.status_code == 401


def test_cadastrar_encomenda_sem_cadastro_de_cliente_retorna_403(client, db_session, rota_com_paradas):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )
    token = criar_token_acesso({"sub": str(usuario.id)})
    dados = {**DADOS_ENCOMENDA, "destinatario_id": 1, "parada_destino_id": rota_com_paradas.destino.id}

    response = client.post(
        "/encomendas",
        json=dados,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_cadastrar_encomenda_destinatario_inexistente_retorna_404(client, db_session, rota_com_paradas):
    _, _, token = _cadastrar_cliente_logado_com_destinatario(db_session)
    dados = {**DADOS_ENCOMENDA, "destinatario_id": 9999, "parada_destino_id": rota_com_paradas.destino.id}

    response = client.post(
        "/encomendas",
        json=dados,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_cadastrar_encomenda_destinatario_de_outro_cliente_retorna_404(client, db_session, rota_com_paradas):
    _, destinatario_maria, _ = _cadastrar_cliente_logado_com_destinatario(
        db_session, email="maria@teste.com", cpf_cliente=CPF_CLIENTE_1
    )
    _, _, token_joao = _cadastrar_cliente_logado_com_destinatario(
        db_session, email="joao@teste.com", cpf_cliente=CPF_CLIENTE_2
    )
    dados = {**DADOS_ENCOMENDA, "destinatario_id": destinatario_maria.id, "parada_destino_id": rota_com_paradas.destino.id}

    response = client.post(
        "/encomendas",
        json=dados,
        headers={"Authorization": f"Bearer {token_joao}"},
    )

    assert response.status_code == 404


def test_cadastrar_encomenda_gera_codigos_diferentes_para_cada_encomenda(client, db_session, rota_com_paradas):
    _, destinatario, token = _cadastrar_cliente_logado_com_destinatario(db_session)
    dados = {**DADOS_ENCOMENDA, "destinatario_id": destinatario.id, "parada_destino_id": rota_com_paradas.destino.id}
    headers = {"Authorization": f"Bearer {token}"}

    primeira = client.post("/encomendas", json=dados, headers=headers)
    segunda = client.post("/encomendas", json=dados, headers=headers)

    assert primeira.status_code == 201
    assert segunda.status_code == 201
    assert primeira.json()["codigo_rastreio"] != segunda.json()["codigo_rastreio"]


def test_buscar_encomenda_por_codigo_sucesso(client, db_session, rota_com_paradas):
    _, destinatario, token = _cadastrar_cliente_logado_com_destinatario(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    dados = {**DADOS_ENCOMENDA, "destinatario_id": destinatario.id, "parada_destino_id": rota_com_paradas.destino.id}
    criada = client.post("/encomendas", json=dados, headers=headers).json()

    response = client.get(f"/encomendas/{criada['codigo_rastreio']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["codigo_rastreio"] == criada["codigo_rastreio"]


def test_buscar_encomenda_por_codigo_sem_token_retorna_401(client, db_session, rota_com_paradas):
    _, destinatario, token = _cadastrar_cliente_logado_com_destinatario(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    dados = {**DADOS_ENCOMENDA, "destinatario_id": destinatario.id, "parada_destino_id": rota_com_paradas.destino.id}
    criada = client.post("/encomendas", json=dados, headers=headers).json()

    response = client.get(f"/encomendas/{criada['codigo_rastreio']}")

    assert response.status_code == 401


def test_buscar_encomenda_por_codigo_inexistente_retorna_404(client, db_session):
    _, _, token = _cadastrar_cliente_logado_com_destinatario(db_session)

    response = client.get(
        "/encomendas/FLXNAOEXISTE",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_buscar_encomenda_de_outro_cliente_retorna_404(client, db_session, rota_com_paradas):
    _, destinatario_maria, token_maria = _cadastrar_cliente_logado_com_destinatario(
        db_session, email="maria@teste.com", cpf_cliente=CPF_CLIENTE_1
    )
    dados = {**DADOS_ENCOMENDA, "destinatario_id": destinatario_maria.id, "parada_destino_id": rota_com_paradas.destino.id}
    criada = client.post(
        "/encomendas",
        json=dados,
        headers={"Authorization": f"Bearer {token_maria}"},
    ).json()

    _, _, token_joao = _cadastrar_cliente_logado_com_destinatario(
        db_session, email="joao@teste.com", cpf_cliente=CPF_CLIENTE_2
    )

    response = client.get(
        f"/encomendas/{criada['codigo_rastreio']}",
        headers={"Authorization": f"Bearer {token_joao}"},
    )

    assert response.status_code == 404


def test_listar_encomendas_retorna_apenas_as_do_cliente_logado(client, db_session, rota_com_paradas):
    _, destinatario_maria, token_maria = _cadastrar_cliente_logado_com_destinatario(
        db_session, email="maria@teste.com", cpf_cliente=CPF_CLIENTE_1
    )
    headers_maria = {"Authorization": f"Bearer {token_maria}"}
    dados_maria = {**DADOS_ENCOMENDA, "destinatario_id": destinatario_maria.id, "parada_destino_id": rota_com_paradas.destino.id}
    client.post("/encomendas", json=dados_maria, headers=headers_maria)
    client.post("/encomendas", json=dados_maria, headers=headers_maria)

    _, destinatario_joao, token_joao = _cadastrar_cliente_logado_com_destinatario(
        db_session, email="joao@teste.com", cpf_cliente=CPF_CLIENTE_2
    )
    headers_joao = {"Authorization": f"Bearer {token_joao}"}
    dados_joao = {**DADOS_ENCOMENDA, "destinatario_id": destinatario_joao.id, "parada_destino_id": rota_com_paradas.destino.id}
    client.post("/encomendas", json=dados_joao, headers=headers_joao)

    response = client.get("/encomendas", headers=headers_maria)

    assert response.status_code == 200
    corpo = response.json()
    assert len(corpo) == 2
    assert all(encomenda["destinatario_id"] == destinatario_maria.id for encomenda in corpo)


def test_listar_encomendas_sem_encomendas_retorna_lista_vazia(client, db_session):
    _, destinatario, token = _cadastrar_cliente_logado_com_destinatario(db_session)

    response = client.get("/encomendas", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


def test_listar_encomendas_sem_token_retorna_401(client):
    response = client.get("/encomendas")

    assert response.status_code == 401


def test_atualizar_status_encomenda_sucesso(client, db_session, rota_com_paradas):
    _, destinatario, token_cliente = _cadastrar_cliente_logado_com_destinatario(db_session)
    dados = {**DADOS_ENCOMENDA, "destinatario_id": destinatario.id, "parada_destino_id": rota_com_paradas.destino.id}
    criada = client.post(
        "/encomendas", json=dados, headers={"Authorization": f"Bearer {token_cliente}"}
    ).json()

    _, token_empresa = _cadastrar_empresa_logada(db_session)

    response = client.patch(
        f"/encomendas/{criada['id']}/status",
        json={"status": "recebida"},
        headers={"Authorization": f"Bearer {token_empresa}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "recebida"


def test_atualizar_status_encomenda_aceita_qualquer_perfil_de_empresa(client, db_session, rota_com_paradas):
    _, destinatario, token_cliente = _cadastrar_cliente_logado_com_destinatario(db_session)
    dados = {**DADOS_ENCOMENDA, "destinatario_id": destinatario.id, "parada_destino_id": rota_com_paradas.destino.id}
    criada = client.post(
        "/encomendas", json=dados, headers={"Authorization": f"Bearer {token_cliente}"}
    ).json()

    _, token_atendente = _cadastrar_empresa_logada(
        db_session, email="atendente@teste.com", perfil=PerfilEmpresa.ATENDENTE
    )

    response = client.patch(
        f"/encomendas/{criada['id']}/status",
        json={"status": "aguardando_embarque"},
        headers={"Authorization": f"Bearer {token_atendente}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "aguardando_embarque"


def test_atualizar_status_encomenda_sem_token_retorna_401(client, db_session, rota_com_paradas):
    _, destinatario, token_cliente = _cadastrar_cliente_logado_com_destinatario(db_session)
    dados = {**DADOS_ENCOMENDA, "destinatario_id": destinatario.id, "parada_destino_id": rota_com_paradas.destino.id}
    criada = client.post(
        "/encomendas", json=dados, headers={"Authorization": f"Bearer {token_cliente}"}
    ).json()

    response = client.patch(
        f"/encomendas/{criada['id']}/status",
        json={"status": "recebida"},
    )

    assert response.status_code == 401


def test_atualizar_status_encomenda_cliente_logado_retorna_403(client, db_session, rota_com_paradas):
    _, destinatario, token_cliente = _cadastrar_cliente_logado_com_destinatario(db_session)
    dados = {**DADOS_ENCOMENDA, "destinatario_id": destinatario.id, "parada_destino_id": rota_com_paradas.destino.id}
    criada = client.post(
        "/encomendas", json=dados, headers={"Authorization": f"Bearer {token_cliente}"}
    ).json()

    response = client.patch(
        f"/encomendas/{criada['id']}/status",
        json={"status": "recebida"},
        headers={"Authorization": f"Bearer {token_cliente}"},
    )

    assert response.status_code == 403


def test_atualizar_status_encomenda_inexistente_retorna_404(client, db_session):
    _, token_empresa = _cadastrar_empresa_logada(db_session)

    response = client.patch(
        "/encomendas/9999/status",
        json={"status": "recebida"},
        headers={"Authorization": f"Bearer {token_empresa}"},
    )

    assert response.status_code == 404


def test_atualizar_status_encomenda_status_fora_da_lista_fixa_retorna_422(client, db_session, rota_com_paradas):
    _, destinatario, token_cliente = _cadastrar_cliente_logado_com_destinatario(db_session)
    dados = {**DADOS_ENCOMENDA, "destinatario_id": destinatario.id, "parada_destino_id": rota_com_paradas.destino.id}
    criada = client.post(
        "/encomendas", json=dados, headers={"Authorization": f"Bearer {token_cliente}"}
    ).json()

    _, token_empresa = _cadastrar_empresa_logada(db_session)

    response = client.patch(
        f"/encomendas/{criada['id']}/status",
        json={"status": "status_que_nao_existe"},
        headers={"Authorization": f"Bearer {token_empresa}"},
    )

    assert response.status_code == 422


def test_cadastrar_encomenda_sem_parada_destino_retorna_422(client, db_session, rota_com_paradas):
    _, destinatario, token = _cadastrar_cliente_logado_com_destinatario(db_session)
    dados = {**DADOS_ENCOMENDA, "destinatario_id": destinatario.id}

    response = client.post(
        "/encomendas", json=dados, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422
    assert db_session.query(Encomenda).count() == 0


def test_cadastrar_encomenda_parada_destino_inexistente_retorna_404(
    client, db_session, rota_com_paradas
):
    _, destinatario, token = _cadastrar_cliente_logado_com_destinatario(db_session)
    dados = {**DADOS_ENCOMENDA, "destinatario_id": destinatario.id, "parada_destino_id": 9999}

    response = client.post(
        "/encomendas", json=dados, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404
    assert db_session.query(Encomenda).count() == 0


def test_cadastrar_encomenda_com_parada_de_origem_como_destino_retorna_422(
    client, db_session, rota_com_paradas
):
    _, destinatario, token = _cadastrar_cliente_logado_com_destinatario(db_session)
    dados = {
        **DADOS_ENCOMENDA,
        "destinatario_id": destinatario.id,
        "parada_destino_id": rota_com_paradas.origem.id,
    }

    response = client.post(
        "/encomendas", json=dados, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422
    assert db_session.query(Encomenda).count() == 0


def test_cadastrar_encomenda_aceita_parada_de_qualquer_rota(client, db_session, rota_com_paradas):
    from app.models.parada import Parada
    from app.models.rota import Rota

    outra_rota = Rota(nome="Manaus - Parintins")
    db_session.add(outra_rota)
    db_session.flush()
    parintins = Parada(rota_id=outra_rota.id, nome="Parintins", ordem=2)
    db_session.add(parintins)
    db_session.commit()

    _, destinatario, token = _cadastrar_cliente_logado_com_destinatario(db_session)
    dados = {
        **DADOS_ENCOMENDA,
        "destinatario_id": destinatario.id,
        "parada_destino_id": parintins.id,
    }

    response = client.post(
        "/encomendas", json=dados, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    assert response.json()["destino_nome"] == "Parintins"


def test_buscar_e_listar_encomenda_devolvem_o_destino(client, db_session, rota_com_paradas):
    _, destinatario, token = _cadastrar_cliente_logado_com_destinatario(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    dados = {
        **DADOS_ENCOMENDA,
        "destinatario_id": destinatario.id,
        "parada_destino_id": rota_com_paradas.final.id,
    }
    criada = client.post("/encomendas", json=dados, headers=headers).json()

    por_codigo = client.get(f"/encomendas/{criada['codigo_rastreio']}", headers=headers).json()
    lista = client.get("/encomendas", headers=headers).json()

    assert por_codigo["destino_nome"] == "Coari"
    assert lista[0]["destino_nome"] == "Coari"


def test_encomenda_antiga_sem_destino_continua_legivel(client, db_session, rota_com_paradas):
    """Dados anteriores a migration (parada_destino_id nulo) nao quebram a leitura."""
    cliente, destinatario, token = _cadastrar_cliente_logado_com_destinatario(db_session)
    db_session.add(
        Encomenda(
            cliente_id=cliente.id,
            destinatario_id=destinatario.id,
            codigo_rastreio="FLXANTIGA001",
            descricao="Caixa antiga",
        )
    )
    db_session.commit()

    response = client.get("/encomendas", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()[0]["parada_destino_id"] is None
    assert response.json()[0]["destino_nome"] is None


def test_migration_parada_destino_em_banco_temporario(tmp_path):
    """Sobe e desce a migration em banco descartavel, nunca no flurios.db."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect

    url = f"sqlite:///{tmp_path / 'migration.db'}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    engine = create_engine(url)

    command.upgrade(config, "7ceac32dc579")
    with engine.begin() as conexao:
        conexao.execute(text("INSERT INTO usuarios (nome, email, senha_hash, ativo, criado_em) "
                             "VALUES ('A', 'a@a.com', 'x', 1, '2026-01-01')"))
        conexao.execute(text("INSERT INTO clientes (usuario_id, cpf, telefone, criado_em) "
                             "VALUES (1, '11122233396', '1', '2026-01-01')"))
        conexao.execute(text("INSERT INTO destinatarios (cliente_id, nome, cpf, telefone, endereco, municipio, criado_em) "
                             "VALUES (1, 'D', '22233344405', '1', 'R', 'Tefe', '2026-01-01')"))
        conexao.execute(text("INSERT INTO encomendas (cliente_id, destinatario_id, codigo_rastreio, descricao, status, criado_em) "
                             "VALUES (1, 1, 'FLXEXISTENTE1', 'caixa', 'pendente', '2026-01-01')"))

    command.upgrade(config, "head")
    colunas = {c["name"]: c for c in inspect(engine).get_columns("encomendas")}
    assert colunas["parada_destino_id"]["nullable"] is True
    with engine.connect() as conexao:
        assert conexao.execute(
            text("SELECT parada_destino_id FROM encomendas WHERE codigo_rastreio = 'FLXEXISTENTE1'")
        ).scalar() is None

    command.downgrade(config, "7ceac32dc579")
    assert "parada_destino_id" not in {c["name"] for c in inspect(engine).get_columns("encomendas")}

    engine.dispose()
