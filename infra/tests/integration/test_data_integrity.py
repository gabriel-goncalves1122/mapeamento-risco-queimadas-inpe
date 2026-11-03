import pytest
import requests

DRUID_BROKER = "http://localhost:8082/druid/v2/sql"

def query_druid(sql: str) -> list:
    payload = {"query": sql, "resultFormat": "object"}
    try:
        response = requests.post(DRUID_BROKER, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        pytest.skip("Druid nao esta rodando no localhost:8082")
    except Exception as e:
        pytest.fail(f"Erro ao consultar Druid: {e}")


def test_tabelas_fatos_possuem_dados():
    res_focos = query_druid("SELECT COUNT(*) as total FROM fato_focos_incendio")
    assert res_focos[0]["total"] > 0, "A tabela fato_focos_incendio esta vazia ou nao existe"

    res_eventos = query_druid("SELECT COUNT(*) as total FROM fato_eventos_incendio")
    assert res_eventos[0]["total"] > 0, "A tabela fato_eventos_incendio esta vazia ou nao existe"


def test_dimensoes_possuem_dados_e_lookups_acessiveis():
    dimensoes = [
        "dim_hospitais_cnes",
        "dim_municipios_coordenadas",
        "dim_ons_linhas_transmissao",
        "dim_ons_sistemas_isolados",
        "dim_ons_subestacoes",
        "dim_rodovias_federais",
        "dim_terras_indigenas"
    ]
    for dim in dimensoes:
        res = query_druid(f"SELECT COUNT(*) as total FROM {dim}")
        assert res[0]["total"] > 0, f"A dimensao {dim} esta vazia ou nao existe"

    # Verificar se LOOKUP esta registrado e roda sem erro
    res_lookup = query_druid("SELECT LOOKUP('1100015', 'municipios_uf') as uf")
    assert len(res_lookup) > 0, "LOOKUP falhou ao processar a query"


def test_cobertura_geografica_eventos():
    res = query_druid("SELECT COUNT(DISTINCT fk_bioma) as biomas, COUNT(DISTINCT LOOKUP(fk_municipio_principal, 'municipios_uf')) as ufs FROM fato_eventos_incendio")
    assert res[0]["biomas"] >= 4, "Eventos deveriam cobrir pelo menos 4 biomas"
    assert res[0]["ufs"] >= 15, "Eventos deveriam cobrir pelo menos 15 UFs"

def test_lookups_resolvem_corretamente():
    res = query_druid("SELECT LOOKUP(codigo_ibge, 'municipios_uf') as uf FROM dim_municipios_coordenadas WHERE codigo_ibge IS NOT NULL LIMIT 1")
    assert res[0]["uf"] is not None, "LOOKUP municipio -> UF falhou em amostras"

def test_ordenacao_virtual_dataset_max_frp():
    res = query_druid('''
        SELECT max_frp 
        FROM fato_eventos_incendio 
        GROUP BY 1, fire_event_id, __time, latitude_centroide, longitude_centroide, fk_bioma, total_focos, soma_frp, area_evento_km2 
        ORDER BY max_frp DESC 
        LIMIT 100
    ''')
    for i in range(len(res) - 1):
        assert res[i]["max_frp"] >= res[i+1]["max_frp"], "Ordenacao falhou"

def test_janela_temporal():
    res = query_druid("SELECT COUNT(DISTINCT TIME_FLOOR(__time, 'P1M')) as meses FROM fato_eventos_incendio")
    assert res[0]["meses"] >= 6, "Os dados deveriam cobrir pelo menos 6 meses distintos"
