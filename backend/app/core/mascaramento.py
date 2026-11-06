import re
from typing import Annotated

from pydantic import AfterValidator

CPF_COMPLETO = re.compile(r"\d{11}")
CPF_JA_MASCARADO = re.compile(r"\d{3}\.\*\*\*\.\*\*\*-\d{2}")
CPF_OCULTO = "***.***.***-**"


def mascarar_cpf(cpf: str) -> str:
    return f"{cpf[0:3]}.***.***-{cpf[9:11]}"


def _mascarar_para_saida(valor: str) -> str:
    """Garante a mascara na saida. Qualquer formato inesperado e ocultado por inteiro."""
    if CPF_COMPLETO.fullmatch(valor):
        return mascarar_cpf(valor)

    if CPF_JA_MASCARADO.fullmatch(valor):
        return valor

    return CPF_OCULTO


# Use nos schemas de SAIDA: o CPF completo vindo do banco sai sempre mascarado,
# mesmo que o router esqueca de mascarar.
CpfMascarado = Annotated[str, AfterValidator(_mascarar_para_saida)]
