#!/usr/bin/env bash
#
# deploy/release_lambda.sh — repeatable: rebuilds the Lambda package and
# updates the function code. Independent of deploy/release_static.sh
# (FR-028) and never touches DynamoDB — only `aic.public`'s code changes,
# never the tables' contents.

set -euo pipefail

# See provision_lambda.sh for why: defensive, even though this script's only
# `/`-leading argument is the zip path, already explicitly converted below.
export MSYS_NO_PATHCONV=1

AWS_REGION="${AWS_REGION:-eu-central-1}"
FUNCTION_NAME="${FUNCTION_NAME:-quorum-public}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# See provision_lambda.sh for why this conversion is needed on Git Bash/MSYS.
native_path() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -m "$1"
  else
    printf '%s' "$1"
  fi
}

# See provision_lambda.sh: `aws lambda wait function-updated` needs
# lambda:GetFunctionConfiguration, which proved unreliable to keep granted
# via IAM Identity Center in practice — poll with GetFunction instead.
wait_for_function_ready() {
  local tries=0
  while [ "$tries" -lt 60 ]; do
    local status
    status="$(aws lambda get-function --region "$AWS_REGION" --function-name "$FUNCTION_NAME" \
      --query 'Configuration.[State,LastUpdateStatus]' --output text)"
    if echo "$status" | grep -qE '^(Active|None)[[:space:]]+(Successful|None)$'; then
      return 0
    fi
    tries=$((tries + 1))
    sleep 2
  done
  echo "WARNING: function did not report ready within ~2 minutes; continuing anyway (last status: $status)" >&2
}

bash "$SCRIPT_DIR/build_lambda_package.sh"

aws lambda update-function-code \
  --region "$AWS_REGION" \
  --function-name "$FUNCTION_NAME" \
  --zip-file "fileb://$(native_path "$REPO_ROOT/build/lambda.zip")"

wait_for_function_ready

echo "Lambda function '$FUNCTION_NAME' updated. Static site and DynamoDB data are unaffected."
