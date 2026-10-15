import json
import sys
import math
import csv
import os
import ast
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

TZ_IST = ZoneInfo("Asia/Kolkata")

# ========================================================
# CONFIGURABLE SCORING WEIGHTS (Must sum to 1.0)
# ========================================================
WEIGHT_DISTANCE = 0.30
WEIGHT_CAPACITY = 0.25
WEIGHT_DIETARY = 0.20
WEIGHT_TIME_WINDOW = 0.15
WEIGHT_NEED_LEVEL = 0.10

MAX_DISTANCE_KM = 15.0 # Max radius in Bhubaneswar city
CITY_SPEED_KMH = 20.0
MINUTES_PER_KM = 60.0 / CITY_SPEED_KMH
PICKUP_BUFFER_MIN = 12.0 # Time to reach donor & load food

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

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)

def load_recipients(csv_path="data/recipients.csv"):
    recipients = []
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(os.path.dirname(__file__), "../../../", csv_path)
    
    if os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                recipients.append({
                    "id": row["id"].strip(),
                    "name": row["name"].strip(),
                    "area": row["area"].strip(),
                    "lat": float(row["lat"]),
                    "lng": float(row["lng"]),
                    "capacity_meals": int(row["capacity_meals"]),
                    "accepts": row["accepts"].lower().strip(),
                    "available_from": row["available_from"].strip(),
                    "available_until": row["available_until"].strip(),
                    "need_level": int(row["need_level"]),
                    "contact": row["contact"].strip(),
                    "notes": row["notes"].strip()
                })
    return recipients

def parse_time_str(t_str, base_date):
    """Parses '08:00' or '22:30' into an aware datetime on base_date."""
    parts = t_str.split(":")
    hr = int(parts[0])
    mn = int(parts[1]) if len(parts) > 1 else 0
    if hr >= 24: # e.g. 02:00 next day
        return datetime(base_date.year, base_date.month, base_date.day, 23, 59, 59, tzinfo=TZ_IST)
    return datetime(base_date.year, base_date.month, base_date.day, hr, mn, 0, tzinfo=TZ_IST)

def score_recipient(rec, donor_lat, donor_lng, total_meals, is_veg, now_ist, deliver_by_dt=None):
    # 1. Distance & Transit calculation
    dist = haversine(donor_lat, donor_lng, rec["lat"], rec["lng"])
    transit_mins = dist * MINUTES_PER_KM
    estimated_arrival = now_ist + timedelta(minutes=PICKUP_BUFFER_MIN + transit_mins)
    
    dist_score = max(0.0, 1.0 - (dist / MAX_DISTANCE_KM))
    
    # 2. Capacity Score
    cap = rec["capacity_meals"]
    if total_meals <= cap:
        cap_score = 1.0 - ((cap - total_meals) / (cap * 2.0))
    else:
        cap_score = max(0.1, cap / float(total_meals))
        
    # 3. Dietary Score
    if not is_veg and rec["accepts"] == "veg":
        diet_score = 0.0 # Strict reject for non-veg at vegetarian-only shelter
    else:
        diet_score = 1.0
        
    # 4. Real Time Window & Operating Hours Check
    # Parse available_from and available_until
    avail_from_dt = parse_time_str(rec["available_from"], now_ist.date())
    avail_until_dt = parse_time_str(rec["available_until"], now_ist.date())
    
    # Check if overnight shelter (e.g. 18:00 to 02:00)
    if avail_until_dt < avail_from_dt:
        if estimated_arrival.hour < 12:
            # morning after midnight
            avail_from_dt -= timedelta(days=1)
        else:
            avail_until_dt += timedelta(days=1)

    is_open = (avail_from_dt <= estimated_arrival <= avail_until_dt)
    
    if not is_open:
        # Exclude recipient: closed upon volunteer arrival
        time_score = 0.0
        time_reason = f"CLOSED upon arrival (Opens: {rec['available_from']}, Closes: {rec['available_until']}, ETA: {estimated_arrival.strftime('%H:%M')})"
    else:
        # Score by safety margin before closing time
        closing_margin_mins = (avail_until_dt - estimated_arrival).total_seconds() / 60.0
        
        # Also compare with deliver_by / food expiry if available
        if deliver_by_dt:
            food_expiry_margin = (deliver_by_dt - estimated_arrival).total_seconds() / 60.0
            margin = min(closing_margin_mins, food_expiry_margin)
        else:
            margin = closing_margin_mins
            
        if margin <= 0:
            time_score = 0.0
            time_reason = "Arrival exceeds safe delivery cutoff"
        elif margin >= 60.0:
            time_score = 1.0
            time_reason = f"Open ({round(margin)} min buffer before closing at {rec['available_until']})"
        else:
            # Scaled margin between 0 and 1
            time_score = round(margin / 60.0, 2)
            time_reason = f"Tight closing window: only {round(margin)} mins margin before {rec['available_until']}"
    
    # 5. Need Level Score (1 to 5)
    need_score = rec["need_level"] / 5.0
    
    # If closed or dietary violation, disqualified
    if diet_score == 0.0 or time_score == 0.0:
        total_score = 0.0
        is_viable = False
    else:
        is_viable = True
        total_score = (
            dist_score * WEIGHT_DISTANCE +
            cap_score * WEIGHT_CAPACITY +
            diet_score * WEIGHT_DIETARY +
            time_score * WEIGHT_TIME_WINDOW +
            need_score * WEIGHT_NEED_LEVEL
        )
    
    reason = f"{dist}km away in {rec['area']}, cap {cap} meals. {time_reason}."
    if diet_score == 0.0:
        reason += " [DISQUALIFIED: Vegetarian only shelter]."
    elif time_score == 0.0:
        reason += " [DISQUALIFIED: Shelter closed at expected arrival]."

    return {
        "recipient": rec,
        "is_viable": is_viable,
        "distance_km": dist,
        "estimated_arrival": estimated_arrival.isoformat(),
        "eta_minutes": round(PICKUP_BUFFER_MIN + transit_mins, 1),
        "score": round(total_score * 100, 1),
        "breakdown": {
            "distance": round(dist_score * 100, 1),
            "capacity": round(cap_score * 100, 1),
            "dietary": round(diet_score * 100, 1),
            "time_window": round(time_score * 100, 1),
            "need": round(need_score * 100, 1)
        },
        "reason": reason
    }

