#!/bin/bash

# Setup virtual environment for agent component

echo "Setting up virtual environment for Insurance Agent..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment with uv using Python 3.11
uv venv .venv --python 3.11

# Activate virtual environment
source .venv/bin/activate

# Install dependencies with uv
uv sync

echo "Virtual environment setup complete!"
echo "To activate from agent directory: source .venv/bin/activate"
