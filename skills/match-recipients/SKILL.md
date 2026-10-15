---
name: match-recipients
description: "MANDATORY TRIGGER: You MUST activate this skill immediately after food safety is verified to rank, score, and select optimal welfare recipients in Bhubaneswar. NEVER hand-pick recipients without running this matching script."
---

# Hyperlocal Recipient Matcher

Ranks verified welfare recipients in Bhubaneswar using a weighted multi-factor scoring formula: distance (Haversine), capacity fit, dietary restrictions (veg/non-veg), receiving time windows, and organizational need level.

## Capabilities
- Loads verified recipient registry from `data/recipients.csv`.
- Computes Haversine distances between donor and recipient coordinates.
- Penalizes dietary mismatches (strictly enforces vegetarian shelters).
- Supports automatic **batch splitting** across 2 recipients when donations exceed single-shelter capacity (>65 meals).
- Outputs top 3 ranked matches with granular score breakdowns and one-line justifications.

## Usage
Run via Python script:

```bash
python skills/match-recipients/scripts/match.py '<intake_json>'
```

## Configurable Scoring Weights
- **Distance:** 30%
- **Capacity Fit:** 25%
- **Dietary Alignment:** 20%
- **Time Window Availability:** 15%
- **Urgent Need Level:** 10%
