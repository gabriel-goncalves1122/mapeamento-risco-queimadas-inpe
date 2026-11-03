#!/bin/bash
uv run pytest "$(dirname "$0")/tests" "$@"
