---
name: pickup-plan
description: "MANDATORY TRIGGER: You MUST activate this skill immediately when a food safety verdict is SAFE or SAFE_IF_FAST and recipients are matched. It selects the nearest volunteer and computes the exact pickup and drop route with ETA."
---

# Hyperlocal Pickup & Route Planner

Assigns the nearest available volunteer from `data/volunteers.csv` and builds an optimal pickup-and-drop route across Bhubaneswar using nearest-neighbor navigation at 20 km/h city transit speed.

## Capabilities
- Selects best-suited vehicle type (bike vs auto) based on batch size.
- Calculates leg distances, driving durations, and handling intervals (10 min pickup, 5 min drop).
- Supports single-stop deliveries as well as multi-stop split distributions.
- **Strict Time-Window Gate:** Automatically rejects the plan if total ETA exceeds `minutes_remaining` to prevent spoiled food delivery.

## Usage
Run via Python script:

```bash
python skills/pickup-plan/scripts/route.py '<payload_json>'
```

## Constraints
- Assumed city traffic speed: 20 km/h (3.0 mins/km).
- Handling time: 10 mins pickup, 5 mins dropoff.
- Reject verdict issued if `total_eta_minutes > minutes_remaining`.
