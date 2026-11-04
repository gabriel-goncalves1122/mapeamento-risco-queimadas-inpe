"""
Testes unitários do extrator de focos de queimada do INPE (`InpeQueimadasExtractor`).

Valida a resolução de URLs, o download atômico em chunks e o tratamento de falhas HTTP
utilizando cliente injetado (DIP / SRP).
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.bronze.extractors.inpe_queimadas_extractor import InpeQueimadasExtractor
from src.core.contracts.contracts import ExecutablePipelineStep


def test_inpe_extractor_contrato_executable_step(tmp_path: Path) -> None:
    """Verifica herança de ExecutablePipelineStep e nome da etapa."""
    extractor = InpeQueimadasExtractor(output_dir=tmp_path)
    assert isinstance(extractor, ExecutablePipelineStep)
    assert extractor.step_name == "InpeQueimadasExtractor"


def test_inpe_extractor_resolucao_urls() -> None:
    """Testa a geração determinística de URLs conforme o modo de agregação temporal."""
    ext_diario = InpeQueimadasExtractor(modo="diario", data_ref="20240915")
    assert ext_diario.resolver_nome_arquivo() == "focos_diario_br_20240915.csv"
    assert ext_diario.construir_url().endswith("/diario/Brasil/focos_diario_br_20240915.csv")

    ext_mensal = InpeQueimadasExtractor(modo="mensal", data_ref="202408")
    assert ext_mensal.resolver_nome_arquivo() == "focos_mensal_br_202408.csv"
    assert ext_mensal.construir_url().endswith("/mensal/Brasil/focos_mensal_br_202408.csv")

    ext_10min = InpeQueimadasExtractor(modo="10min", data_ref="20240915_1430")
    assert ext_10min.resolver_nome_arquivo() == "focos_10min_20240915_1430.csv"
    assert ext_10min.construir_url().endswith("/10min/focos_10min_20240915_1430.csv")

    with pytest.raises(ValueError, match="Modo de extração não suportado"):
        InpeQueimadasExtractor(modo="invalido").resolver_nome_arquivo()


def test_inpe_extractor_download_com_sucesso(tmp_path: Path) -> None:
    """Valida o download streaming e a persistência do CSV em disco."""
    csv_bytes = b"DataHora,Satelite,Pais,Estado,Municipio,Bioma,DiaSemChuva,Precipitacao,RiscoFogo,FRP,Latitude,Longitude\n2024-09-15 12:00:00,AQUA_M-T,Brasil,MG,Itajuba,Mata Atlantica,10,0.0,0.8,45.2,-22.425,-45.452\n"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_content.return_value = [csv_bytes]

    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp

    extractor = InpeQueimadasExtractor(
        output_dir=tmp_path,
        modo="diario",
        data_ref="20240915",
        http_client=mock_client,
    )

    arquivo_salvo = extractor.execute()

    assert arquivo_salvo.exists()
    assert arquivo_salvo.name == "focos_diario_br_20240915.csv"
    assert arquivo_salvo.read_bytes() == csv_bytes
    mock_client.get.assert_called_once()


def test_inpe_extractor_falha_http_lanca_excecao(tmp_path: Path) -> None:
    """Garante que respostas HTTP != 200 disparam exceção clara e não criam arquivos corrompidos."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404

    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp

    extractor = InpeQueimadasExtractor(
        output_dir=tmp_path,
        modo="diario",
        data_ref="20240915",
        http_client=mock_client,
    )

    with pytest.raises(RuntimeError, match="HTTP 404"):
        extractor.execute()

    # Garante que nenhum arquivo parcial ou temporário permaneceu no disco
    assert list(tmp_path.glob("*.csv")) == []
    assert list(tmp_path.glob("*.tmp")) == []
