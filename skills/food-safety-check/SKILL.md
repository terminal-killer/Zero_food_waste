---
name: food-safety-check
description: "MANDATORY TRIGGER: You MUST activate this skill immediately on every parsed food listing before matching recipients or routing volunteers. NEVER bypass this safety gate, and NEVER override a REJECT verdict."
---

# Food Safety & Microbial Risk Evaluator

Validates food safety using strict standards: 4-hour ambient rule, temperature retention criteria, open-plate hygiene verification, and high-risk dairy/rice handling checks.

## Capabilities
- Computes `minutes_remaining` before microbial growth threshold.
- Generates verdicts: `SAFE`, `SAFE_IF_FAST`, or `REJECT`.
- Provides explicit handling instructions for volunteers and recipients.
- Includes mandatory non-overridable legal/hygiene disclaimer.

## Usage
Run via Python script:

```bash
python skills/food-safety-check/scripts/safety_check.py '<intake_json>'
```

## Output Schema
```json
{
  "verdict": "SAFE | SAFE_IF_FAST | REJECT",
  "minutes_remaining": 120,
  "reasons": [
    "Storage verified: Kept in insulated thermal containers above 60C."
  ],
  "handling_instructions": [
    "Maintain insulated container closures during transit."
  ],
  "disclaimer": "Final sensory inspection and acceptance judgment always rests with the designated receiving welfare organization."
}
```
