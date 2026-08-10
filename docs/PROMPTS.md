# AI Investment Committee — Prompt Architecture

Version: 0.1

## Purpose

AIC uses specialized agents with distinct responsibilities:

Research → Bull/Bear → Valuation assumptions → Committee Chair.

The system is not a collection of generic summaries. Each agent has a different epistemic role.

## Agent responsibilities

| Agent | Question |
|---|---|
| Research | What do we actually know? |
| Bull | What could make this investment outperform expectations? |
| Bear | What could make the thesis wrong? |
| Valuation | What assumptions justify different values? |
| Committee | Given evidence, contradiction and valuation, what should we believe? |

## Global rules

1. Never fabricate facts.
2. Classify material claims as FACT, CALCULATION, ASSUMPTION, INTERPRETATION or OPINION.
3. Preserve source IDs where available.
4. Do not issue BUY/WATCH/AVOID before the Committee.
5. Focus on material information.
6. Expose uncertainty.
7. Distinguish company quality from investment attractiveness at the current price.
8. Prompts are production code and require evaluation when changed.
