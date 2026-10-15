---
name: surplus-intake
description: "MANDATORY TRIGGER: You MUST activate this skill immediately whenever any plain text, WhatsApp message, voice transcript, or description of surplus food in Bhubaneswar is submitted. Do NOT manually extract food details; delegate parsing strictly to this skill."
---

# Surplus Food Intake Parser

Extracts messy, unstructured surplus food donation reports into standardized structured JSON.

## Capabilities
- Parses donor details, location/coordinates in Bhubaneswar, item breakdowns, veg/non-veg status, quantities, cooking time, expiry time, and phone numbers.
- Checks completeness and issues **strictly ONE clarifying question** only if essential fields (quantity, location, or expiry) are missing.
- Detects storage conditions (hot insulated, ambient, chilled, open leftovers).

## Usage
Run the deterministic intake parser:

```bash
python skills/surplus-intake/scripts/surplus_intake.py "<raw_surplus_text>"
```

## Output Schema
```json
{
  "donor_name": "string",
  "donor_type": "string",
  "area": "string",
  "lat": 20.3550,
  "lng": 85.8180,
  "items": [{"name": "veg biryani", "qty": 40, "unit": "packets", "veg": true}],
  "total_quantity": 40,
  "storage_condition": "hot_insulated | ambient | chilled | open_leftover",
  "cooked_at": "6:30 pm",
  "expires_at": "10:30 pm",
  "contact": "9861122334",
  "clarifying_question": null
}
```
