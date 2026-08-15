"""Captures one validated run_investment_workflow execution for Amazon/AMZN and
writes it as a static AmazonPresentation snapshot (data/amazon_snapshot.json).

The public web app (aic.public.app) loads this file at startup and never
recomputes it per visitor — see specs/011-public-mvp-validation/research.md
Decision 2. Run this manually, occasionally, whenever the underlying dataset or
model output should be refreshed; it makes real OpenAI API calls.
"""

from pathlib import Path

from mvp_amazon_dataset import build_workflow_input

from aic.public.presentation import build_presentation
from aic.research import OpenAIProvider
from aic.settings import get_settings
from aic.workflow import run_investment_workflow

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "amazon_snapshot.json"


def main() -> None:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError(
            "AIC_OPENAI_API_KEY is not configured. Set it before capturing the "
            "Amazon snapshot."
        )

    workflow_input = build_workflow_input()
    provider = OpenAIProvider(api_key=settings.openai_api_key)

    result = run_investment_workflow(workflow_input, provider)
    presentation = build_presentation(result, workflow_input.evidence)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(presentation.model_dump_json(indent=2), encoding="utf-8")

    print("=" * 70)
    print("AMAZON SNAPSHOT CAPTURED")
    print("=" * 70)
    print(f"Company:              {presentation.company_name} ({presentation.ticker})")
    print(f"Implied value/share:  {presentation.implied_value_per_share}")
    print(f"Enterprise value:     {presentation.enterprise_value}")
    print(f"Recommendation:       {presentation.recommendation}")
    print(f"Conviction:           {presentation.conviction}")
    print(f"Evidence items:       {len(presentation.evidence)}")
    print(f"Written to:           {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
