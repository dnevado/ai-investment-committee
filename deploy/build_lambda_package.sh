#!/usr/bin/env bash
#
# deploy/build_lambda_package.sh — shared by provision_lambda.sh (first
# deploy) and release_lambda.sh (updates): builds build/lambda.zip
# containing aic.public + its runtime dependencies + the committed Amazon
# snapshot.
#
# Layout mirrors the repo's own src/ + data/ structure (rather than
# flattening `aic` to the zip root) so `app.py`'s existing
# `_DEFAULT_SNAPSHOT_PATH = Path(__file__).resolve().parent.parent.parent /
# "data" / "amazon_snapshot.json"` keeps resolving correctly UNMODIFIED —
# `provision_lambda.sh` sets the function's `PYTHONPATH` environment
# variable to `/var/task/src` so `import aic.public...` still works despite
# `aic` not sitting directly at the zip root.
#
# `src/aic/__init__.py`, `src/aic/public/`, and `src/aic/domain/` are
# vendored. `aic.domain` is required — `presentation.py` needs
# `EvidenceType` at runtime (found the hard way: an initial deploy omitted
# it and Lambda failed with `No module named 'aic.domain'`) — but is safe
# and lightweight to include: verified it imports nothing outside itself
# (`grep`-checked every `aic.domain` submodule). `aic.dcf`/`aic.research`/
# `aic.bullbear`/`aic.committee`/`aic.report`/`aic.workflow` are NOT
# vendored — `presentation.py`'s only reference to `aic.workflow`
# (`WorkflowResult`, used purely as a `build_presentation` type hint, a
# function that only ever runs in `capture_amazon_snapshot.py`, never at
# request-serving time) is deferred behind `TYPE_CHECKING` specifically so
# that heavy chain (which pulls in `openai` etc.) doesn't have to be
# present here — keeping the deployment package as thin as spec.md
# requires.
#
# Not meant to be run standalone against AWS — it only produces the zip.
#
# Uses `uv pip install --python-platform x86_64-manylinux2014` (not plain
# `pip`) to force genuine Linux/manylinux wheels regardless of the host OS
# this script runs on — verified: this pulls a real
# `*.cpython-312-x86_64-linux-gnu.so` for pydantic-core, not a Windows/macOS
# build, which matters because Lambda runs Amazon Linux. Uses Python's
# stdlib `zipfile` (not the external `zip` binary) to build the archive,
# since `zip` isn't guaranteed to be present (e.g. Git Bash on Windows does
# not ship it by default).

set -euo pipefail

# Explicit, self-contained conversion for the one native-Windows-executable
# call this script makes (`python -c ...` below) — deliberately NOT relying
# on Git Bash/MSYS's automatic argument conversion, because whether that
# conversion is active depends on the CALLER's environment
# (MSYS_NO_PATHCONV), not this script's own. Found in practice: when this
# script runs standalone, auto-conversion is on and works; when invoked
# from provision_lambda.sh/release_lambda.sh (which export
# MSYS_NO_PATHCONV=1 to protect an unrelated non-path argument), the
# suppressed conversion meant python.exe received a raw POSIX-style path
# and silently wrote the zip to a different location than bash was
# checking — Windows treats a leading "/" with no drive letter as "root of
# the current drive", not as MSYS's drive-letter mapping. Converting
# explicitly here makes this script correct regardless of caller context.
native_path() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -m "$1"
  else
    printf '%s' "$1"
  fi
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-$REPO_ROOT/build/lambda}"
ZIP_PATH="${ZIP_PATH:-$REPO_ROOT/build/lambda.zip}"

echo "Building Lambda package..."
rm -rf "$BUILD_DIR" "$ZIP_PATH"
# NOTE: do not pre-create "$BUILD_DIR/src/aic/public" — `cp -r` below must be
# the one to create that final path component, otherwise (since the
# destination would already exist as a directory) it nests the source
# *inside* it instead of *as* it (src/aic/public/public/... — a real bug
# caught by actually running this script and inspecting the resulting zip).
mkdir -p "$BUILD_DIR/src/aic" "$BUILD_DIR/data"

uv pip install \
  --target "$(native_path "$BUILD_DIR")" \
  --python-platform x86_64-manylinux2014 \
  --python-version 3.12 \
  --only-binary :all: \
  --upgrade \
  --quiet \
  fastapi jinja2 python-multipart email-validator pydantic mangum boto3

cp "$REPO_ROOT/src/aic/__init__.py" "$BUILD_DIR/src/aic/__init__.py"
cp -r "$REPO_ROOT/src/aic/public" "$BUILD_DIR/src/aic/public"
cp -r "$REPO_ROOT/src/aic/domain" "$BUILD_DIR/src/aic/domain"
find "$BUILD_DIR/src/aic" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
cp "$REPO_ROOT/data/amazon_snapshot.json" "$BUILD_DIR/data/amazon_snapshot.json"

# Convert explicitly (see the native_path() comment above) rather than
# relying on ambient auto-conversion — this is what was actually silently
# broken before, not antivirus.
BUILD_DIR_NATIVE="$(native_path "$BUILD_DIR")"
ZIP_PATH_NATIVE="$(native_path "$ZIP_PATH")"

rm -f "$ZIP_PATH"
python -c "
import os
import sys
import zipfile

build_dir, zip_path = sys.argv[1], sys.argv[2]

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, _dirs, files in os.walk(build_dir):
        for name in files:
            full_path = os.path.join(root, name)
            arcname = os.path.relpath(full_path, build_dir)
            zf.write(full_path, arcname)
" "$BUILD_DIR_NATIVE" "$ZIP_PATH_NATIVE"

# Cheap, retained defensive check (not the fix itself — the path conversion
# above is): confirm the file exists with a stable, non-zero size before
# trusting it, in case anything (AV or otherwise) still touches it.
stable_checks=0
last_size=-1
zip_ok=false
for _ in $(seq 1 8); do
  if [ -f "$ZIP_PATH" ]; then
    current_size="$(wc -c < "$ZIP_PATH" | tr -d ' ')"
    if [ "$current_size" = "$last_size" ] && [ "$current_size" != "0" ]; then
      stable_checks=$((stable_checks + 1))
      if [ "$stable_checks" -ge 2 ]; then
        zip_ok=true
        break
      fi
    else
      stable_checks=0
    fi
    last_size="$current_size"
  else
    stable_checks=0
    last_size=-1
  fi
  sleep 1
done

if [ "$zip_ok" != "true" ]; then
  echo "ERROR: $ZIP_PATH did not stabilize after building." >&2
  exit 1
fi

echo "Lambda package built: $ZIP_PATH"