def match_recipients(intake_data, csv_path="data/recipients.csv", simulated_now=None):
    recipients = load_recipients(csv_path)
    donor_lat = intake_data.get("lat", 20.2961)
    donor_lng = intake_data.get("lng", 85.8245)
    total_meals = intake_data.get("total_quantity", 40)
    
    # Determine reference time
    if simulated_now:
        now_ist = parse_iso_dt(simulated_now)
    elif intake_data.get("intake_timestamp"):
        now_ist = parse_iso_dt(intake_data.get("intake_timestamp"))
    else:
        now_ist = datetime.now(TZ_IST)

    deliver_by_dt = parse_iso_dt(intake_data.get("effective_cutoff") or intake_data.get("expires_at"))

    # Determine if veg
    items = intake_data.get("items", [])
    is_veg = all(it.get("veg", True) for it in items)
    
    scored = []
    for r in recipients:
        s = score_recipient(r, donor_lat, donor_lng, total_meals, is_veg, now_ist, deliver_by_dt)
        if s["is_viable"]:
            scored.append(s)
            
    scored.sort(key=lambda x: x["score"], reverse=True)
    top_3 = scored[:3]
    
    # Check if batch splitting is needed (>65 meals)
    split_plan = None
    if total_meals > 65 and len(scored) >= 2:
        rec1 = scored[0]["recipient"]
        rec2 = scored[1]["recipient"]
        
        alloc1 = min(rec1["capacity_meals"], total_meals - 20)
        alloc2 = total_meals - alloc1
        
        split_plan = {
            "required": True,
            "total_batch": total_meals,
            "reason": f"Batch of {total_meals} meals exceeds capacity of single shelter. Split planned across 2 open shelters.",
            "allocations": [
                {
                    "recipient_id": rec1["id"],
                    "recipient_name": rec1["name"],
                    "area": rec1["area"],
                    "allocated_meals": alloc1,
                    "contact": rec1["contact"]
                },
                {
                    "recipient_id": rec2["id"],
                    "recipient_name": rec2["name"],
                    "area": rec2["area"],
                    "allocated_meals": alloc2,
                    "contact": rec2["contact"]
                }
            ]
        }
        
    return {
        "total_meals": total_meals,
        "is_veg": is_veg,
        "evaluated_at": now_ist.isoformat(),
        "total_recipients_evaluated": len(recipients),
        "viable_open_recipients_count": len(scored),
        "split_plan": split_plan,
        "top_matches": [
            {
                "id": m["recipient"]["id"],
                "name": m["recipient"]["name"],
                "area": m["recipient"]["area"],
                "lat": m["recipient"]["lat"],
                "lng": m["recipient"]["lng"],
                "capacity": m["recipient"]["capacity_meals"],
                "available_from": m["recipient"]["available_from"],
                "available_until": m["recipient"]["available_until"],
                "contact": m["recipient"]["contact"],
                "distance_km": m["distance_km"],
                "eta_minutes": m["eta_minutes"],
                "match_score": m["score"],
                "score_breakdown": m["breakdown"],
                "reason": m["reason"]
            }
            for m in top_3
        ]
    }

if __name__ == "__main__":
    sim_now = None
    for arg in sys.argv[1:]:
        if arg.startswith("--simulated-now="):
            sim_now = arg.split("=", 1)[1]

    clean_args = [a for a in sys.argv[1:] if not a.startswith("--simulated-now=")]
    if clean_args:
        intake_json = safe_load(clean_args[0])
    else:
        raw_in = sys.stdin.read().strip()
        intake_json = safe_load(raw_in) if raw_in else {}
        
    result = match_recipients(intake_json, simulated_now=sim_now)
    print(json.dumps(result, indent=2, ensure_ascii=False))
