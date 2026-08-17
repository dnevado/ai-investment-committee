#!/usr/bin/env bash
#
# deploy/provision_data.sh — one-time (idempotent) creation of the three
# DynamoDB tables the production application uses (data-model.md "Deployment
# revision, second"). On-Demand capacity mode throughout (spec.md's explicit
# preference for a low-volume, irregular validation workload).
#
# Requires: AWS CLI v2, credentials configured with DynamoDB permissions.
# NOT executed or verified in the environment that authored it — no AWS
# credentials are available there. Safe to re-run.

set -euo pipefail

# See provision_lambda.sh for why: Git Bash/MSYS auto-"path-converts"
# `/...`-shaped substrings in arguments passed to a native Windows exe —
# demonstrated in practice to corrupt unrelated string values. Harmless to
# set defensively here even though this script's arguments are less likely
# to trigger it.
export MSYS_NO_PATHCONV=1

AWS_REGION="${AWS_REGION:-eu-central-1}"
REGISTRATIONS_TABLE="${REGISTRATIONS_TABLE:-quorum-registrations}"
FEEDBACK_TABLE="${FEEDBACK_TABLE:-quorum-feedback-submissions}"
EVENTS_TABLE="${EVENTS_TABLE:-quorum-validation-events}"

aws_ddb() { aws dynamodb --region "$AWS_REGION" "$@"; }

create_table_if_missing() {
  local table_name="$1"
  local key_name="$2"

  if aws_ddb describe-table --table-name "$table_name" >/dev/null 2>&1; then
    echo "Table '$table_name' already exists — skipping."
    return
  fi

  aws_ddb create-table \
    --table-name "$table_name" \
    --attribute-definitions "AttributeName=$key_name,AttributeType=S" \
    --key-schema "AttributeName=$key_name,KeyType=HASH" \
    --billing-mode PAY_PER_REQUEST

  echo "Waiting for '$table_name' to become active..."
  aws_ddb wait table-exists --table-name "$table_name"
  echo "Table '$table_name' ready (partition key: $key_name)."
}

echo "== 1/3 registrations (partition key: email_normalized) =="
create_table_if_missing "$REGISTRATIONS_TABLE" "email_normalized"

echo "== 2/3 feedback_submissions (partition key: feedback_id) =="
create_table_if_missing "$FEEDBACK_TABLE" "feedback_id"

echo "== 3/3 validation_events (partition key: event_id) =="
create_table_if_missing "$EVENTS_TABLE" "event_id"

echo
echo "DynamoDB tables ready:"
echo "  $REGISTRATIONS_TABLE"
echo "  $FEEDBACK_TABLE"
echo "  $EVENTS_TABLE"
echo "Next: ./deploy/provision_lambda.sh"
