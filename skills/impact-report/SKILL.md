---
name: impact-report
description: "MANDATORY TRIGGER: You MUST activate this skill immediately after successful food delivery planning to compute carbon offset, diverted food mass, and economic value, and log transactions to the immutable ledger."
---

# Environmental & Social Impact Quantifier

Calculates real-world sustainability and economic metrics for each rescued food batch and maintains the running cumulative audit ledger in `data/ledger.csv`.

## Editable Scientific Assumptions
- **1 Meal Packet** = `0.40 kg` food mass.
- **1 kg Food Waste Diverted** = `2.50 kg CO2e` avoided (methane landfill diversion factor).
- **1 Meal Packet** = `Rs 60.00` estimated economic replacement value.

## Capabilities
- Computes single-donation and cumulative lifetime impact metrics.
- Logs full transaction trails (listing ID, donor, area, recipients, volunteer, status) to `data/ledger.csv`.
- Generates auditor-ready summaries for corporate ESG and municipal reporting.

## Usage
Run via Python script:

```bash
python skills/impact-report/scripts/impact.py '<payload_json>'
```
