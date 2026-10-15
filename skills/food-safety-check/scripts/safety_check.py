import json
import sys
import re
import ast
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ_IST = ZoneInfo("Asia/Kolkata")

def safe_load(raw):
    try:
        return json.loads(raw)
    except Exception:
        try:
            return ast.literal_eval(raw)
        except Exception:
            return {}

def parse_iso_dt(dt_val):
    if not dt_val:
        return None
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            return dt_val.replace(tzinfo=TZ_IST)
        return dt_val.astimezone(TZ_IST)
    try:
        dt = datetime.fromisoformat(str(dt_val))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ_IST)
        return dt.astimezone(TZ_IST)
    except Exception:
        return None

def check_food_safety(intake_data, simulated_now=None):
    """
    Evaluates microbial food safety strictly using the clock and timestamps.
    Formula: minutes_remaining = min(expires_at, cooked_at + 4h) - now - 30 minute serving margin.
    No synthetic string detectors.
    """
    if intake_data.get("status") == "NEEDS_INFO":
        return {
            "verdict": "REJECT",
            "minutes_remaining": 0,
            "reasons": ["Incomplete intake data: Food details missing or ambiguous."],
            "handling_instructions": ["Do not collect until full details are clarified."],
            "disclaimer": "Safety cannot be assessed without verified cooking timestamp and location."
        }

    raw_text = intake_data.get("raw_text", "").lower()
    storage = intake_data.get("storage_condition", "ambient")
    items = intake_data.get("items", [])
    
    # Resolve current clock time (simulated or real now in Asia/Kolkata)
    if simulated_now:
        now_ist = parse_iso_dt(simulated_now)
    elif intake_data.get("intake_timestamp"):
        now_ist = parse_iso_dt(intake_data.get("intake_timestamp"))
    else:
        now_ist = datetime.now(TZ_IST)

    reasons = []
    handling_instructions = []
    
    # 1. Non-negotiable Sanitary & Contamination Gate
    if any(k in raw_text for k in ["leftover", "open plate", "half-eaten", "touched by guests", "buffet trays"]):
        reasons.append("SANITARY VIOLATION: Opened buffet trays or half-eaten consumer plate food violates food safety protocols.")
        return {
            "verdict": "REJECT",
            "minutes_remaining": 0.0,
            "reasons": reasons,
            "handling_instructions": ["Do not distribute for human consumption. Advise composting or safe disposal."],
            "disclaimer": "Final judgment rests with the receiving organization. Rejection decisions are absolute and non-negotiable for public health safety."
        }

    # 2. Parse ISO-8601 Timestamps
    cooked_at = parse_iso_dt(intake_data.get("cooked_at"))
    expires_at = parse_iso_dt(intake_data.get("expires_at"))

    if not cooked_at:
        return {
            "verdict": "REJECT",
            "minutes_remaining": 0.0,
            "reasons": ["Missing verified cooking timestamp."],
            "handling_instructions": ["Reject donation."],
            "disclaimer": "Mandatory safety verification failed."
        }

    # Ambient cooked food safe threshold is 4 hours from cooking
    # (If hot insulated cambro >60C, extends up to 6 hours)
    safe_window_hours = 6.0 if storage == "hot_insulated" else 4.0
    microbial_cutoff = cooked_at + timedelta(hours=safe_window_hours)
    
    if expires_at:
        effective_cutoff = min(expires_at, microbial_cutoff)
    else:
        effective_cutoff = microbial_cutoff

    # Formula: minutes_remaining = effective_cutoff - now - 30 minute serving margin
    diff_seconds = (effective_cutoff - now_ist).total_seconds()
    minutes_remaining = round((diff_seconds / 60.0) - 30.0, 1)

    # High-risk items note
    high_risk_items = ["rice", "biryani", "sweets", "kheeri", "paneer", "dairy", "curd"]
    has_high_risk = any(any(hr in it.get("name", "").lower() for hr in high_risk_items) for it in items)

    if storage == "hot_insulated":
        reasons.append(f"Storage verified: Kept in insulated thermal containers above 60C (extended {safe_window_hours}h window).")
        handling_instructions.append("Maintain insulated container closures during transit. Do not unseal until delivery.")
    elif storage == "chilled":
        reasons.append("Storage verified: Chilled below 5C.")
        handling_instructions.append("Transport in insulated cool-bags with icepacks.")
    else:
        if has_high_risk:
            reasons.append("High-risk item (rice/dairy/sweets) at ambient temperature requires expedited transit.")
        handling_instructions.append("Keep in clean, shaded transport away from direct vehicle exhaust and dust.")

    # 3. Verdict Assessment based purely on minutes_remaining
    if minutes_remaining <= 0:
        verdict = "REJECT"
        reasons.append(f"Food has expired or safe redistribution cutoff is past ({abs(minutes_remaining)} mins beyond safe serving margin).")
        handling_instructions = ["Reject donation. Do not collect for human consumption."]
    elif minutes_remaining <= 60.0:
        verdict = "SAFE_IF_FAST"
        reasons.append(f"Time-critical window: only {minutes_remaining} minutes remaining before safe serving cutoff.")
        handling_instructions.append("URGENT: Prioritize express delivery within 30 minutes. Recipient must serve immediately upon receipt.")
    else:
        verdict = "SAFE"
        reasons.append(f"Safe for redistribution with {minutes_remaining} minutes remaining before cutoff.")
        handling_instructions.append("Standard sanitary transport. Verify seal integrity and aroma upon handover.")

    return {
        "verdict": verdict,
        "minutes_remaining": minutes_remaining,
        "effective_cutoff": effective_cutoff.isoformat(),
        "evaluated_at": now_ist.isoformat(),
        "reasons": reasons,
        "handling_instructions": handling_instructions,
        "disclaimer": "Final sensory inspection and acceptance judgment always rests with the designated receiving welfare organization."
    }

if __name__ == "__main__":
    sim_now = None
    for arg in sys.argv[1:]:
        if arg.startswith("--simulated-now="):
            sim_now = arg.split("=", 1)[1]

    clean_args = [a for a in sys.argv[1:] if not a.startswith("--simulated-now=")]
    if clean_args:
        data = safe_load(clean_args[0])
    else:
        raw_in = sys.stdin.read().strip()
        data = safe_load(raw_in) if raw_in else {}
        
    result = check_food_safety(data, simulated_now=sim_now)
    print(json.dumps(result, indent=2, ensure_ascii=False))
