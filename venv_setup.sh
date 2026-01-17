#!/usr/bin/env bash
set -euo pipefail

# Create a virtual environment and install requirements
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Virtualenv created at .venv. Activate with: source .venv/bin/activate"
