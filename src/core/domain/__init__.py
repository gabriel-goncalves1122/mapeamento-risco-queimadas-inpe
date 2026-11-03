"""Contratos Pydantic de dados e payloads das Tabelas Fato."""
from src.core.domain.evento_fato_payload import EventoFatoPayload
from src.core.domain.foco_fato_payload import FocoFatoPayload
from src.core.domain.models import EventoFatoPayload as EventoFatoPayloadAlias
from src.core.domain.models import FocoFatoPayload as FocoFatoPayloadAlias

__all__ = ["EventoFatoPayload", "FocoFatoPayload"]
