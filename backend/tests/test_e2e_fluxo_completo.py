"""Bateria ponta a ponta do backend (somente leitura do codigo da aplicacao).

Percorre o fluxo real pela API HTTP, sem atalhos no banco: administrador monta
embarcacao/rota/paradas, cliente se cadastra e cria a encomenda, a empresa
opera a viagem, a retirada acontece e o dashboard fecha coerente. Depois
cobre o caminho de excecao (viagem cancelada -> imprevisto -> realocacao).

O banco e um arquivo SQLite temporario criado com `alembic upgrade head`
(o mesmo caminho das migrations de verdade); o flurios.db nunca e tocado.

Cada divergencia em relacao ao esperado (regras do CLAUDE.md) e registrada
pelo `Verificador` em vez de abortar o teste: o fluxo continua ate o fim e o
teste falha no final listando TODOS os desvios encontrados. Esta bateria so
testa e reporta; nao corrige nada.
"""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import get_db
from app.main import app
from app.scripts.criar_admin import criar_primeiro_administrador

RAIZ_BACKEND = Path(__file__).resolve().parents[1]

CPF_CLIENTE = "11122233396"
CPF_DESTINATARIO = "22233344405"
CPF_AUTORIZADA = "33344455508"
CPF_ERRADO = "52998224725"
SENHA = "senha123"

HISTORICO_ESPERADO = [
    ("pendente", None),
    ("recebida", None),
    ("aguardando_embarque", None),
    ("embarcada", None),
    ("em_transito", "Manaus"),
    ("em_transito", "Tefé"),
    ("chegou_ao_destino", None),
    ("a_retirar", None),
    ("entregue", None),
]


class Verificador:
    """Soft assert: guarda as divergencias e deixa o fluxo seguir."""

    def __init__(self):
        self.falhas = []
        self.conhecidos = []

    def ok(self, condicao, mensagem):
        if not condicao:
            self.falhas.append(mensagem)
        return bool(condicao)

    def igual(self, obtido, esperado, mensagem):
        if obtido != esperado:
            self.falhas.append(f"{mensagem}: esperado {esperado!r}, obtido {obtido!r}")
            return False
        return True

    def conhecido(self, condicao, defeito, mensagem):
        """Desvio ja listado em docs/relatorio-testes-e2e.md (ID `defeito`).

        Nao derruba a suite: o teste termina como xfail citando o defeito. Quando
        o defeito for corrigido a condicao passa e o xfail some sozinho.
        """
        if not condicao:
            self.conhecidos.append(f"{defeito}: {mensagem}")
        return bool(condicao)

    def exigir(self):
        """Falha o teste, no fim do fluxo, listando todos os desvios novos."""
        assert not self.falhas, (
            f"{len(self.falhas)} desvio(s) encontrado(s):\n"
            + "\n".join(f" - {f}" for f in self.falhas)
        )
        if self.conhecidos:
            pytest.xfail("defeitos conhecidos (ver relatorio): " + " | ".join(self.conhecidos))


@pytest.fixture()
def v():
    return Verificador()


