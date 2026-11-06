"""Auditoria (T7.6): nenhuma resposta da API pode devolver CPF completo.

Duas frentes:
1. Estatica: todo campo de CPF em um response_model de rota precisa usar CpfMascarado.
2. Dinamica: executa o fluxo real e procura qualquer CPF (so digitos ou
   formatado) em TODOS os corpos de resposta, inclusive os de erro.

Os vazamentos encontrados na revisao (docs/relatorio-revisao-cpf-t7-6.md) foram
corrigidos em fix/mascarar-cpf-respostas; estes testes passam a impedir que voltem.
"""
import importlib
import pkgutil
import re
import typing

import pytest
from fastapi.routing import APIRoute
from pydantic import BaseModel

import app.routers as pacote_routers
from app.core.cpf import cpf_e_valido
from app.core.mascaramento import CpfMascarado
from app.core.security import criar_token_acesso
from app.main import app
from app.models.encomenda import StatusEncomenda
from app.schemas.usuario import UsuarioCreate
from app.services.usuario import criar_usuario

CPF_CLIENTE = "52998224725"
CPF_DESTINATARIO = "11144477735"
CPF_AUTORIZADO = "11122233396"
CPF_INVALIDO_ENVIADO = "12345678900"
SENTINELAS = [CPF_CLIENTE, CPF_DESTINATARIO, CPF_AUTORIZADO, CPF_INVALIDO_ENVIADO]

# Formato ddd.ddd.ddd-dd, ou 11 digitos seguidos (so conta se o digito verificador
# bater, para nao confundir com telefone de 11 digitos).
PADRAO_CPF_FORMATADO = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
PADRAO_ONZE_DIGITOS = re.compile(r"(?<!\d)\d{11}(?!\d)")


def _corpo_expoe_cpf(corpo):
    """True se o texto traz um CPF sentinela, um CPF formatado ou 11 digitos que formam CPF valido."""
    if any(sentinela in corpo for sentinela in SENTINELAS):
        return True

    if PADRAO_CPF_FORMATADO.search(corpo):
        return True

    return any(cpf_e_valido(m.group()) for m in PADRAO_ONZE_DIGITOS.finditer(corpo))


def _modelos_aninhados(tipo, vistos):
    """Percorre um tipo (inclusive list[...], X | None) devolvendo os BaseModel dentro dele."""
    if isinstance(tipo, type) and issubclass(tipo, BaseModel):
        if tipo in vistos:
            return
        vistos.add(tipo)
        yield tipo
        for campo in tipo.model_fields.values():
            yield from _modelos_aninhados(campo.annotation, vistos)
        return

    for argumento in typing.get_args(tipo):
        yield from _modelos_aninhados(argumento, vistos)


def _rotas_da_api():
    """Todas as APIRoute, lidas dos modulos de app.routers (app.routes embrulha os
    routers incluidos e nao lista as rotas diretamente)."""
    rotas = []

    for modulo in pkgutil.iter_modules(pacote_routers.__path__):
        roteador = getattr(importlib.import_module(f"app.routers.{modulo.name}"), "router", None)

        if roteador is not None:
            rotas.extend(r for r in roteador.routes if isinstance(r, APIRoute))

    return rotas


def test_enumeracao_de_rotas_cobre_todas_as_operacoes_do_openapi():
    """Evita que a varredura estatica fique cega se o FastAPI mudar a estrutura de rotas."""
    operacoes_openapi = {
        (metodo.upper(), caminho)
        for caminho, operacoes in app.openapi()["paths"].items()
        for metodo in operacoes
    }
    operacoes_lidas = {
        (metodo, rota.path) for rota in _rotas_da_api() for metodo in rota.methods
    }

    # /health e definida direto em main.py, nao em um router
    assert operacoes_openapi - {("GET", "/health")} <= operacoes_lidas
    assert len(operacoes_openapi) > 30


def _campos_de_cpf_sem_mascara():
    achados = set()
    vistos = set()

    for rota in _rotas_da_api():
        if rota.response_model is None:
            continue

        for modelo in _modelos_aninhados(rota.response_model, vistos):
            for nome, campo in modelo.model_fields.items():
                if "cpf" not in nome.lower():
                    continue

                # CpfMascarado = Annotated[str, AfterValidator(...)]: a marca fica em metadata
                mascarado = any(m in typing.get_args(CpfMascarado)[1:] for m in campo.metadata)

                if not mascarado:
                    achados.add(f"{modelo.__name__}.{nome}")

    return achados


