from app.core.security import criar_token_acesso
from app.models.empresa import PerfilEmpresa
from app.models.encomenda import StatusEncomenda
from app.schemas.cliente import ClienteCreate
from app.schemas.destinatario import DestinatarioCreate
from app.schemas.encomenda import EncomendaCreate
from app.schemas.usuario import UsuarioCreate
from app.services.cliente import completar_cadastro_cliente
from app.services.destinatario import criar_destinatario
from app.services.empresa import completar_cadastro_empresa
from app.services.encomenda import (
    atualizar_status_encomenda,
    buscar_encomenda_por_id,
    criar_encomenda,
)
from app.services.usuario import criar_usuario


def _cadastrar_cliente_com_destinatario(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Maria", email="maria@teste.com", senha="123456"),
    )
    cliente = completar_cadastro_cliente(
        db_session,
        usuario,
        ClienteCreate(cpf="11122233396", telefone="92999990000"),
    )
    destinatario = criar_destinatario(
        db_session,
        cliente.id,
        DestinatarioCreate(
            nome="Joao Pereira",
            cpf="22233344405",
            telefone="92988887777",
            endereco="Rua das Flores, 123",
            municipio="Tefe",
        ),
    )

    return usuario, cliente, destinatario


def test_buscar_encomenda_por_id_retorna_none_para_id_inexistente(db_session):
    assert buscar_encomenda_por_id(db_session, 9999) is None


def test_buscar_encomenda_por_id_retorna_encomenda_existente(db_session):
    _, cliente, destinatario = _cadastrar_cliente_com_destinatario(db_session)
    encomenda = criar_encomenda(
        db_session,
        cliente,
        destinatario,
        EncomendaCreate(destinatario_id=destinatario.id, descricao="Caixa"),
    )

    encontrada = buscar_encomenda_por_id(db_session, encomenda.id)

    assert encontrada is not None
    assert encontrada.id == encomenda.id


def test_atualizar_status_encomenda_persiste_no_banco(db_session):
    _, cliente, destinatario = _cadastrar_cliente_com_destinatario(db_session)
    encomenda = criar_encomenda(
        db_session,
        cliente,
        destinatario,
        EncomendaCreate(destinatario_id=destinatario.id, descricao="Caixa"),
    )

    atualizar_status_encomenda(db_session, encomenda, StatusEncomenda.EMBARCADA)

    recarregada = buscar_encomenda_por_id(db_session, encomenda.id)
    assert recarregada.status == StatusEncomenda.EMBARCADA


def test_fluxo_completo_cadastro_codigo_e_mudanca_de_status(client, db_session):
    usuario_cliente, cliente, destinatario = _cadastrar_cliente_com_destinatario(db_session)
    token_cliente = criar_token_acesso({"sub": str(usuario_cliente.id)})

    usuario_empresa = criar_usuario(
        db_session,
        UsuarioCreate(nome="Operador", email="operador@teste.com", senha="123456"),
    )
    completar_cadastro_empresa(db_session, usuario_empresa, PerfilEmpresa.OPERADOR_EMBARCACAO)
    token_empresa = criar_token_acesso({"sub": str(usuario_empresa.id)})

    # 1. cadastro da encomenda pelo cliente
    resposta_cadastro = client.post(
        "/encomendas",
        json={"destinatario_id": destinatario.id, "descricao": "Caixa de ferramentas"},
        headers={"Authorization": f"Bearer {token_cliente}"},
    )
    assert resposta_cadastro.status_code == 201
    encomenda = resposta_cadastro.json()

    # 2. codigo de rastreio gerado e unico
    codigo_rastreio = encomenda["codigo_rastreio"]
    assert codigo_rastreio
    assert encomenda["status"] == "pendente"

    # 3. cliente consegue buscar a propria encomenda pelo codigo
    resposta_busca = client.get(
        f"/encomendas/{codigo_rastreio}",
        headers={"Authorization": f"Bearer {token_cliente}"},
    )
    assert resposta_busca.status_code == 200

    # 4. empresa avanca o status em etapas, codigo permanece o mesmo
    for novo_status in ["recebida", "aguardando_embarque", "embarcada", "em_transito"]:
        resposta_status = client.patch(
            f"/encomendas/{encomenda['id']}/status",
            json={"status": novo_status},
            headers={"Authorization": f"Bearer {token_empresa}"},
        )
        assert resposta_status.status_code == 200
        corpo = resposta_status.json()
        assert corpo["status"] == novo_status
        assert corpo["codigo_rastreio"] == codigo_rastreio

    # 5. cliente ainda ve a encomenda com o status mais recente
    resposta_final = client.get(
        f"/encomendas/{codigo_rastreio}",
        headers={"Authorization": f"Bearer {token_cliente}"},
    )
    assert resposta_final.status_code == 200
    assert resposta_final.json()["status"] == "em_transito"
