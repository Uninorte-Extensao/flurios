import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError

from alembic import command
from alembic.config import Config
from app.models.pessoa_autorizada import PessoaAutorizada


def _nova(encomenda_id, **extra):
    dados = {"encomenda_id": encomenda_id, "nome": "Ana Souza", "cpf": "11122233396"}
    dados.update(extra)
    return PessoaAutorizada(**dados)


def test_grava_pessoa_autorizada_com_cpf_completo(db_session, criar_encomenda_no_banco):
    encomenda = criar_encomenda_no_banco()

    db_session.add(_nova(encomenda.id))
    db_session.commit()

    salva = db_session.query(PessoaAutorizada).one()
    assert salva.encomenda_id == encomenda.id
    assert salva.nome == "Ana Souza"
    assert salva.cpf == "11122233396"
    assert salva.criado_em is not None


def test_so_uma_pessoa_autorizada_por_encomenda(db_session, criar_encomenda_no_banco):
    encomenda = criar_encomenda_no_banco()

    db_session.add(_nova(encomenda.id))
    db_session.commit()

    db_session.add(_nova(encomenda.id, nome="Outra Pessoa"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_encomendas_diferentes_podem_ter_pessoas_autorizadas(
    db_session, criar_encomenda_no_banco
):
    primeira = criar_encomenda_no_banco()
    segunda = criar_encomenda_no_banco()

    db_session.add_all([_nova(primeira.id), _nova(segunda.id)])
    db_session.commit()

    assert db_session.query(PessoaAutorizada).count() == 2


def test_migration_cria_e_remove_tabela_em_banco_temporario(tmp_path):
    """Sobe e desce a migration em um banco descartavel, nunca no flurios.db."""
    url = f"sqlite:///{tmp_path / 'migration.db'}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    engine = create_engine(url)

    command.upgrade(config, "head")
    assert "pessoas_autorizadas" in inspect(engine).get_table_names()
    colunas = {c["name"] for c in inspect(engine).get_columns("pessoas_autorizadas")}
    assert colunas == {"id", "encomenda_id", "nome", "cpf", "criado_em"}

    command.downgrade(config, "-1")
    assert "pessoas_autorizadas" not in inspect(engine).get_table_names()

    engine.dispose()
