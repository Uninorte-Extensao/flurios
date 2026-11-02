def mascarar_cpf(cpf: str) -> str:
    return f"{cpf[0:3]}.***.***-{cpf[9:11]}"
