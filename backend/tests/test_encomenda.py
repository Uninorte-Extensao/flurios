import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.encomenda import Encomenda, StatusEncomenda
from app.schemas.cliente import ClienteCreate
from app.schemas.destinatario import DestinatarioCreate
from app.schemas.usuario import UsuarioCreate
from app.services.cliente import completar_cadastro_cliente
from app.services.destinatario import criar_destinatario
from app.services.encomenda import gerar_codigo_rastreio_unico
from app.services.usuario import criar_usuario

CPF_CLIENTE = "11122233396"
CPF_DESTINATARIO = "22233344405"


def _cadastrar_cliente_com_destinatario(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Maria", email="maria@teste.com", senha="123456"),
    )
    cliente = completar_cadastro_cliente(
        db_session,
        usuario,
        ClienteCreate(cpf=CPF_CLIENTE, telefone="92999990000"),
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
