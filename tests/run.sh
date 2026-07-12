#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

bash -n "$ROOT/install/install.sh" "$ROOT/tests/test_install.sh"
node --check "$ROOT/automation/quickadd/rollup.js"
node --check "$ROOT/tests/test_rollup.js"

bash "$ROOT/tests/test_install.sh"
node "$ROOT/tests/test_rollup.js"
python "$ROOT/tests/test_python_tools.py"

echo "All regression checks passed."
