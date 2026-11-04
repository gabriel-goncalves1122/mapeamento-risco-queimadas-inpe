"""
Ponto de entrada CLI para registro de Lookups URI no Apache Druid (`04_druid_lookups.py`).

Ponto de entrada em `scripts/run/` para automações e esteiras CI/CD.
A implementação de domínio reside em `src.silver.lookups.druid_lookup_registrar`.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parents[2])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.silver.lookups.druid_lookup_registrar import DruidLookupRegistrar


def main() -> int:
    """Entrypoint CLI de registro dos lookups no Druid."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    ok = DruidLookupRegistrar().execute()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
