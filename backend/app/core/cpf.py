import re

def _calcular_dv(parcial: str) -> str:
    tamanho = len(parcial) + 1
    soma = sum(int(digito) * (tamanho - i) for i, digito in enumerate(parcial))
    resto = (soma * 10) % 11

    return str(resto if resto < 10 else 0)


def cpf_e_valido(cpf: str) -> bool:
    if len(cpf) != 11 or not cpf.isdigit() or cpf == cpf[0] * 11:
        return False

    dv1 = _calcular_dv(cpf[:9])
    dv2 = _calcular_dv(cpf[:9] + dv1)

    return cpf[9:] == dv1 + dv2


def normalizar_cpf(cpf: str) -> str:
    cpf_limpo = re.sub(r"\D", "", cpf)

    if not cpf_e_valido(cpf_limpo):
        raise ValueError("CPF invalido.")

    return cpf_limpo