def test_todo_campo_de_cpf_em_resposta_usa_cpf_mascarado():
    """Um campo novo de CPF em schema de saida, sem CpfMascarado, quebra este teste."""
    assert _campos_de_cpf_sem_mascara() == set()


class _Gravador:
    """Envolve o TestClient e guarda (metodo, caminho, status, corpo) de cada resposta."""

    def __init__(self, client):
        self._client = client
        self.respostas = []

    def request(self, metodo, caminho, **kwargs):
        resposta = self._client.request(metodo, caminho, **kwargs)
        self.respostas.append((metodo, caminho, resposta.status_code, resposta.text))
        return resposta

    def vazamentos(self):
        achados = set()

        for metodo, caminho, status, corpo in self.respostas:
            caminho_generico = re.sub(r"/\d+", "/{id}", caminho)
            if _corpo_expoe_cpf(corpo):
                achados.add((metodo, caminho_generico, status))

        return achados


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _parada_destino_id(db_session):
    from app.models.parada import Parada

    return db_session.query(Parada).filter(Parada.ordem == 2).order_by(Parada.id).first().id


def _percorrer_fluxo_completo(client, db_session, headers_empresa, criar_encomenda_no_banco):
    api = _Gravador(client)

    # Cliente novo cadastra seu CPF (POST /clientes) e um destinatario
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Cliente Auditoria", email="auditoria@teste.com", senha="123456"),
    )
    headers_novo = _headers(criar_token_acesso({"sub": str(usuario.id)}))
    api.request("POST", "/clientes", json={"cpf": CPF_CLIENTE, "telefone": "92999990000"}, headers=headers_novo)
    api.request("POST", "/clientes", json={"cpf": CPF_CLIENTE, "telefone": "92999990000"}, headers=headers_novo)

    dados_dest = {
        "nome": "Joao",
        "cpf": CPF_DESTINATARIO,
        "telefone": "92988887777",
        "endereco": "Rua A, 1",
        "municipio": "Tefe",
    }
    criado = api.request("POST", "/destinatarios", json=dados_dest, headers=headers_novo)
    destinatario_id = criado.json()["id"]
    api.request("GET", f"/destinatarios/{destinatario_id}", headers=headers_novo)
    api.request("GET", "/destinatarios", headers=headers_novo)
    api.request("GET", "/rotas/destinos", headers=headers_novo)
    api.request("POST", "/destinatarios", json={**dados_dest, "cpf": CPF_INVALIDO_ENVIADO}, headers=headers_novo)

    # Encomenda, pessoa autorizada e retirada
    encomenda_resp = api.request(
        "POST",
        "/encomendas",
        json={
            "destinatario_id": destinatario_id,
            "parada_destino_id": _parada_destino_id(db_session),
            "descricao": "Caixa",
        },
        headers=headers_novo,
    )
    encomenda_id = encomenda_resp.json()["id"]
    codigo = encomenda_resp.json()["codigo_rastreio"]
    api.request("GET", "/encomendas", headers=headers_novo)
    api.request("GET", f"/encomendas/{codigo}", headers=headers_novo)
    api.request("GET", f"/encomendas/{codigo}/rastreio", headers=headers_novo)
    api.request("GET", f"/encomendas/{codigo}/rastreio", headers=headers_empresa)

    corpo_pessoa = {"nome": "Ana", "cpf": CPF_AUTORIZADO}
    api.request("POST", f"/encomendas/{encomenda_id}/pessoa-autorizada", json=corpo_pessoa, headers=headers_novo)
    api.request("POST", f"/encomendas/{encomenda_id}/pessoa-autorizada", json={**corpo_pessoa, "cpf": CPF_INVALIDO_ENVIADO}, headers=headers_novo)
    api.request("POST", f"/encomendas/{encomenda_id}/pessoa-autorizada", json={"destinatario_e_a_pessoa": True, "cpf": CPF_AUTORIZADO}, headers=headers_novo)
    api.request("GET", f"/encomendas/{encomenda_id}/pessoa-autorizada", headers=headers_novo)
    api.request("GET", f"/encomendas/{encomenda_id}/pessoa-autorizada", headers=headers_empresa)

    api.request("PATCH", f"/encomendas/{encomenda_id}/status", json={"status": StatusEncomenda.A_RETIRAR.value}, headers=headers_empresa)
    retirar = f"/encomendas/{encomenda_id}/retirada"
    api.request("POST", retirar, json={"cpf_retirante": CPF_CLIENTE, "termo_aceito": True}, headers=headers_empresa)
    api.request("POST", retirar, json={"cpf_retirante": CPF_INVALIDO_ENVIADO, "termo_aceito": True}, headers=headers_empresa)
    api.request("POST", retirar, json={"cpf_retirante": CPF_AUTORIZADO, "termo_aceito": False}, headers=headers_empresa)
    api.request("POST", retirar, json={"cpf_retirante": CPF_AUTORIZADO, "termo_aceito": True}, headers=headers_empresa)
    api.request("POST", retirar, json={"cpf_retirante": CPF_AUTORIZADO, "termo_aceito": True}, headers=headers_empresa)

    # Demais modulos (nao devem tocar em CPF, mas a varredura confirma)
    for caminho in ("/embarcacoes", "/rotas", "/viagens"):
        api.request("GET", caminho, headers=headers_empresa)

    return api


