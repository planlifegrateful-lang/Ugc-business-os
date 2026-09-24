#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
rm -f affiliate_ops.sqlite3
python3 affiliate_ops.py add-product --name "Smoke Test Product" --category "test" --url "https://example.com" --affiliate-url "https://example.com/?ref=test"
PID=$(python3 - <<'PY'
import sqlite3
c=sqlite3.connect('affiliate_ops.sqlite3')
print(c.execute('select id from products limit 1').fetchone()[0])
PY
)
python3 affiliate_ops.py add-evidence --product-id "$PID" --source-url "https://example.com/specs" --claim "The official page states the product has a documented feature." --verified
python3 affiliate_ops.py create-content --product-id "$PID" --channel tiktok --angle "buyer checklist"
CID=$(python3 - <<'PY'
import sqlite3
c=sqlite3.connect('affiliate_ops.sqlite3')
print(c.execute('select id from content limit 1').fetchone()[0])
PY
)
python3 affiliate_ops.py approve --content-id "$CID" --reviewer "smoke-test" --decision approved --notes "Automated smoke test only."
python3 affiliate_ops.py export
python3 affiliate_ops.py report
