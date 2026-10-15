import json
import sys
import os
import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
RUNS_DIR = os.path.join(BASE_DIR, "runs")
os.makedirs(RUNS_DIR, exist_ok=True)

# Add skill paths
sys.path.append(os.path.join(BASE_DIR, "skills", "surplus-intake", "scripts"))
sys.path.append(os.path.join(BASE_DIR, "skills", "food-safety-check", "scripts"))
sys.path.append(os.path.join(BASE_DIR, "skills", "match-recipients", "scripts"))
sys.path.append(os.path.join(BASE_DIR, "skills", "pickup-plan", "scripts"))
sys.path.append(os.path.join(BASE_DIR, "skills", "notify-message", "scripts"))
sys.path.append(os.path.join(BASE_DIR, "skills", "impact-report", "scripts"))

from surplus_intake import parse_surplus_intake, load_areas, match_area, parse_time_point
from safety_check import check_food_safety
from match import match_recipients
from route import generate_pickup_plan
from generate_messages import build_messages
from impact import compute_impact

TZ_IST = ZoneInfo("Asia/Kolkata")

def execute_pipeline(raw_text, run_id=None, simulated_now=None, override_json=None):
    if not run_id:
        run_id = f"run_{int(time.time() * 1000)}"

    now_ist = datetime.now(TZ_IST)
    stages = []
    
    # -------------------------------------------------------------------------
    # STAGE 1: Surplus Intake
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    intake = parse_surplus_intake(raw_text, simulated_now=simulated_now)
    
    # Apply override_json if provided (e.g. from /api/annasetu/run/:id/answer or user edits)
    if override_json:
        try:
            overrides = json.loads(override_json) if isinstance(override_json, str) else override_json
            if isinstance(overrides, dict):
                # Handle direct field overrides
                for k, v in overrides.items():
                    if k == "quantity" or k == "total_quantity":
                        intake["total_quantity"] = int(v)
                        if "items" in intake and intake["items"]:
                            intake["items"][0]["qty"] = int(v)
                        else:
                            intake["items"] = [{"name": "Meal Packets", "qty": int(v), "unit": "packets", "veg": True}]
                    elif k == "area":
                        intake["area"] = str(v)
                        areas = load_areas()
                        matched_obj, _, _ = match_area(str(v), areas)
                        if matched_obj:
                            intake["lat"] = matched_obj["lat"]
                            intake["lng"] = matched_obj["lng"]
                    elif k in ["cooked_at", "expires_at", "donor_name", "donor_type", "contact"]:
                        intake[k] = v

                # Handle raw answer string e.g. "40 packets" or "Nayapalli"
                if "answer" in overrides and str(overrides["answer"]).strip():
                    ans_text = str(overrides["answer"]).strip()
                    ans_parse = parse_surplus_intake(ans_text + " " + raw_text, simulated_now=simulated_now)
                    for f in ["total_quantity", "cooked_at", "expires_at", "area", "lat", "lng", "items"]:
                        if ans_parse.get(f):
                            intake[f] = ans_parse[f]

                # Re-check required fields
                missing = []
                if not intake.get("total_quantity"):
                    missing.append("quantity of food packets")
                if not intake.get("cooked_at"):
                    missing.append("time when food was cooked")
                if not intake.get("area"):
                    missing.append("pickup location or neighborhood in Bhubaneswar")

                intake["missing_fields"] = missing
                if not missing:
                    intake["status"] = "VALID"
        except Exception as e:
            sys.stderr.write(f"Error applying override_json: {e}\n")

    d1 = round((time.perf_counter() - t0) * 1000, 2)
    intake_status = intake.get("status", "VALID")
    stages.append({
        "id": "intake",
        "name": "Surplus Intake & Parsing",
        "status": intake_status,
        "duration_ms": d1
    })

    # Early exit on NEEDS_INFO
    if intake_status == "NEEDS_INFO":
        result = {
            "run_id": run_id,
            "timestamp": now_ist.isoformat(),
            "status": "NEEDS_INFO",
            "stages": stages,
            "intake": intake,
            "safety": None,
            "match": None,
            "pickup": None,
            "notify": None,
            "impact": None
        }
        save_run(run_id, result)
        return result

    # -------------------------------------------------------------------------
    # STAGE 2: Food Safety Check
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    safety = check_food_safety(intake, simulated_now=simulated_now)
    d2 = round((time.perf_counter() - t0) * 1000, 2)
    verdict = safety.get("verdict", "SAFE")
    stages.append({
        "id": "safety",
        "name": "Microbial Food Safety Audit",
        "status": verdict,
        "duration_ms": d2
    })

    # Early exit on REJECT
    if verdict == "REJECT":
        result = {
            "run_id": run_id,
            "timestamp": now_ist.isoformat(),
            "status": "REJECT",
            "stages": stages,
            "intake": intake,
            "safety": safety,
            "match": None,
            "pickup": None,
            "notify": None,
            "impact": None
        }
        save_run(run_id, result)
        return result

    # -------------------------------------------------------------------------
    # STAGE 3: Recipient Matching
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    match = match_recipients(intake, simulated_now=simulated_now)
    d3 = round((time.perf_counter() - t0) * 1000, 2)
    stages.append({
        "id": "match",
        "name": "Hyperlocal Recipient Matching",
        "status": "MATCHED",
        "duration_ms": d3
    })

    # -------------------------------------------------------------------------
    # STAGE 4: Volunteer Pickup & Routing
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    pickup_payload = {"intake": intake, "safety": safety, "matches": match}
    pickup = generate_pickup_plan(pickup_payload)
    d4 = round((time.perf_counter() - t0) * 1000, 2)
    stages.append({
        "id": "pickup",
        "name": "Volunteer Route Optimization",
        "status": pickup.get("status", "CONFIRMED"),
        "duration_ms": d4
    })

    # -------------------------------------------------------------------------
    # STAGE 5: Ready-to-Send Notifications
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    notify_payload = {"intake": intake, "safety": safety, "pickup": pickup}
    notify = build_messages(notify_payload)
    d5 = round((time.perf_counter() - t0) * 1000, 2)
    stages.append({
        "id": "notify",
        "name": "Multi-Lingual Notification Dispatch",
        "status": "GENERATED",
        "duration_ms": d5
    })

    # -------------------------------------------------------------------------
    # STAGE 6: Impact Quantification
    # -------------------------------------------------------------------------
    t0 = time.perf_counter()
    impact_payload = {"intake": intake, "safety": safety, "pickup": pickup}
    # record_to_ledger=False because server.js appends to ledger safely
    impact = compute_impact(impact_payload, record_to_ledger=False)
    d6 = round((time.perf_counter() - t0) * 1000, 2)
    stages.append({
        "id": "impact",
        "name": "Environmental & Economic Impact",
        "status": "CALCULATED",
        "duration_ms": d6
    })

    result = {
        "run_id": run_id,
        "timestamp": now_ist.isoformat(),
        "status": verdict,  # "SAFE" or "SAFE_IF_FAST"
        "stages": stages,
        "intake": intake,
        "safety": safety,
        "match": match,
        "pickup": pickup,
        "notify": notify,
        "impact": impact
    }
    save_run(run_id, result)
    return result

