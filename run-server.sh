#!/bin/bash
# Platform-agnostic launcher for sequence-mcp server
# Uses script's own location to find the venv

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/venv/bin/python" -m sequence_mcp.server "$@"
