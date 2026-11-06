import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError

from alembic import command
from alembic.config import Config
from app.models.empresa import Empresa
from app.models.retirada import Retirada


def _nova(encomenda_id, empresa_id, **extra):
    dados = {
        "encomenda_id": encomenda_id,
        "empresa_id": empresa_id,
        "cpf_retirante": "11122233396",
        "termo_aceito": True,
    }
    dados.update(extra)
    return Retirada(**dados)


def test_grava_retirada_com_cpf_completo(
    db_session, headers_empresa, criar_encomenda_no_banco
):
    empresa = db_session.query(Empresa).one()
    encomenda = criar_encomenda_no_banco()

    db_session.add(_nova(encomenda.id, empresa.id))
    db_session.commit()

    salva = db_session.query(Retirada).one()
    assert salva.encomenda_id == encomenda.id
    assert salva.empresa_id == empresa.id
    assert salva.cpf_retirante == "11122233396"
    assert salva.termo_aceito is True
    assert salva.criado_em is not None


def test_so_uma_retirada_por_encomenda(
    db_session, headers_empresa, criar_encomenda_no_banco
):
    empresa = db_session.query(Empresa).one()
    encomenda = criar_encomenda_no_banco()

    db_session.add(_nova(encomenda.id, empresa.id))
    db_session.commit()

    db_session.add(_nova(encomenda.id, empresa.id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_termo_aceito_e_obrigatorio_no_banco(
    db_session, headers_empresa, criar_encomenda_no_banco
):
    empresa = db_session.query(Empresa).one()
    encomenda = criar_encomenda_no_banco()

    db_session.add(_nova(encomenda.id, empresa.id, termo_aceito=None))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_migration_cria_e_remove_tabela_em_banco_temporario(tmp_path):
    """Sobe e desce a migration em um banco descartavel, nunca no flurios.db."""
    url = f"sqlite:///{tmp_path / 'migration.db'}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    engine = create_engine(url)

    command.upgrade(config, "head")
    assert "retiradas" in inspect(engine).get_table_names()
    colunas = {c["name"] for c in inspect(engine).get_columns("retiradas")}
    assert colunas == {
        "id",
        "encomenda_id",
        "empresa_id",
        "cpf_retirante",
        "termo_aceito",
        "criado_em",
    }

    command.downgrade(config, "-1")
    assert "retiradas" not in inspect(engine).get_table_names()
    assert "pessoas_autorizadas" in inspect(engine).get_table_names()

    engine.dispose()
