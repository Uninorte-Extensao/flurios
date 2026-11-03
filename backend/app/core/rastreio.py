import secrets
import string

PREFIXO = "FLX"
TAMANHO_SUFIXO = 10
_ALFABETO = string.ascii_uppercase + string.digits


def gerar_codigo_rastreio() -> str:
    sufixo = "".join(secrets.choice(_ALFABETO) for _ in range(TAMANHO_SUFIXO))

    return f"{PREFIXO}{sufixo}"
