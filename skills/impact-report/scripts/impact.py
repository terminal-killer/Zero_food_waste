import json
import sys
import csv
import os
import ast
from datetime import datetime

# ========================================================
# IMPACT QUANTIFICATION CONSTANTS (Documented & Editable)
# ========================================================
KG_FOOD_PER_MEAL = 0.40         # 1 meal packet = 0.4 kg food
CO2E_AVOIDED_PER_KG_FOOD = 2.50 # 1 kg avoided landfill food waste = 2.5 kg CO2e avoided
INR_VALUE_PER_MEAL = 60.0       # 1 meal packet = Rs 60 economic replacement value

def safe_load(raw):
    try:
        return json.loads(raw)
    except Exception:
        try:
            return ast.literal_eval(raw)
        except Exception:
            return {}

def compute_impact(payload, ledger_path="data/ledger.csv", record_to_ledger=True):
    intake = payload.get("intake", {})
    safety = payload.get("safety", {})
    pickup = payload.get("pickup", {})
    
    if safety.get("verdict") == "REJECT" or pickup.get("status", "").startswith("REJECT"):
        return {
            "status": "NO_IMPACT",
            "reason": "Listing was rejected or unsafe. Zero food diverted.",
            "this_listing": {
                "meals_saved": 0,
                "kg_diverted": 0.0,
                "co2e_avoided_kg": 0.0,
                "economic_value_inr": 0.0
            },
            "cumulative": get_cumulative_stats(ledger_path)
        }

    total_meals = intake.get("total_quantity", 0)
    kg_diverted = round(total_meals * KG_FOOD_PER_MEAL, 2)
    co2e_avoided_kg = round(kg_diverted * CO2E_AVOIDED_PER_KG_FOOD, 2)
    economic_value_inr = round(total_meals * INR_VALUE_PER_MEAL, 2)
    
    donor_name = intake.get("donor_name", "Anonymous Donor")
    donor_area = intake.get("area", "Bhubaneswar")
    destinations = pickup.get("destinations", [])
    recipients_served = ", ".join([d["name"] for d in destinations])
    vol = pickup.get("assigned_volunteer", {})
    volunteer_name = vol.get("name", "Volunteer")
    
    listing_id = f"OD-{datetime.now().strftime('%m%d%H%M')}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if record_to_ledger:
        if not os.path.isabs(ledger_path):
            ledger_path = os.path.join(os.path.dirname(__file__), "../../../", ledger_path)
        
        file_exists = os.path.exists(ledger_path)
        with open(ledger_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "listing_id", "timestamp", "donor_name", "area", "total_meals",
                    "kg_diverted", "co2e_avoided_kg", "economic_value_inr",
                    "recipients_served", "volunteer_name", "status"
                ])
            writer.writerow([
                listing_id, now_str, donor_name, donor_area, total_meals,
                kg_diverted, co2e_avoided_kg, economic_value_inr,
                recipients_served, volunteer_name, "COMPLETED"
            ])

    cumulative = get_cumulative_stats(ledger_path)

    return {
        "status": "SUCCESS",
        "this_listing": {
            "listing_id": listing_id,
            "meals_saved": total_meals,
            "kg_diverted": kg_diverted,
            "co2e_avoided_kg": co2e_avoided_kg,
            "economic_value_inr": economic_value_inr,
            "donor": f"{donor_name} ({donor_area})",
            "recipients_served": [d["name"] for d in destinations],
            "volunteer": volunteer_name
        },
        "assumptions": {
            "kg_food_per_meal": KG_FOOD_PER_MEAL,
            "co2e_per_kg_food": CO2E_AVOIDED_PER_KG_FOOD,
            "inr_value_per_meal": INR_VALUE_PER_MEAL
        },
        "cumulative": cumulative
    }

def get_cumulative_stats(ledger_path="data/ledger.csv"):
    if not os.path.isabs(ledger_path):
        ledger_path = os.path.join(os.path.dirname(__file__), "../../../", ledger_path)
    
    total_meals = 0
    total_kg = 0.0
    total_co2e = 0.0
    total_inr = 0.0
    donors = set()
    recipients = set()
    completed_runs = 0

    if os.path.exists(ledger_path):
        with open(ledger_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("status") == "COMPLETED":
                    completed_runs += 1
                    total_meals += int(float(row.get("total_meals", 0)))
                    total_kg += float(row.get("kg_diverted", 0))
                    total_co2e += float(row.get("co2e_avoided_kg", 0))
                    total_inr += float(row.get("economic_value_inr", 0))
                    donors.add(row.get("donor_name"))
                    for r in row.get("recipients_served", "").split(","):
                        if r.strip():
                            recipients.add(r.strip())

    return {
        "total_dispatches": completed_runs,
        "total_meals_saved": total_meals,
        "total_kg_diverted": round(total_kg, 2),
        "total_co2e_avoided_kg": round(total_co2e, 2),
        "total_economic_value_inr": round(total_inr, 2),
        "unique_donors_served": len(donors),
        "unique_recipients_served": len(recipients)
    }

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "--dry-run":
        data = safe_load(sys.argv[1])
    else:
        raw_in = sys.stdin.read().strip()
        data = safe_load(raw_in) if raw_in else {}
    record = "--dry-run" not in sys.argv
    result = compute_impact(data, record_to_ledger=record)
    print(json.dumps(result, indent=2))