def save_run(run_id, data):
    try:
        run_file = os.path.join(RUNS_DIR, f"{run_id}.json")
        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        sys.stderr.write(f"Error saving run file: {e}\n")

if __name__ == "__main__":
    run_id_arg = None
    text_arg = None
    sim_now_arg = None
    override_arg = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--run-id="):
            run_id_arg = arg.split("=", 1)[1]
        elif arg == "--run-id" and i + 1 < len(args):
            run_id_arg = args[i+1]
            i += 1
        elif arg.startswith("--text="):
            text_arg = arg.split("=", 1)[1]
        elif arg == "--text" and i + 1 < len(args):
            text_arg = args[i+1]
            i += 1
        elif arg.startswith("--simulated-now="):
            sim_now_arg = arg.split("=", 1)[1]
        elif arg == "--simulated-now" and i + 1 < len(args):
            sim_now_arg = args[i+1]
            i += 1
        elif arg.startswith("--override-json="):
            override_arg = arg.split("=", 1)[1]
        elif arg == "--override-json" and i + 1 < len(args):
            override_arg = args[i+1]
            i += 1
        else:
            if not text_arg and not arg.startswith("--"):
                text_arg = arg
        i += 1

    if not text_arg:
        text_arg = "Surplus food donation in Bhubaneswar"

    res = execute_pipeline(text_arg, run_id=run_id_arg, simulated_now=sim_now_arg, override_json=override_arg)
    # Output strictly ONLY valid JSON to stdout
    print(json.dumps(res, indent=2, ensure_ascii=False))
