#!/bin/bash
# Convenient runner alias for setup_and_run_raspberry.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/setup_and_run_raspberry.sh" "$@"
