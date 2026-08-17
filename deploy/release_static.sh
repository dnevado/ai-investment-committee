#!/usr/bin/env bash
#
# deploy/release_static.sh — repeatable: rebuilds the static landing page,
# syncs it to S3, and invalidates the CloudFront cache. Independent of
# deploy/release_lambda.sh (FR-028) and never touches DynamoDB.

set -euo pipefail

# See provision_lambda.sh for the full explanation: Git Bash/MSYS
# auto-"path-converts" `/...`-shaped argument substrings passed to a native
# Windows exe — wanted for the real local `dist/` path below (handled
# explicitly via native_path()/cygpath instead of relying on the automatic
# conversion, since we can't be sure it fires exactly where needed), but
# actively harmful for the CloudFront invalidation `--paths` values
# ("/", "/index.html", "/static/*"), which are not local paths at all.
export MSYS_NO_PATHCONV=1
native_path() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -m "$1"
  else
    printf '%s' "$1"
  fi
}

AWS_REGION="${AWS_REGION:-eu-central-1}"
BUCKET_NAME="${BUCKET_NAME:?BUCKET_NAME is required, e.g. BUCKET_NAME=quorum-public-site ./deploy/release_static.sh}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== 1/3 Building the static site =="
(cd "$REPO_ROOT" && uv run python scripts/build_static_site.py)

echo "== 2/3 Syncing to S3 (private bucket, read via CloudFront OAC only) =="
aws s3 sync "$(native_path "$REPO_ROOT/dist")/" "s3://$BUCKET_NAME/" --region "$AWS_REGION" --delete

echo "== 3/3 Invalidating the CloudFront cache =="
DIST_ID="$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Comment=='quorum-public'].Id | [0]" --output text)"
if [ "$DIST_ID" = "None" ] || [ -z "$DIST_ID" ]; then
  echo "No distribution found (Comment='quorum-public') — run deploy/provision_cdn.sh first." >&2
  exit 1
fi
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/" "/index.html" "/static/*" >/dev/null

echo "Static site released. Registration/feedback/events/metrics (Lambda) are unaffected."