@pytest.fixture()
def api(tmp_path):
    """Cliente HTTP sobre um banco temporario criado pelas migrations."""
    url = f"sqlite:///{(tmp_path / 'e2e.db').as_posix()}"

    config = Config(str(RAIZ_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(RAIZ_BACKEND / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")

    engine = create_engine(url, connect_args={"check_same_thread": False})
    sessao = sessionmaker(bind=engine)

    def _get_db():
        db = sessao()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    db_setup = sessao()
    try:
        criar_primeiro_administrador(db_setup, "Admin Flurios", "admin@flurios.com", SENHA)
    finally:
        db_setup.close()

    yield TestClient(app)

    app.dependency_overrides.clear()
    engine.dispose()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def login(api, email, senha=SENHA):
    resposta = api.post("/usuarios/login", json={"email": email, "senha": senha})
    assert resposta.status_code == 200, resposta.text
    return auth(resposta.json()["access_token"])


def criar_funcionario(api, admin, nome, email, perfil):
    """Usuario se cadastra e o administrador o vincula a empresa com o perfil."""
    r = api.post("/usuarios", json={"nome": nome, "email": email, "senha": SENHA})
    assert r.status_code == 201, r.text
    r = api.post("/empresas", json={"email": email, "perfil": perfil}, headers=admin)
    assert r.status_code == 201, r.text
    return login(api, email)


def criar_cliente(api, nome, email, cpf):
    r = api.post("/usuarios", json={"nome": nome, "email": email, "senha": SENHA})
    assert r.status_code == 201, r.text
    headers = login(api, email)
    r = api.post("/clientes", json={"cpf": cpf, "telefone": "(92) 99999-0000"}, headers=headers)
    assert r.status_code == 201, r.text
    return headers, r.json()


def mudar_status(api, headers, encomenda_id, novo_status):
    return api.patch(
        f"/encomendas/{encomenda_id}/status", json={"status": novo_status}, headers=headers
    )


def historico(api, headers, codigo):
    r = api.get(f"/encomendas/{codigo}/rastreio", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_fluxo_completo_e_caminho_de_excecao(api, v):
    # ------------------------------------------------------------------ equipe
    admin = login(api, "admin@flurios.com")
    me = api.get("/usuarios/me", headers=admin).json()
    v.igual((me["tipo"], me["perfil"]), ("empresa", "administrador"), "/usuarios/me do admin")

    atendente = criar_funcionario(api, admin, "Ana Atendente", "ana@flurios.com", "atendente")
    operador = criar_funcionario(api, admin, "Otávio Operador", "otavio@flurios.com", "operador_embarcacao")
    retirada = criar_funcionario(api, admin, "Rita Retirada", "rita@flurios.com", "funcionario_retirada")

    # --------------------------------------- administrador: embarcacao/rota/paradas
    r = api.post("/embarcacoes", json={"nome": "Rio Negro I", "capacidade": 5}, headers=atendente)
    v.igual(r.status_code, 403, "atendente nao pode cadastrar embarcacao")

    r = api.post("/embarcacoes", json={"nome": "Rio Negro I", "capacidade": 5}, headers=admin)
    assert r.status_code == 201, r.text
    embarcacao = r.json()
    v.ok(embarcacao["ativa"] is True, "embarcacao nasce ativa")

    r = api.post("/rotas", json={"nome": "Manaus - Coari"}, headers=admin)
    assert r.status_code == 201, r.text
    rota = r.json()

    paradas = {}
    for nome, ordem in (("Manaus", 1), ("Tefé", 2), ("Coari", 3)):
        r = api.post(f"/rotas/{rota['id']}/paradas", json={"nome": nome, "ordem": ordem}, headers=admin)
        assert r.status_code == 201, r.text
        paradas[nome] = r.json()

    r = api.post(
        f"/rotas/{rota['id']}/paradas", json={"nome": "Codajás", "ordem": 2}, headers=admin
    )
    v.ok(r.status_code in (409, 422), f"ordem de parada repetida deve ser recusada (veio {r.status_code})")

    r = api.get(f"/rotas/{rota['id']}", headers=operador)
    v.igual([p["nome"] for p in r.json()["paradas"]], ["Manaus", "Tefé", "Coari"], "paradas da rota, em ordem")

    # ------------------------------------------------ cliente: cadastro e encomenda
    r = api.post("/usuarios", json={"nome": "maria souza", "email": "maria@exemplo.com", "senha": SENHA})
    assert r.status_code == 201
    cliente = login(api, "maria@exemplo.com")
    me = api.get("/usuarios/me", headers=cliente).json()
    v.igual(me["tipo"], None, "recem-cadastrado ainda sem tipo")

    r = api.post("/clientes", json={"cpf": CPF_CLIENTE, "telefone": "(92) 99999-0000"}, headers=cliente)
    assert r.status_code == 201, r.text
    v.ok(CPF_CLIENTE not in r.text, "CPF do cliente nao pode voltar completo")
    v.igual(r.json()["cpf"], "111.***.***-96", "CPF do cliente mascarado")
    v.igual(api.get("/usuarios/me", headers=cliente).json()["tipo"], "cliente", "tipo apos cadastro")

    r = api.post("/clientes", json={"cpf": "11111111111", "telefone": "1"}, headers=login(api, "ana@flurios.com"))
    v.ok(r.status_code in (400, 422), f"CPF invalido deve ser recusado (veio {r.status_code})")

    r = api.post(
        "/destinatarios",
        json={
            "nome": "João Pereira",
            "cpf": CPF_DESTINATARIO,
            "telefone": "(97) 98888-7777",
            "endereco": "Rua das Flores, 123",
            "municipio": "Tefé",
        },
        headers=cliente,
    )
    assert r.status_code == 201, r.text
    destinatario = r.json()
    v.ok(CPF_DESTINATARIO not in r.text, "CPF do destinatario nao pode voltar completo")

    r = api.get("/rotas/destinos", headers=cliente)
    destinos = r.json()
    v.igual(sorted(d["nome"] for d in destinos), ["Coari", "Tefé"], "destinos oferecidos ao cliente (sem a origem)")

    r = api.post(
        "/encomendas",
        json={
            "destinatario_id": destinatario["id"],
            "parada_destino_id": paradas["Tefé"]["id"],
            "descricao": "Caixa de ferramentas",
        },
        headers=cliente,
    )
    assert r.status_code == 201, r.text
    enc = r.json()
    v.igual(enc["status"], "pendente", "status inicial da encomenda")
    v.igual(enc["destino_nome"], "Tefé", "destino da encomenda")
    v.ok(bool(enc["codigo_rastreio"]), "codigo de rastreio gerado")

    r = api.post(
        "/encomendas",
        json={
            "destinatario_id": destinatario["id"],
            "parada_destino_id": paradas["Manaus"]["id"],
            "descricao": "Para a origem",
        },
        headers=cliente,
    )
    v.igual(r.status_code, 422, "a origem nao pode ser destino")

    # pessoa autorizada (obrigatoria): cadastra, CPF mascarado
    r = api.post(
        f"/encomendas/{enc['id']}/pessoa-autorizada",
        json={"nome": "Carlos Souza", "cpf": CPF_AUTORIZADA},
        headers=cliente,
    )
    v.igual(r.status_code, 201, "cadastro da pessoa autorizada")
    v.ok(CPF_AUTORIZADA not in r.text, "CPF da pessoa autorizada nao pode voltar completo")
    v.igual(r.json().get("cpf"), "333.***.***-08", "CPF da pessoa autorizada mascarado")

    # --------------------------------------------- empresa: recebe e associa a viagem
    r = api.get("/empresa/encomendas", headers=atendente)
    v.igual(r.json()["total"], 1, "atendente ve a encomenda do cliente")
    v.ok(CPF_DESTINATARIO not in r.text, "listagem da empresa nao expoe CPF completo")

    v.igual(mudar_status(api, atendente, enc["id"], "recebida").status_code, 200, "pendente -> recebida")

    r = api.post(
        "/viagens",
        json={"embarcacao_id": embarcacao["id"], "rota_id": rota["id"], "data_saida": "2026-12-01T08:00:00"},
        headers=operador,
    )
    assert r.status_code == 201, r.text
    viagem = r.json()
    v.igual(viagem["status"], "programada", "status inicial da viagem")

    r = api.post(f"/viagens/{viagem['id']}/encomendas", json={"encomenda_id": enc["id"]}, headers=atendente)
    v.igual(r.status_code, 201, "associar encomenda a viagem")
    v.igual(
        api.get(f"/encomendas/{enc['codigo_rastreio']}", headers=cliente).json()["status"],
        "aguardando_embarque",
        "associar leva a aguardando_embarque",
    )

    r = api.post(f"/viagens/{viagem['id']}/localizacao", json={"parada_id": paradas["Manaus"]["id"]}, headers=operador)
    v.igual(r.status_code, 409, "nao registra localizacao em viagem nao iniciada")

    r = api.patch(f"/viagens/{viagem['id']}/status", json={"status": "em_andamento"}, headers=operador)
    v.igual(r.status_code, 200, "iniciar viagem")

    # iniciar a viagem nao muda a encomenda sozinho: o operador a embarca
    status_apos_inicio = api.get(f"/encomendas/{enc['codigo_rastreio']}", headers=cliente).json()["status"]
    v.igual(status_apos_inicio, "aguardando_embarque", "iniciar viagem nao altera encomendas (operador embarca manualmente)")
    v.igual(mudar_status(api, operador, enc["id"], "embarcada").status_code, 200, "operador embarca a encomenda")

    # localizacao manual em cada parada da rota
    for nome in ("Manaus", "Tefé"):
        r = api.post(
            f"/viagens/{viagem['id']}/localizacao", json={"parada_id": paradas[nome]["id"]}, headers=operador
        )
        v.igual(r.status_code, 201, f"registrar localizacao em {nome}")
        v.igual(r.json().get("encomendas_registradas"), 1, f"encomendas registradas em {nome}")

    status_em_tefe = api.get(f"/encomendas/{enc['codigo_rastreio']}", headers=cliente).json()["status"]
    v.igual(status_em_tefe, "em_transito", "status apos registrar localizacao")

    # dashboard durante a viagem
    ocupacao = api.get("/dashboard/ocupacao", headers=admin).json()
    v.igual(ocupacao["total"], 1, "uma viagem em andamento na ocupacao")
    if ocupacao["viagens"]:
        v.igual(ocupacao["viagens"][0]["ocupacao"], 0.2, "ocupacao = 1 encomenda / capacidade 5")
    envios = api.get("/dashboard/envios-ativos", headers=admin).json()["envios"]
    if v.igual(len(envios), 1, "um envio ativo durante a viagem"):
        envio = envios[0]
        v.igual(envio["municipio_destino"], "Tefé", "municipio de destino do envio")
        # D-1 (corrigido): a encomenda para Tefé ja esta em Tefé, entao chegou ao destino
        v.igual(envio["proxima_parada"], None, "encomenda em Tefé (destino) nao tem proxima parada")
        v.igual(envio["progresso"], 1.0, "progresso 100% ao chegar no destino da encomenda")

    # chegada e retirada
    v.igual(mudar_status(api, operador, enc["id"], "chegou_ao_destino").status_code, 200, "chegou ao destino")
    v.igual(mudar_status(api, operador, enc["id"], "a_retirar").status_code, 200, "a retirar")

    r = api.post(f"/encomendas/{enc['id']}/retirada", json={"cpf_retirante": CPF_ERRADO, "termo_aceito": True}, headers=operador)
    v.igual(r.status_code, 403, "operador de embarcacao nao registra retirada")

    r = api.post(f"/encomendas/{enc['id']}/retirada", json={"cpf_retirante": CPF_AUTORIZADA, "termo_aceito": False}, headers=retirada)
    v.igual(r.status_code, 422, "retirada sem aceite do termo")

    r = api.post(f"/encomendas/{enc['id']}/retirada", json={"cpf_retirante": CPF_ERRADO, "termo_aceito": True}, headers=retirada)
    v.igual(r.status_code, 403, "retirada com CPF errado")
    v.ok(CPF_ERRADO not in r.text and CPF_AUTORIZADA not in r.text, "erro de retirada nao vaza CPF")
    v.igual(api.get(f"/encomendas/{enc['codigo_rastreio']}", headers=cliente).json()["status"], "a_retirar", "CPF errado nao entrega")

    r = api.post(f"/encomendas/{enc['id']}/retirada", json={"cpf_retirante": "333.444.555-08", "termo_aceito": True}, headers=retirada)
    v.igual(r.status_code, 201, "retirada com CPF certo (formatado)")
    v.ok(CPF_AUTORIZADA not in r.text, "CPF de quem retirou nao volta completo")
    v.igual(r.json().get("cpf_retirante"), "333.***.***-08", "CPF de quem retirou mascarado")
    v.igual(r.json().get("status_encomenda"), "entregue", "encomenda entregue")

    r = api.post(f"/encomendas/{enc['id']}/retirada", json={"cpf_retirante": CPF_AUTORIZADA, "termo_aceito": True}, headers=retirada)
    v.igual(r.status_code, 409, "retirada repetida")
    v.igual(mudar_status(api, admin, enc["id"], "recebida").status_code, 409, "entregue nao muda mais")

    # concluir viagem
    v.igual(
        api.patch(f"/viagens/{viagem['id']}/status", json={"status": "concluida"}, headers=operador).status_code,
        200,
        "concluir viagem",
    )

    # rastreio do cliente com a linha do tempo completa
    rastreio = historico(api, cliente, enc["codigo_rastreio"])
    v.igual(rastreio["status_atual"], "entregue", "status atual no rastreio")
    obtido = [(h["status"], h["parada_nome"]) for h in rastreio["historico"]]
    v.igual(obtido, HISTORICO_ESPERADO, "linha do tempo completa do rastreio")
    datas = [h["criado_em"] for h in rastreio["historico"]]
    v.ok(datas == sorted(datas), "historico em ordem cronologica")

    # privacidade: outro cliente nao rastreia
    outro, _ = criar_cliente(api, "Outro Cliente", "outro@exemplo.com", "11144477735")
    v.igual(
        api.get(f"/encomendas/{enc['codigo_rastreio']}/rastreio", headers=outro).status_code,
        404,
        "outro cliente nao rastreia codigo alheio",
    )
    v.igual(api.get("/encomendas", headers=outro).json(), [], "lista do outro cliente vazia")
    v.igual(api.get(f"/encomendas/{enc['codigo_rastreio']}/rastreio").status_code, 401, "rastreio exige login")
    v.igual(api.get("/dashboard/resumo", headers=cliente).status_code, 403, "cliente nao acessa dashboard")

    # -------------------------------------------------------- caminho de excecao
    r = api.post(
        "/encomendas",
        json={
            "destinatario_id": destinatario["id"],
            "parada_destino_id": paradas["Tefé"]["id"],
            "descricao": "Sacos de farinha",
        },
        headers=cliente,
    )
    enc2 = r.json()
    api.post(
        f"/encomendas/{enc2['id']}/pessoa-autorizada",
        json={"destinatario_e_a_pessoa": True},
        headers=cliente,
    )
    mudar_status(api, atendente, enc2["id"], "recebida")

    r = api.post(
        "/viagens",
        json={"embarcacao_id": embarcacao["id"], "rota_id": rota["id"], "data_saida": "2026-12-10T08:00:00"},
        headers=operador,
    )
    viagem2 = r.json()
    v.igual(
        api.post(f"/viagens/{viagem2['id']}/encomendas", json={"encomenda_id": enc2["id"]}, headers=atendente).status_code,
        201,
        "associar a 2a encomenda a viagem 2",
    )

    r = api.patch(f"/viagens/{viagem2['id']}/status", json={"status": "cancelada"}, headers=operador)
    v.igual(r.status_code, 200, "cancelar viagem")
    v.igual(
        api.get(f"/encomendas/{enc2['codigo_rastreio']}", headers=cliente).json()["status"],
        "imprevisto",
        "viagem cancelada -> encomenda imprevisto",
    )
    v.igual(
        api.patch(f"/viagens/{viagem2['id']}/status", json={"status": "em_andamento"}, headers=operador).status_code,
        409,
        "viagem cancelada e estado final",
    )

    # realocar: a regra do projeto e voltar a "recebida" e so entao associar a outra viagem
    r = api.post("/viagens", json={"embarcacao_id": embarcacao["id"], "rota_id": rota["id"], "data_saida": "2026-12-20T08:00:00"}, headers=operador)
    viagem3 = r.json()
    r = api.post(f"/viagens/{viagem3['id']}/encomendas", json={"encomenda_id": enc2["id"]}, headers=atendente)
    v.igual(r.status_code, 409, "encomenda em imprevisto nao e associada direto (precisa voltar a recebida)")
    v.igual(mudar_status(api, atendente, enc2["id"], "recebida").status_code, 200, "imprevisto -> recebida (realocar)")
    r = api.post(f"/viagens/{viagem3['id']}/encomendas", json={"encomenda_id": enc2["id"]}, headers=atendente)
    v.igual(r.status_code, 201, "realocar para a viagem 3")

    rastreio2 = historico(api, cliente, enc2["codigo_rastreio"])
    v.igual(rastreio2["status_atual"], "aguardando_embarque", "encomenda realocada aguardando embarque")
    v.igual(
        [h["status"] for h in rastreio2["historico"]],
        ["pendente", "recebida", "aguardando_embarque", "imprevisto", "recebida", "aguardando_embarque"],
        "historico da encomenda realocada",
    )

    # ------------------------------------------------------------ dashboard final
    resumo = api.get("/dashboard/resumo", headers=admin).json()
    v.igual(resumo["total"], 2, "dashboard: total de encomendas")
    v.igual(resumo["por_status"]["entregue"], 1, "dashboard: entregues")
    v.igual(resumo["por_status"]["aguardando_embarque"], 1, "dashboard: aguardando embarque")
    v.igual(sum(resumo["por_status"].values()), resumo["total"], "dashboard: soma dos status = total")

    viagens = api.get("/dashboard/viagens", headers=admin).json()
    v.igual(viagens["total"], 3, "dashboard: total de viagens")
    v.igual(viagens["em_andamento"], 0, "dashboard: nenhuma em andamento")
    v.igual(
        (viagens["por_status"]["concluida"], viagens["por_status"]["cancelada"], viagens["por_status"]["programada"]),
        (1, 1, 1),
        "dashboard: viagens por status",
    )
    v.igual(api.get("/dashboard/ocupacao", headers=admin).json()["total"], 0, "dashboard: ocupacao sem viagem em andamento")

    municipios = api.get("/dashboard/municipios", headers=admin).json()
    v.igual(municipios["municipios"], [{"municipio": "Tefé", "total": 2}], "dashboard: encomendas por municipio")

    envios = api.get("/dashboard/envios-ativos", headers=admin).json()
    v.igual(envios["total"], 1, "dashboard: envios ativos (entregue sai da lista)")
    if envios["envios"]:
        e = envios["envios"][0]
        v.igual(e["codigo_rastreio"], enc2["codigo_rastreio"], "envio ativo e a encomenda realocada")
        v.igual(e["destinatario"], "João Pereira", "envio ativo: destinatario")
        v.igual((e["proxima_parada"], e["progresso"]), ("Manaus", 0.0), "envio ativo: viagem programada, nada registrado")

    movs = api.get("/dashboard/movimentacoes-recentes?limite=100", headers=admin).json()
    v.igual(movs["total"], len(rastreio["historico"]) + len(rastreio2["historico"]), "dashboard: movimentacoes = soma dos historicos")
    if movs["movimentacoes"]:
        v.igual(movs["movimentacoes"][0]["status"], "aguardando_embarque", "movimentacao mais recente")

    # lista da empresa e filtros
    lista = api.get("/empresa/encomendas?status=entregue", headers=atendente).json()
    v.igual([i["codigo_rastreio"] for i in lista["itens"]], [enc["codigo_rastreio"]], "filtro por status entregue")
    v.ok(CPF_DESTINATARIO not in str(lista), "lista da empresa sem CPF completo")
    pa = api.get(f"/encomendas/{enc['id']}/pessoa-autorizada", headers=atendente)
    v.igual(pa.status_code, 200, "empresa consulta pessoa autorizada")
    v.ok(CPF_AUTORIZADA not in pa.text, "pessoa autorizada sem CPF completo para a empresa")

    v.exigir()


def test_regras_de_transicao_de_status_da_encomenda(api, v):
    """O PATCH de status recusa saltos e retrocessos (F-1, corrigido): 409; perfil e erros de entrada seguem iguais."""
    admin = login(api, "admin@flurios.com")
    cliente, _ = criar_cliente(api, "Maria", "maria2@exemplo.com", CPF_CLIENTE)
    r = api.post("/embarcacoes", json={"nome": "B", "capacidade": 2}, headers=admin)
    r = api.post("/rotas", json={"nome": "R"}, headers=admin)
    rota_id = r.json()["id"]
    api.post(f"/rotas/{rota_id}/paradas", json={"nome": "Manaus", "ordem": 1}, headers=admin)
    p = api.post(f"/rotas/{rota_id}/paradas", json={"nome": "Tefé", "ordem": 2}, headers=admin).json()
    d = api.post(
        "/destinatarios",
        json={"nome": "Fulano", "cpf": CPF_DESTINATARIO, "telefone": "1", "endereco": "x", "municipio": "Tefé"},
        headers=cliente,
    ).json()
    enc = api.post(
        "/encomendas",
        json={"destinatario_id": d["id"], "parada_destino_id": p["id"], "descricao": "Caixa"},
        headers=cliente,
    ).json()

    # F-1 (corrigido): salto e retrocesso sao recusados com 409 e o status nao muda
    r = mudar_status(api, admin, enc["id"], "a_retirar")
    v.igual(r.status_code, 409, "salto pendente -> a_retirar e recusado")
    v.igual(
        r.json().get("detail"),
        "Transicao de status invalida: pendente -> a_retirar.",
        "mensagem do salto recusado",
    )
    v.igual(
        api.get(f"/encomendas/{enc['codigo_rastreio']}", headers=cliente).json()["status"],
        "pendente",
        "salto recusado nao altera o status",
    )
    v.igual(mudar_status(api, admin, enc["id"], "recebida").status_code, 200, "pendente -> recebida")
    v.igual(mudar_status(api, admin, enc["id"], "pendente").status_code, 409, "retrocesso recebida -> pendente e recusado")
    r = mudar_status(api, cliente, enc["id"], "recebida")
    v.igual(r.status_code, 403, "cliente nao muda status")
    r = mudar_status(api, admin, enc["id"], "status_que_nao_existe")
    v.igual(r.status_code, 422, "status inexistente")
    r = mudar_status(api, admin, 99999, "recebida")
    v.igual(r.status_code, 404, "encomenda inexistente")

    v.exigir()
