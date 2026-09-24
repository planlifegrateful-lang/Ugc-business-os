#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m py_compile affiliate_ops.py
python3 affiliate_ops.py report
mkdir -p exports
echo "Affiliate operations system initialized at $(pwd)"
