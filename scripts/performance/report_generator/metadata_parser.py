from pathlib import Path
from scripts.performance.capacity_metadata import PROJECT_ROOT
QUERY_FAMILY_GUIDE = {
    "latency_simple": {
        "titulo": "Latencia simples",
        "conceito": "Consultas pequenas usadas para medir o piso de resposta do Broker e a leitura basica de segmentos.",
        "hipotese": "Se ate essas consultas oscilarem, o problema esta no cluster ou na disponibilidade dos segmentos, nao na complexidade analitica.",
        "motivo": "Funciona como controle experimental para comparar as consultas mais pesadas.",
        "impacto": "Pressiona pouco o Historical; serve para medir overhead de SQL, roteamento e filtros simples.",
    },
    "olap_pesado": {
        "titulo": "OLAP pesado",
        "conceito": "Agregacoes, agrupamentos multidimensionais, soma, media e count distinct sobre dimensoes batch.",
        "hipotese": "Quanto mais cardinalidade e agregacao numerica, maior a pressao sobre processamento e merge de resultados.",
        "motivo": "Representa o uso esperado de um banco OLAP em paineis de resumo e ranking.",
        "impacto": "Exige varredura de colunas, agregacao no Historical e merge no Broker.",
    },
    "joins_dimensionais": {
        "titulo": "Joins dimensionais",
        "conceito": "Cruzamentos entre dimensoes ja enriquecidas pelo ETL para simular visoes analiticas territoriais.",
        "hipotese": "Joins com hospitais, municipios e terras indigenas devem expor gargalos de planejamento, shuffle e merge.",
        "motivo": "Testa o limite pratico de usar Druid SQL para cruzamentos que o Superset pode exigir.",
        "impacto": "Pressiona Broker e Historical ao mesmo tempo, principalmente quando a maior dimensao participa.",
    },
    "payload_espacial": {
        "titulo": "Payload espacial",
        "conceito": "Leituras de `path_json` e campos de geometria serializada usados por mapas no Superset.",
        "hipotese": "Mesmo sem calculo espacial nativo, retornar strings grandes aumenta bytes e latencia de resposta.",
        "motivo": "Mede o custo operacional do contrato visual adotado para Druid/Superset.",
        "impacto": "Pressiona I/O, serializacao e tamanho de resposta ao cliente.",
    },
    "dashboard_misto": {
        "titulo": "Dashboard misto",
        "conceito": "Consultas compostas que combinam padroes de painel real: agregacao, joins, union e regras de qualidade.",
        "hipotese": "A mistura de padroes aproxima melhor a experiencia de uso do que queries isoladas.",
        "motivo": "Valida se o perfil suporta uma sessao analitica mais proxima do Superset.",
        "impacto": "Exercita planejamento SQL, subconsultas, union, filtros e agregacoes em uma mesma carga.",
    },
    "fatos_streaming": {
        "titulo": "Fatos e Streaming",
        "conceito": "Consultas pesadas diretamente sobre os maiores volumes de dados com agregacoes temporais.",
        "hipotese": "A tabela fato e o gargalo e pode saturar o motor Scan e GroupBy do Druid sem filtros eficientes.",
        "motivo": "Simula carga baseada no historico sem camada semantica.",
        "impacto": "Pressao maxima no Historical Node.",
    },
    "virtual_datasets": {
        "titulo": "Virtual Datasets",
        "conceito": "Modelos multidimensionais com varios lookups simulando a camada semantica real.",
        "hipotese": "Lookups sobre uma Fato grande nao deve derrubar a performance devido aos mapas compactados.",
        "motivo": "Representa o workload mais realista e pesado gerado pelos dashboards em producao.",
        "impacto": "Pressao distribuida entre Historical e Broker.",
    },
}

def parse_query_metadata(sql_text):
    metadata = {}
    body_lines = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") and ":" in stripped:
            key, value = stripped[2:].split(":", 1)
            metadata[key.strip()] = value.strip()
        else:
            body_lines.append(line)
    return metadata, "\n".join(body_lines).strip()


def read_query_catalog(sql_dir):
    rows = []
    for path in sorted(sql_dir.rglob("*.sql")):
        text = path.read_text(encoding="utf-8")
        metadata, body = parse_query_metadata(text)
        categoria = metadata.get("categoria", path.parent.name)
        guide = QUERY_FAMILY_GUIDE.get(categoria, {})
        objetivo = metadata.get("objetivo", "")
        rows.append(
            {
                "query_id": f"{path.parent.name}/{path.stem}",
                "path": str(path.relative_to(PROJECT_ROOT)),
                "categoria": categoria,
                "familia": guide.get("titulo", categoria),
                "conceito": guide.get("conceito", ""),
                "hipotese": guide.get("hipotese", ""),
                "motivo_cientifico": f"{guide.get('motivo', '')} Objetivo local: {objetivo}".strip(),
                "impacto_druid": guide.get("impacto", ""),
                "objetivo": objetivo,
                "datasource": metadata.get("datasource", ""),
                "padrao_carga": metadata.get("padrao_carga", ""),
                "visualizacao": metadata.get("visualizacao", ""),
                "sql": body,
            }
        )
    return rows

