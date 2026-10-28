#!/bin/bash
# Descobre e roda todos os testes espalhados pelo repositório
uv run pytest pipelines/ infrastructure/ scripts/ "$@"
