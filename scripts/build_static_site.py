"""Renders the public landing page to static HTML for S3/CloudFront hosting.

Only `GET /` becomes static (spec.md: S3 stores "landing page HTML, CSS, JS,
static assets" — every other route stays dynamic, served by Lambda via
`aic.public.lambda_handler`; see plan.md "Deployment Technical Context" and
research.md Decision 7).

This script renders `templates/landing.html` through a plain Jinja2
environment pointed at the same templates directory `aic.public.app` uses,
with the same `AmazonPresentation` context `GET /` passes. Verified safe:
no template in `src/aic/public/templates/` references `request` or
`url_for`, so this produces byte-identical output to what the FastAPI route
would render — nothing here is a second implementation of that rendering
logic, just the same inputs run outside a live HTTP request.

Run this whenever `data/amazon_snapshot.json` or the landing page templates/
static assets change; `deploy/release_static.sh` runs it as its first step
before syncing the output to S3.
"""

import shutil
from pathlib import Path

import jinja2

from aic.public.presentation import AmazonPresentation

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PACKAGE_DIR = _REPO_ROOT / "src" / "aic" / "public"
_TEMPLATES_DIR = _PACKAGE_DIR / "templates"
_STATIC_DIR = _PACKAGE_DIR / "static"
_SNAPSHOT_PATH = _REPO_ROOT / "data" / "amazon_snapshot.json"
_OUTPUT_DIR = _REPO_ROOT / "dist"


def build(output_dir: Path = _OUTPUT_DIR) -> None:
    presentation = AmazonPresentation.model_validate_json(
        _SNAPSHOT_PATH.read_text(encoding="utf-8")
    )

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=jinja2.select_autoescape(["html", "xml"]),
    )
    html = env.get_template("landing.html").render(presentation=presentation)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    (output_dir / "index.html").write_text(html, encoding="utf-8")
    shutil.copytree(_STATIC_DIR, output_dir / "static")


def main() -> None:
    build()
    print(f"Static site written to {_OUTPUT_DIR}")
    print(f"  {_OUTPUT_DIR / 'index.html'}")
    print(f"  {_OUTPUT_DIR / 'static'} ({len(list((_OUTPUT_DIR / 'static').iterdir()))} files)")


if __name__ == "__main__":
    main()
