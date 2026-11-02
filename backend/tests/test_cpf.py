import pytest

from app.core.cpf import cpf_e_valido, normalizar_cpf


def test_cpf_e_valido_aceita_cpf_valido():
    assert cpf_e_valido("12345678909") is True


def test_cpf_e_valido_rejeita_digito_verificador_errado():
    assert cpf_e_valido("12345678900") is False


def test_cpf_e_valido_rejeita_todos_digitos_iguais():
    assert cpf_e_valido("11111111111") is False


def test_cpf_e_valido_rejeita_tamanho_errado():
    assert cpf_e_valido("123456789") is False


def test_normalizar_cpf_remove_pontuacao():
    assert normalizar_cpf("123.456.789-09") == "12345678909"


def test_normalizar_cpf_levanta_erro_para_cpf_invalido():
    with pytest.raises(ValueError):
        normalizar_cpf("111.111.111-11")
