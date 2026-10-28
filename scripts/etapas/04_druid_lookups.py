import os
import csv
import json
import urllib.request
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DIMS_DIR = os.path.join(PROJECT_ROOT, "pipelines/silver/data/dimensions")
DRUID_URL = os.environ.get("DRUID_OVERLORD_URL", "http://localhost:8081")

def get_csv_columns(filename):
    filepath = os.path.join(DIMS_DIR, filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            return next(reader)
        except StopIteration:
            return []

def make_uri_lookup(filename, key_col, val_col):
    cols = get_csv_columns(filename)
    if not cols:
        return None
        
    return {
        "version": str(int(time.time())),
        "lookupExtractorFactory": {
            "type": "cachedNamespace",
            "extractionNamespace": {
                "type": "uri",
                "uri": f"file:///opt/pipelines/silver/data/dimensions/{filename}",
                "namespaceParseSpec": {
                    "format": "csv",
                    "columns": cols,
                    "skipHeaderRows": 1,
                    "keyColumn": key_col,
                    "valueColumn": val_col
                }
            },
            "firstCacheTimeout": 0
        }
    }

# Configurando os mapas usando URI (Sem sobrecarregar o Coordinator com JSON gigante)
lookups = {
  "municipios_nome": make_uri_lookup("dim_municipios_coordenadas.csv", "codigo_ibge", "municipios_nome"),
  "municipios_uf": make_uri_lookup("dim_municipios_coordenadas.csv", "codigo_ibge", "estado_sigla"),
  "municipios_regiao": make_uri_lookup("dim_municipios_coordenadas.csv", "codigo_ibge", "regiao_brasil"),
  
  "hospitais_nome": make_uri_lookup("dim_hospitais_cnes.csv", "codigo_cnes", "nome_hospital"),
  "hospitais_tipo": make_uri_lookup("dim_hospitais_cnes.csv", "codigo_cnes", "tipo_unidade"),
  "hospitais_critico": make_uri_lookup("dim_hospitais_cnes.csv", "codigo_cnes", "tipo_unidade_critica"),
  "hospitais_24h": make_uri_lookup("dim_hospitais_cnes.csv", "codigo_cnes", "funciona_24h"),

  "ti_nome": make_uri_lookup("dim_terras_indigenas.csv", "codigo_ti", "nome_terra_indigena"),
  "ti_etnia": make_uri_lookup("dim_terras_indigenas.csv", "codigo_ti", "etnia"),
  "ti_uf": make_uri_lookup("dim_terras_indigenas.csv", "codigo_ti", "estado_sigla"),
  "ti_path_json": make_uri_lookup("dim_terras_indigenas.csv", "codigo_ti", "path_json"),

  "linha_nome": make_uri_lookup("dim_ons_linhas_transmissao.csv", "id_linha_transmissao", "nome_linha"),
  "linha_tensao": make_uri_lookup("dim_ons_linhas_transmissao.csv", "id_linha_transmissao", "tensao_kv"),
  "linha_uf": make_uri_lookup("dim_ons_linhas_transmissao.csv", "id_linha_transmissao", "estado_sigla_estimado"),
  "linha_path_json": make_uri_lookup("dim_ons_linhas_transmissao.csv", "id_linha_transmissao", "path_json"),

  "subestacao_nome": make_uri_lookup("dim_ons_subestacoes.csv", "id_subestacao", "nome_subestacao"),
  "subestacao_capacidade": make_uri_lookup("dim_ons_subestacoes.csv", "id_subestacao", "capacidade_mw"),
  "subestacao_risco_cascata": make_uri_lookup("dim_ons_subestacoes.csv", "id_subestacao", "risco_cascata"),
  "subestacao_betweenness": make_uri_lookup("dim_ons_subestacoes.csv", "id_subestacao", "betweenness_score_norm"),

  "sistema_isolado_nome": make_uri_lookup("dim_ons_sistemas_isolados.csv", "id_sistema_isolado", "nome_sistema_isolado"),
  "sistema_isolado_uf": make_uri_lookup("dim_ons_sistemas_isolados.csv", "id_sistema_isolado", "estado_sigla"),

  "rodovia_codigo": make_uri_lookup("dim_rodovias_federais.csv", "id_trecho_rodoviario", "codigo_rodovia"),
  "rodovia_criticidade": make_uri_lookup("dim_rodovias_federais.csv", "id_trecho_rodoviario", "criticidade_rodovia")
}

payload = {
    "__default": {}
}

for lookup_name, l_config in lookups.items():
    if not l_config:
        continue
    payload["__default"][lookup_name] = l_config

def post_lookups(payload_data):
    url = f"{DRUID_URL}/druid/coordinator/v1/lookups/config"
    req = urllib.request.Request(url, data=json.dumps(payload_data).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
            return True, None
    except Exception as e:
        err = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
        return False, err

print(f"Enviando configuração de {len(payload['__default'])} lookups URI ao Druid...")
success, err = post_lookups(payload)

if not success and "Not initialized" in err:
    print("Inicializando lookups no Druid...")
    post_lookups({})
    success, err = post_lookups(payload)

if success:
    print("✅ Lookups configurados com sucesso no Druid!")
else:
    print(f"❌ Erro ao configurar lookups: {err}")
    exit(1)
