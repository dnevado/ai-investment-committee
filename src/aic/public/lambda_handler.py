"""AWS Lambda entry point for the public validation application.

The only thing this module does is choose the production `Storage`
implementation and wrap the existing, unmodified `aic.public.app` FastAPI app
for Lambda — every route, template, and validation rule lives in `app.py`
exactly as it does locally; nothing here duplicates or reimplements it
(plan.md "Deployment Technical Context"; research.md Decision 7).

`create_app(storage=None)` would default to `SqliteStorage`, which does not
work in Lambda's ephemeral filesystem — this module is the one place in the
codebase that constructs `DynamoDbStorage` instead. `presentation` is left
unset so `create_app` loads the committed `data/amazon_snapshot.json` exactly
as it does locally.
"""

import os

from mangum import Mangum
from mangum.types import LambdaContext

from aic.public.app import create_app
from aic.public.storage import DynamoDbStorage

app = create_app(storage=DynamoDbStorage())

_mangum_handler = Mangum(app)

# The Function URL's AuthType is NONE (research.md Decision 7 amendment):
# CloudFront's Origin Access Control for Lambda signs origin requests with
# SigV4, but that signing requires the *viewer* request to already carry a
# precomputed x-amz-content-sha256 body-hash header — a plain HTML <form>
# POST never sends one, so every real registration/feedback submission was
# rejected with InvalidSignatureException. Instead, CloudFront is configured
# to inject this fixed secret header on every request it forwards to the
# Lambda origin (deploy/provision_cdn.sh), and this handler rejects anything
# that doesn't carry it — the standard shared-secret pattern for restricting
# a public custom origin to a single CloudFront distribution.
_ORIGIN_VERIFY_SECRET = os.environ.get("ORIGIN_VERIFY_SECRET")


def handler(event: dict, context: LambdaContext) -> dict:
    headers = event.get("headers") or {}
    if not _ORIGIN_VERIFY_SECRET or headers.get("x-quorum-origin-verify") != _ORIGIN_VERIFY_SECRET:
        return {"statusCode": 403, "body": "Forbidden"}
    return _mangum_handler(event, context)
