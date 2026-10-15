---
name: annasetu-orchestrator
description: "MANDATORY MASTER TRIGGER: You MUST activate this skill whenever a surplus food listing, text report, or event leftover donation is submitted. This master coordinator chains intake -> safety-check -> match-recipients -> pickup-plan -> notify-message -> impact-report into a unified automated pipeline."
---

# AnnaSetu Master Pipeline Orchestrator

End-to-end autonomous surplus food redistribution pipeline for Bhubaneswar, India.

## Pipeline Workflow
1. **`surplus-intake`**: Extracts structured JSON from freeform text, transcripts, or notes.
2. **`food-safety-check`**: Validates the 4-hour ambient rule and sanitary criteria (**halts pipeline early on REJECT**).
3. **`match-recipients`**: Ranks top welfare shelters using weighted criteria and plans batch splits when needed (>65 meals).
4. **`pickup-plan`**: Assigns nearest volunteer, computes route itinerary at 20 km/h, and enforces safety window bounds.
5. **`notify-message`**: Formats copy-paste WhatsApp notifications in English, Hindi, and Odia.
6. **`impact-report`**: Calculates meals saved, kg diverted, CO2e offset, and INR community value, updating `data/ledger.csv`.

## Usage
Run directly from terminal or pass custom surplus text:

```bash
python skills/annasetu-orchestrator/scripts/orchestrate.py "<plain_text_food_listing>"
```