def test_fluxo_completo_foi_exercitado(client, db_session, headers_empresa, criar_encomenda_no_banco):
    """Garante que a varredura dinamica realmente passou pelos endpoints sensiveis."""
    api = _percorrer_fluxo_completo(client, db_session, headers_empresa, criar_encomenda_no_banco)
    chamados = {(m, re.sub(r"/\d+", "/{id}", c), s) for m, c, s, _ in api.respostas}

    assert ("POST", "/clientes", 201) in chamados
    assert ("POST", "/destinatarios", 201) in chamados
    assert ("GET", "/destinatarios/{id}", 200) in chamados
    assert ("GET", "/destinatarios", 200) in chamados
    assert ("POST", "/encomendas/{id}/pessoa-autorizada", 201) in chamados
    assert ("GET", "/encomendas/{id}/pessoa-autorizada", 200) in chamados
    assert ("POST", "/encomendas/{id}/retirada", 201) in chamados
    assert ("POST", "/encomendas/{id}/retirada", 403) in chamados
    assert ("POST", "/encomendas/{id}/retirada", 422) in chamados


def test_nenhuma_resposta_da_api_devolve_cpf(
    client, db_session, headers_empresa, criar_encomenda_no_banco
):
    """Nenhuma resposta (sucesso ou erro) traz CPF completo, formatado ou digitado de volta."""
    api = _percorrer_fluxo_completo(client, db_session, headers_empresa, criar_encomenda_no_banco)

    assert api.vazamentos() == set()


def test_detector_dinamico_reconhece_cpf_exposto():
    """Sanidade do proprio detector: ele precisa acusar CPF em qualquer formato."""
    assert _corpo_expoe_cpf('{"cpf": "52998224725"}')
    assert _corpo_expoe_cpf('{"cpf": "529.982.247-25"}')
    assert _corpo_expoe_cpf('{"input": "12345678900"}')
    assert not _corpo_expoe_cpf('{"cpf": "529.***.***-25", "telefone": "92999990000"}')


@pytest.mark.parametrize(
    "caminho_corpo",
    [
        ("/clientes", {"cpf": CPF_INVALIDO_ENVIADO, "telefone": "92999990000"}),
        ("/destinatarios", {"nome": "Joao", "cpf": CPF_INVALIDO_ENVIADO, "telefone": "1", "endereco": "R", "municipio": "T"}),
    ],
)
def test_erro_422_nao_repete_o_cpf_digitado(client, headers_cliente, caminho_corpo):
    caminho, corpo = caminho_corpo

    resposta = client.post(caminho, json=corpo, headers=headers_cliente)

    assert resposta.status_code == 422
    assert CPF_INVALIDO_ENVIADO not in resposta.text
    assert all("input" not in erro for erro in resposta.json()["detail"])
    assert resposta.json()["detail"][0]["loc"][-1] == "cpf"  # a mensagem de erro continua util
