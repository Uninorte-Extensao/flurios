from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def gerar_hash_senha(senha: str) -> str:
  return password_hash.hash(senha)


