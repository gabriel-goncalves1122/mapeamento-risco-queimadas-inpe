"""
Fachada de exportação dos contratos Pydantic de Tabelas Fato (`src.core.domain.models`).

Cada payload possui seu módulo dedicado segundo a regra "1 Classe Principal por Arquivo":
- `FocoFatoPayload` em `src/core/domain/foco_fato_payload.py`
- `EventoFatoPayload` em `src/core/domain/evento_fato_payload.py`
"""
from src.core.domain.evento_fato_payload import EventoFatoPayload
from src.core.domain.foco_fato_payload import FocoFatoPayload

__all__ = ["EventoFatoPayload", "FocoFatoPayload"]
