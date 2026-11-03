from pathlib import Path
from unittest.mock import MagicMock

from src.bronze.extractors.ingestao_aneel import AneelArcGisExtractor
from src.core.contracts import ExecutablePipelineStep


def test_aneel_extractor_is_executable_step(tmp_path: Path):
    extractor = AneelArcGisExtractor(output_dir=tmp_path)
    assert isinstance(extractor, ExecutablePipelineStep)
    assert extractor.step_name == "AneelArcGisExtractor"


def test_aneel_extractor_mock_http(tmp_path: Path):
    mock_http = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-45.0, -22.0]},
                "properties": {"OBJECTID": 1, "NOMESUB": "SE Teste"},
            }
        ]
    }
    mock_http.get.return_value = mock_response

    extractor = AneelArcGisExtractor(
        output_dir=tmp_path,
        camadas={"subestacoes": 3},
        http_client=mock_http,
        rate_limit_s=0.0,
    )
    result = extractor.execute()
    assert "subestacoes" in result
    assert result["subestacoes"].exists()
