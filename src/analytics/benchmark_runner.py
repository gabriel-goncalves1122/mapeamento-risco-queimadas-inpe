"""
=========================================================
MÓDULO: benchmark_runner.py
---------------------------------------------------------
Função Geral: Abstrai e executa testes analíticos ou geração de relatórios de benchmark do Druid.
=========================================================
"""
import argparse
import requests
import time
import pandas as pd
import os
import statistics

DRUID_SQL_URL = "http://localhost:8888/druid/v2/sql"

def get_queries(sufixo):
    return {
        f"Bench_1_Serie_Temporal_{sufixo}": """
            SELECT 
              TIME_FLOOR(__time, 'PT1H') AS janela_hora, 
              SUM(total_focos) AS volume_focos_hora, 
              MAX(frp_maximo) AS pico_calor_registrado,
              MIN(dist_linha_minima_km) AS aproximacao_maxima_torres
            FROM "queimadas_focos_calor"
            GROUP BY 1 
            ORDER BY 1 DESC
            LIMIT 100
        """,
        f"Bench_2_Alta_Cardinalidade_{sufixo}": """
            SELECT 
              municipio, 
              bioma, 
              SUM(total_focos) AS total_focos
            FROM "queimadas_focos_calor"
            GROUP BY 1, 2 
            ORDER BY total_focos DESC 
            LIMIT 50
        """,
        f"Bench_3_Filtros_Complexos_{sufixo}": """
            SELECT 
              satelite,
              COUNT(*) as fatias_de_minuto_processadas,
              SUM(total_focos) as focos_reais
            FROM "queimadas_focos_calor"
            WHERE risco_eletrico = 'ALTO' 
              AND bioma = 'Amazônia' 
              AND em_terra_indigena = 'true'
            GROUP BY 1
        """,
        f"BI_1_ONS_Infraestrutura_{sufixo}": """
            SELECT 
              linha_afetada, 
              estado,
              SUM(total_focos) as ocorrencias_criticas, 
              MIN(dist_linha_minima_km) as menor_distancia_km, 
              MAX(frp_maximo) as intensidade_maxima_fogo
            FROM "queimadas_focos_calor"
            WHERE risco_eletrico = 'ALTO' AND linha_afetada <> 'N/A'
            GROUP BY 1, 2
            ORDER BY ocorrencias_criticas DESC 
            LIMIT 15
        """,
        f"BI_2_FUNAI_Terras_Indigenas_{sufixo}": """
            SELECT 
              nome_ti, 
              estado, 
              bioma, 
              SUM(total_focos) as focos_registrados, 
              MAX(frp_maximo) as pico_energia_frp
            FROM "queimadas_focos_calor"
            WHERE em_terra_indigena = 'true' AND nome_ti <> 'Nenhuma'
            GROUP BY 1, 2, 3
            ORDER BY pico_energia_frp DESC 
            LIMIT 10
        """,
        f"BI_3_Defesa_Civil_Risco_{sufixo}": """
            SELECT 
              estado, 
              risco_eletrico, 
              SUM(total_focos) as volume_focos,
              MIN(dist_subestacao_minima_km) as menor_dist_subestacao_estado
            FROM "queimadas_focos_calor"
            GROUP BY 1, 2
            ORDER BY volume_focos DESC
        """
    }

def run_query(query_str, use_cache=False):
    payload = {"query": query_str, "resultFormat": "object", "context": {"useCache": use_cache, "populateCache": use_cache}}
    headers = {"Content-Type": "application/json"}
    start_time = time.time()
    response = requests.post(DRUID_SQL_URL, json=payload, headers=headers)
    end_time = time.time()
    elapsed_ms = (end_time - start_time) * 1000
    if response.status_code == 200:
        return elapsed_ms, response.json()
    else:
        print(f"❌ Erro na query: {response.status_code} - {response.text}")
        return elapsed_ms, []

def run_benchmark(cores, is_compact):
    sufixo_estado = "Compacto" if is_compact else "6518Seg"
    sufixo_completo = f"{sufixo_estado}_{cores}Cores"
    
    print("="*80)
    print(f" ⚡ BENCHMARK: {sufixo_estado.upper()} + {cores} NÚCLEOS ⚡")
    print("="*80)
    
    output_dir = "data/results/tests"
    os.makedirs(output_dir, exist_ok=True)
    metrics = []
    RODADAS = 7
    queries = get_queries(sufixo_completo)

    for name, query in queries.items():
        print(f"\n🔍 Executando: {name}")

        print(f"   ❄️  Executando {RODADAS} rodadas COLD START (Lendo do Disco)...")
        cold_times = []
        for i in range(RODADAS):
            tempo, _ = run_query(query, use_cache=False)
            cold_times.append(tempo)
            time.sleep(0.2)
        
        avg_cold = statistics.mean(cold_times)

        _, _ = run_query(query, use_cache=True)
        
        print(f"   🔥 Executando {RODADAS} rodadas WARM START (Lendo da Memória RAM)...")
        warm_times = []
        dados_finais = []
        for i in range(RODADAS):
            tempo, dados_finais = run_query(query, use_cache=True)
            warm_times.append(tempo)
            time.sleep(0.2)

        avg_warm = statistics.mean(warm_times)
        linhas_retornadas = len(dados_finais) if dados_finais else 0

        if dados_finais:
            df_result = pd.DataFrame(dados_finais)
            df_result.to_csv(f"{output_dir}/{name}.csv", index=False)

        ganho_cache = round(((avg_cold - avg_warm) / avg_cold) * 100, 2) if avg_cold > 0 else 0

        metrics.append({
            "Nome_Consulta": name, "Cold_1_ms": round(cold_times[0], 2), "Cold_2_ms": round(cold_times[1], 2), "Cold_3_ms": round(cold_times[2], 2),
            "Cold_4_ms": round(cold_times[3], 2), "Cold_5_ms": round(cold_times[4], 2), "Cold_6_ms": round(cold_times[5], 2), "Cold_7_ms": round(cold_times[6], 2),
            "Media_Cold_ms": round(avg_cold, 2), "Warm_1_ms": round(warm_times[0], 2), "Warm_2_ms": round(warm_times[1], 2), "Warm_3_ms": round(warm_times[2], 2),
            "Warm_4_ms": round(warm_times[3], 2), "Warm_5_ms": round(warm_times[4], 2), "Warm_6_ms": round(warm_times[5], 2), "Warm_7_ms": round(warm_times[6], 2),
            "Media_Warm_ms": round(avg_warm, 2), "Linhas_Retornadas": linhas_retornadas, "Ganho_Cache_%": ganho_cache
        })

        print(f"   📊 Média Cold: {avg_cold:.2f} ms | Média Warm: {avg_warm:.2f} ms")
        print(f"   🚀 Otimização do Cache: {ganho_cache}%")

    df_metrics = pd.DataFrame(metrics)
    metric_file = f"{output_dir}/relatorio_estatistico_{sufixo_completo}.csv"
    df_metrics.to_csv(metric_file, index=False)
    
    print("-" * 80)
    print(f"✅ Relatório de testes salvo com sucesso em:\n   -> {metric_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rodar benchmarks no Druid.")
    parser.add_argument("--cores", type=int, required=True, help="Número de núcleos alocados (ex: 2, 4, 6).")
    parser.add_argument("--compact", action="store_true", help="Se os segmentos foram compactados.")
    args = parser.parse_args()
    
    run_benchmark(args.cores, args.compact)
