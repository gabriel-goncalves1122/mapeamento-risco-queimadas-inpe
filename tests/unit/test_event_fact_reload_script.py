from src.config.constants import PROJECT_ROOT


def test_reload_event_fact_script_nao_reingere_dimensoes():
    script = PROJECT_ROOT / "scripts" / "maintenance" / "druid_reload" / "reload_event_fact.sh"
    texto = script.read_text(encoding="utf-8")

    assert "fato_eventos_incendio" in texto
    assert "streaming_eventos_incendio" in texto
    assert "fato_eventos_incendio.json" in texto

    specs_dimensoes = {
        "dim_municipios_coordenadas.json",
        "dim_hospitais_cnes.json",
        "dim_terras_indigenas_funai.json",
        "dim_rodovias_federais.json",
        "dim_ons_linhas_transmissao.json",
        "dim_ons_subestacoes.json",
        "dim_ons_sistemas_isolados.json",
    }
    assert specs_dimensoes.isdisjoint(texto.split())


def test_reload_event_fact_script_tem_guardrails_operacionais():
    script = PROJECT_ROOT / "scripts" / "maintenance" / "druid_reload" / "reload_event_fact.sh"
    texto = script.read_text(encoding="utf-8")

    assert "--dry-run" in texto
    assert "--yes" in texto
    assert "--run-producer" in texto
    assert "/supervisor/$SUPERVISOR_ID/reset" in texto
    assert "MIN_TOTAL_FOCOS" in texto
    assert "EVENTOS_MAX_DURATION_DAYS" in texto
    assert "data/results/ingestion/fato_eventos" in texto
