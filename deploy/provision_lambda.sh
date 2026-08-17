#!/usr/bin/env bash
#
# deploy/provision_lambda.sh — one-time (idempotent) creation of the Lambda
# function, its least-privilege execution role, and its Function URL.
#
# Requires: deploy/provision_data.sh already run (the IAM policy below names
# the three table ARNs). AWS CLI v2, credentials with IAM/Lambda permissions.
# NOT executed or verified in the environment that authored it. Safe to
# re-run: existing role/function/Function URL are updated in place rather
# than recreated.

set -euo pipefail

# On Git Bash/MSYS, ANY argument starting with `/` passed to a native
# Windows executable (the `aws` binary) gets auto-"path-converted" — this
# silently corrupted the Lambda `PYTHONPATH=/var/task/src` environment
# variable value into `C:/Program Files/Git/var/task/src` on a real run
# against AWS (that string was never a local path; it only means anything
# inside the remote Lambda filesystem). MSYS_NO_PATHCONV disables that
# conversion for this script. The one genuine local path this script passes
# (`--zip-file fileb://...`) is already explicitly converted via
# `native_path()`/`cygpath` below, so it's unaffected either way.
export MSYS_NO_PATHCONV=1

AWS_REGION="${AWS_REGION:-eu-central-1}"
FUNCTION_NAME="${FUNCTION_NAME:-quorum-public}"
ROLE_NAME="${ROLE_NAME:-quorum-public-lambda-role}"
REGISTRATIONS_TABLE="${REGISTRATIONS_TABLE:-quorum-registrations}"
FEEDBACK_TABLE="${FEEDBACK_TABLE:-quorum-feedback-submissions}"
EVENTS_TABLE="${EVENTS_TABLE:-quorum-validation-events}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# On Git Bash/MSYS, $REPO_ROOT is POSIX-style (/c/...), which the AWS CLI's
# local-file readers (e.g. `fileb://...`) cannot resolve on Windows — found
# by actually running this against a real account, not just reading the
# script. `cygpath -m` gives the same path in a form both bash and native
# Windows tools understand; on real Linux/macOS, cygpath doesn't exist and
# the path is already native, so this passes it through unchanged.
native_path() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -m "$1"
  else
    printf '%s' "$1"
  fi
}

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

# Shared secret CloudFront injects as a custom header on every request it
# forwards to this function's Function URL (research.md Decision 7
# amendment — see provision_cdn.sh and lambda_handler.py for why: OAC/SigV4
# signing cannot work for plain HTML <form> POSTs). Generated once and
# reused across re-runs so provision_cdn.sh can read the same value; never
# committed (.gitignore).
SECRET_FILE="$SCRIPT_DIR/.origin-verify-secret"
if [ ! -f "$SECRET_FILE" ]; then
  openssl rand -hex 32 > "$SECRET_FILE"
  echo "Generated new origin-verify secret at $SECRET_FILE (also read by provision_cdn.sh)."
fi
ORIGIN_VERIFY_SECRET="$(cat "$SECRET_FILE")"

ENV_VARS="Variables={PYTHONPATH=/var/task/src,QUORUM_REGISTRATIONS_TABLE=$REGISTRATIONS_TABLE,QUORUM_FEEDBACK_TABLE=$FEEDBACK_TABLE,QUORUM_EVENTS_TABLE=$EVENTS_TABLE,ORIGIN_VERIFY_SECRET=$ORIGIN_VERIFY_SECRET}"

# `aws lambda wait function-updated`/`function-active` poll via
# lambda:GetFunctionConfiguration under the hood — a distinct action from
# lambda:GetFunction, and one that kept failing with AccessDenied in
# practice even after the provisioning policy was updated and reprovisioned
# to include it (IAM Identity Center propagation was unreliable here). Since
# the actual updates were confirmed succeeding regardless (CodeSha256
# changed on every call), poll with GetFunction instead — an action already
# proven to work — rather than depend on that other action's permission.
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

echo "== 1/5 IAM execution role =="
if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  echo "Role '$ROLE_NAME' already exists."
else
  aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]
    }'
  aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
fi

