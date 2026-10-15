import json
import sys
import math
import csv
import os
import ast

def safe_load(raw):
    try:
        return json.loads(raw)
    except Exception:
        try:
            return ast.literal_eval(raw)
        except Exception:
            return {}

CITY_SPEED_KMH = 20.0 # Standard city speed in Bhubaneswar
MINUTES_PER_KM = 60.0 / CITY_SPEED_KMH # 3.0 minutes per km
PICKUP_HANDLING_MIN = 10.0
DROPOFF_HANDLING_MIN = 5.0

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)

def load_volunteers(csv_path="data/volunteers.csv"):
    volunteers = []
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(os.path.dirname(__file__), "../../../", csv_path)
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            volunteers.append({
                "id": row["id"],
                "name": row["name"],
                "area": row["area"],
                "lat": float(row["lat"]),
                "lng": float(row["lng"]),
                "vehicle": row["vehicle"],
                "capacity_packets": int(row["capacity_packets"]),
                "status": row["status"].strip().upper(),
                "contact": row["contact"]
            })
    return volunteers

def generate_pickup_plan(payload, volunteers_csv="data/volunteers.csv"):
    intake = payload.get("intake", {})
    safety = payload.get("safety", {})
    match_data = payload.get("matches", {})
    
    donor_lat = intake.get("lat", 20.2961)
    donor_lng = intake.get("lng", 85.8245)
    donor_name = intake.get("donor_name", "Donor")
    donor_area = intake.get("area", "Bhubaneswar")
    
    minutes_remaining = safety.get("minutes_remaining", 120)
    total_meals = intake.get("total_quantity", 40)
    
    # Check if safety verdict was REJECT
    if safety.get("verdict") == "REJECT":
        return {
            "status": "ABORTED",
            "reason": "Safety check verdict was REJECT. No pickup plan generated.",
            "route_steps": [],
            "volunteer": None
        }

    volunteers = load_volunteers(volunteers_csv)
    available_vols = [v for v in volunteers if v["status"] == "AVAILABLE"]
    
    # Filter by vehicle capacity if large batch (>40 meals prefers auto)
    viable_vols = [v for v in available_vols if v["capacity_packets"] >= min(total_meals, 40)]
    if not viable_vols:
        viable_vols = available_vols

    # Find nearest volunteer to donor
    for v in viable_vols:
        v["dist_to_donor"] = haversine(v["lat"], v["lng"], donor_lat, donor_lng)
    viable_vols.sort(key=lambda x: x["dist_to_donor"])
    
    if not viable_vols:
        return {
            "status": "REJECTED_NO_VOLUNTEER",
            "reason": "No active volunteer available in Bhubaneswar network.",
            "route_steps": [],
            "volunteer": None
        }
        
    assigned_vol = viable_vols[0]
    
    # Determine destinations (single vs split)
    split_plan = match_data.get("split_plan")
    top_matches = match_data.get("top_matches", [])
    
    destinations = []
    if split_plan and split_plan.get("required"):
        for alloc in split_plan["allocations"]:
            # find coords from top_matches
            matched_r = next((m for m in top_matches if m["id"] == alloc["recipient_id"]), None)
            destinations.append({
                "id": alloc["recipient_id"],
                "name": alloc["recipient_name"],
                "area": alloc["area"],
                "lat": matched_r["lat"] if matched_r else donor_lat,
                "lng": matched_r["lng"] if matched_r else donor_lng,
                "meals": alloc["allocated_meals"],
                "contact": alloc["contact"]
            })
    elif top_matches:
        best = top_matches[0]
        destinations.append({
            "id": best["id"],
            "name": best["name"],
            "area": best["area"],
            "lat": best["lat"],
            "lng": best["lng"],
            "meals": total_meals,
            "contact": best["contact"]
        })
    else:
        return {
            "status": "REJECTED_NO_RECIPIENT",
            "reason": "No valid recipient match found.",
            "route_steps": [],
            "volunteer": None
        }

    # Build Route Steps (Nearest-Neighbor)
    route_steps = []
    total_km = 0.0
    elapsed_minutes = 0.0
    
    # Leg 1: Volunteer -> Donor Pickup
    leg1_km = assigned_vol["dist_to_donor"]
    leg1_drive_min = round(leg1_km * MINUTES_PER_KM, 1)
    elapsed_minutes += leg1_drive_min + PICKUP_HANDLING_MIN
    total_km += leg1_km
    
    route_steps.append({
        "step": 1,
        "type": "PICKUP",
        "location_name": f"{donor_name} ({donor_area})",
        "action": f"Pickup {total_meals} meal packets from donor",
        "distance_km": leg1_km,
        "drive_time_min": leg1_drive_min,
        "cumulative_time_min": round(elapsed_minutes, 1),
        "lat": donor_lat,
        "lng": donor_lng
    })
    
    # Leg 2+: Drops
    curr_lat, curr_lng = donor_lat, donor_lng
    for idx, dest in enumerate(destinations):
        leg_km = haversine(curr_lat, curr_lng, dest["lat"], dest["lng"])
        leg_drive_min = round(leg_km * MINUTES_PER_KM, 1)
        elapsed_minutes += leg_drive_min + DROPOFF_HANDLING_MIN
        total_km += leg_km
        curr_lat, curr_lng = dest["lat"], dest["lng"]
        
        route_steps.append({
            "step": idx + 2,
            "type": "DROPOFF",
            "location_name": f"{dest['name']} ({dest['area']})",
            "action": f"Handover {dest['meals']} meals to {dest['name']} (Contact: {dest['contact']})",
            "distance_km": leg_km,
            "drive_time_min": leg_drive_min,
            "cumulative_time_min": round(elapsed_minutes, 1),
            "lat": dest["lat"],
            "lng": dest["lng"]
        })

    # Validate against safe time window
    time_feasible = elapsed_minutes <= minutes_remaining
    if not time_feasible:
        status = "REJECTED_EXCEEDS_TIME_WINDOW"
        verdict_msg = f"REJECTED: Estimated transit & handover time ({round(elapsed_minutes)} mins) exceeds available food safety window ({minutes_remaining} mins)."
    else:
        status = "CONFIRMED"
        verdict_msg = f"CONFIRMED: Deliverable within {round(elapsed_minutes)} minutes (safety limit: {minutes_remaining} mins)."

    return {
        "status": status,
        "verdict_message": verdict_msg,
        "assigned_volunteer": {
            "id": assigned_vol["id"],
            "name": assigned_vol["name"],
            "area": assigned_vol["area"],
            "vehicle": assigned_vol["vehicle"],
            "contact": assigned_vol["contact"],
            "dist_to_donor_km": assigned_vol["dist_to_donor"]
        },
        "destinations": destinations,
        "total_distance_km": round(total_km, 2),
        "total_eta_minutes": round(elapsed_minutes, 1),
        "minutes_remaining_buffer": round(minutes_remaining - elapsed_minutes, 1),
        "route_steps": route_steps
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = safe_load(sys.argv[1])
    else:
        raw_in = sys.stdin.read().strip()
        data = safe_load(raw_in) if raw_in else {}
    result = generate_pickup_plan(data)
    print(json.dumps(result, indent=2))
