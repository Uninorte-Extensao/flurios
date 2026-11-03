from app.core.rastreio import PREFIXO, TAMANHO_SUFIXO, gerar_codigo_rastreio


def test_gerar_codigo_rastreio_tem_prefixo_fixo():
    codigo = gerar_codigo_rastreio()

    assert codigo.startswith(PREFIXO)


def test_gerar_codigo_rastreio_tem_tamanho_esperado():
    codigo = gerar_codigo_rastreio()

    assert len(codigo) == len(PREFIXO) + TAMANHO_SUFIXO


def test_gerar_codigo_rastreio_usa_apenas_letras_maiusculas_e_digitos():
    codigo = gerar_codigo_rastreio()
    sufixo = codigo[len(PREFIXO):]

    assert sufixo.isalnum()
    assert sufixo == sufixo.upper()


def test_gerar_codigo_rastreio_gera_codigos_diferentes():
    codigos = {gerar_codigo_rastreio() for _ in range(50)}

    assert len(codigos) == 50