echo "== 2/5 Least-privilege DynamoDB policy (PutItem/GetItem/Query/Scan on exactly the three tables — FR-024) =="
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name quorum-public-dynamodb \
  --policy-document "$(cat <<JSON
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan"],
    "Resource": [
      "arn:aws:dynamodb:$AWS_REGION:$ACCOUNT_ID:table/$REGISTRATIONS_TABLE",
      "arn:aws:dynamodb:$AWS_REGION:$ACCOUNT_ID:table/$FEEDBACK_TABLE",
      "arn:aws:dynamodb:$AWS_REGION:$ACCOUNT_ID:table/$EVENTS_TABLE"
    ]
  }]
}
JSON
)"

if aws iam get-role --role-name "$ROLE_NAME" --query 'Role.CreateDate' --output text \
     | grep -q "$(date -u +%Y-%m-%d)"; then
  echo "Waiting for IAM role propagation (new role)..."
  sleep 10
fi

echo "== 3/5 Package + Lambda function =="
bash "$SCRIPT_DIR/build_lambda_package.sh"
ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"
ZIP_NATIVE_PATH="$(native_path "$REPO_ROOT/build/lambda.zip")"

if aws lambda get-function --region "$AWS_REGION" --function-name "$FUNCTION_NAME" >/dev/null 2>&1; then
  echo "Function '$FUNCTION_NAME' already exists — updating code and configuration."
  aws lambda update-function-code \
    --region "$AWS_REGION" \
    --function-name "$FUNCTION_NAME" \
    --zip-file "fileb://$ZIP_NATIVE_PATH"
  wait_for_function_ready
  aws lambda update-function-configuration \
    --region "$AWS_REGION" \
    --function-name "$FUNCTION_NAME" \
    --environment "$ENV_VARS"
  wait_for_function_ready
else
  aws lambda create-function \
    --region "$AWS_REGION" \
    --function-name "$FUNCTION_NAME" \
    --runtime python3.12 \
    --architectures x86_64 \
    --role "$ROLE_ARN" \
    --handler aic.public.lambda_handler.handler \
    --zip-file "fileb://$ZIP_NATIVE_PATH" \
    --timeout 15 \
    --memory-size 256 \
    --environment "$ENV_VARS"
  wait_for_function_ready
fi

echo "== 4/5 Function URL (AuthType NONE — access is restricted by the shared-secret header check in lambda_handler.py, not IAM) =="
if aws lambda get-function-url-config --region "$AWS_REGION" --function-name "$FUNCTION_NAME" >/dev/null 2>&1; then
  CURRENT_AUTH_TYPE="$(aws lambda get-function-url-config --region "$AWS_REGION" --function-name "$FUNCTION_NAME" --query AuthType --output text)"
  if [ "$CURRENT_AUTH_TYPE" = "NONE" ]; then
    echo "Function URL already configured with AuthType NONE."
  else
    echo "Migrating Function URL from AuthType $CURRENT_AUTH_TYPE to NONE."
    aws lambda update-function-url-config \
      --region "$AWS_REGION" \
      --function-name "$FUNCTION_NAME" \
      --auth-type NONE
  fi
else
  aws lambda create-function-url-config \
    --region "$AWS_REGION" \
    --function-name "$FUNCTION_NAME" \
    --auth-type NONE
fi

# AuthType NONE additionally requires an explicit resource-policy grant for
# public invocation — the console does this implicitly, the CLI does not.
aws lambda add-permission \
  --region "$AWS_REGION" \
  --function-name "$FUNCTION_NAME" \
  --statement-id FunctionURLAllowPublicAccess \
  --action lambda:InvokeFunctionUrl \
  --principal "*" \
  --function-url-auth-type NONE \
  >/dev/null 2>&1 || echo "(permission likely already granted — safe to ignore if so)"

echo "== 5/5 Done =="
FUNCTION_URL="$(aws lambda get-function-url-config --region "$AWS_REGION" --function-name "$FUNCTION_NAME" --query FunctionUrl --output text)"
FUNCTION_ARN="$(aws lambda get-function --region "$AWS_REGION" --function-name "$FUNCTION_NAME" --query 'Configuration.FunctionArn' --output text)"

echo "Function ARN: $FUNCTION_ARN"
echo "Function URL: $FUNCTION_URL"
echo "Next: ./deploy/provision_cdn.sh (needs this Function URL as the Lambda origin)"
