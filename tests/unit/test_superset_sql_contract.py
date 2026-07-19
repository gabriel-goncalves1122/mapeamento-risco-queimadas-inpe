from pathlib import Path

from scripts.maintenance.run_superset_sector_queries import (
    FORBIDDEN_REFERENCES,
    aplicar_limite_previa,
    descobrir_sqls,
    split_sql,
    strip_comments,
    validar_statement,
)
from src.config.constants import PROJECT_ROOT


SQL_DIR = PROJECT_ROOT / "scripts" / "sql" / "superset"
REQUIRED_METADATA = (
    "-- setor:",
    "-- objetivo:",
    "-- datasource:",
    "-- granularidade:",
    "-- visualizacao:",
)


def test_superset_sqls_sao_selects_com_metadados_e_sem_datasources_fora_do_escopo():
    sql_files = descobrir_sqls(SQL_DIR)

    assert sql_files
    for sql_file in sql_files:
        texto = sql_file.read_text(encoding="utf-8")
        texto_lower = texto.lower()

        for metadata in REQUIRED_METADATA:
            assert metadata in texto_lower, f"{sql_file} sem metadado {metadata}"
        for termo in FORBIDDEN_REFERENCES:
            assert termo not in texto_lower, f"{sql_file} referencia {termo}"

        statements = split_sql(strip_comments(texto))
        assert len(statements) == 1, f"{sql_file} deve ter uma consulta por arquivo"
        validar_statement(statements[0], sql_file)


def test_superset_sqls_estao_organizados_por_setores_esperados():
    setores = {path.parent.name for path in descobrir_sqls(SQL_DIR)}

    assert {
        "00_catalogo",
        "01_defesa_civil",
        "02_saude",
        "03_funai",
        "04_energia",
        "05_logistica",
        "06_qualidade",
        "07_eventos_incendio",
    }.issubset(setores)


def test_runner_aplica_limite_de_previa_sem_alterar_sql_original():
    statement = "SELECT codigo_ibge FROM dim_municipios_coordenadas"
    limitado = aplicar_limite_previa(statement, 10)

    assert limitado.startswith(statement)
    assert limitado.endswith("LIMIT 10")


def test_runner_rejeita_comandos_mutantes(tmp_path: Path):
    sql_file = tmp_path / "mutante.sql"

    try:
        validar_statement("DELETE FROM dim_hospitais_cnes", sql_file)
    except ValueError as exc:
        assert "SELECT" in str(exc)
    else:
        raise AssertionError("Comando mutante deveria ser rejeitado")


def test_runner_rejeita_join_amplo_eventos_para_hospitais(tmp_path: Path):
    sql_file = tmp_path / "join_hospital_perigoso.sql"
    statement = """
    SELECT COUNT(*)
    FROM fato_eventos_incendio f
    LEFT JOIN dim_hospitais_cnes h ON f.fk_hospital = h.codigo_cnes
    """

    try:
        validar_statement(statement, sql_file)
    except ValueError as exc:
        assert "join amplo" in str(exc)
    else:
        raise AssertionError("Join amplo fato -> hospitais deveria ser rejeitado")


def test_queries_de_eventos_usam_padrao_seguro_para_hospitais():
    eventos_dir = SQL_DIR / "07_eventos_incendio"
    sqls = {path.name: path.read_text(encoding="utf-8").lower() for path in eventos_dir.glob("*.sql")}

    assert "06_saude_eventos_por_hospital_fk.sql" in sqls
    assert "07_saude_lookup_hospitais_top.sql" in sqls
    for nome, texto in sqls.items():
        assert "fato_focos_incendio" not in texto
        assert "fogo_eventos_stdbscan" not in texto
        assert "from fato_eventos_incendio" not in texto or "join dim_hospitais_cnes" not in texto, nome
