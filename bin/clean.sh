#!/bin/bash
# Clean __pycache__ and bytecode files
# Usage: ./clean.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Cleaning __pycache__ directories..."
find "$SCRIPT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "Cleaning .pyc and .pyo files..."
find "$SCRIPT_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$SCRIPT_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true

echo "Cleaning build directories..."
rm -rf "$SCRIPT_DIR/build" "$SCRIPT_DIR/dist" "$SCRIPT_DIR/*.egg-info" 2>/dev/null || true

echo "Done!"
