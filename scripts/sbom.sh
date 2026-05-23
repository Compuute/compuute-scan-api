#!/bin/bash
# scripts/sbom.sh — generate CycloneDX SBOM for the deployed image.
# Usage: bash scripts/sbom.sh                  (writes sbom.cdx.json)
#        bash scripts/sbom.sh --upload v0.4.0  (attaches to GitHub Release)
#
# Run from the repo root with the venv active.

set -euo pipefail

OUT="${OUT:-sbom.cdx.json}"

# Install if missing (dev convenience; CI installs from requirements-dev.txt)
if ! python -c "import cyclonedx_py" >/dev/null 2>&1; then
  pip install --quiet "cyclonedx-bom>=4,<6"
fi

echo "Generating CycloneDX SBOM → $OUT"

# `cyclonedx-py environment` walks the active venv. Pin to JSON for downstream tooling.
python -m cyclonedx_py environment --output-format json --output-file "$OUT"

# Stamp metadata.component with project info for clarity
python - <<PY
import json, pathlib
p = pathlib.Path("$OUT")
data = json.loads(p.read_text())
data.setdefault("metadata", {})["component"] = {
    "type": "application",
    "name": "compuute-scan-api",
    "version": "0.4.0",
    "supplier": {"name": "Compuute AB", "url": ["https://compuute.se"]},
    "licenses": [{"license": {"id": "MIT"}}],
    "purl": "pkg:github/Compuute/compuute-scan-api@v0.4.0",
}
p.write_text(json.dumps(data, indent=2))
PY

PY_DEPS=$(python -c "import json; d=json.load(open('$OUT')); print(len(d.get('components', [])))")
echo "✓ $OUT ($PY_DEPS Python components, CycloneDX $(python -c "import json; print(json.load(open('$OUT')).get('specVersion','?'))"))"

if [ "${1:-}" = "--upload" ] && [ -n "${2:-}" ]; then
  echo "Uploading to GitHub Release $2..."
  gh release upload "$2" "$OUT" --clobber
  echo "✓ Attached to release $2"
fi
