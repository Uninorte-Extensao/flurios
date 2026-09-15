from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
)


password_hash = PasswordHash.recommended()


def gerar_hash_senha(senha: str) -> str:
    return password_hash.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return password_hash.verify(senha, senha_hash)


def criar_token_acesso(
    dados: dict,
    expira_em_minutos: int | None = None,
) -> str:
    payload = dados.copy()

    minutos = expira_em_minutos or ACCESS_TOKEN_EXPIRE_MINUTES

    expiracao = datetime.now(timezone.utc) + timedelta(minutes=minutos)

    payload.update({"exp": expiracao})

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,

    )
