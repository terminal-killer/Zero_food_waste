import json
import sys
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

def load_templates():
    template_path = os.path.join(os.path.dirname(__file__), "../assets/templates.json")
    with open(template_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_messages(data):
    intake = data.get("intake", {})
    safety = data.get("safety", {})
    pickup = data.get("pickup", {})
    
    # If safety or pickup was rejected
    if safety.get("verdict") == "REJECT" or pickup.get("status", "").startswith("REJECT"):
        return {
            "status": "NOT_APPLICABLE",
            "reason": "Messages not generated for rejected or unsafe listings.",
            "messages": {}
        }

    templates = load_templates()
    
    # Extract variables
    donor_name = intake.get("donor_name", "Donor")
    donor_area = intake.get("area", "Bhubaneswar")
    donor_contact = intake.get("contact", "Not provided")
    total_meals = intake.get("total_quantity", 0)
    expires_at = intake.get("expires_at", "safe window")
    minutes_remaining = safety.get("minutes_remaining", 120)
    
    items = intake.get("items", [])
    items_summary = ", ".join([f"{it['qty']} {it['name']}" for it in items]) or f"{total_meals} meals"
    
    vol = pickup.get("assigned_volunteer", {})
    volunteer_name = vol.get("name", "Assigned Volunteer")
    volunteer_vehicle = vol.get("vehicle", "Vehicle")
    volunteer_contact = vol.get("contact", "9437XXXXXX")
    
    destinations = pickup.get("destinations", [])
    recipient_names = ", ".join([d["name"] for d in destinations])
    
    drop_instructions_en = " -> ".join([f"{d['name']} ({d['area']}) [{d['meals']} meals, Contact: {d.get('contact', '')}]" for d in destinations])
    drop_instructions_hi = " -> ".join([f"{d['name']} ({d['area']}) [{d['meals']} पैकेट]" for d in destinations])
    drop_instructions_or = " -> ".join([f"{d['name']} ({d['area']}) [{d['meals']} ଟି]" for d in destinations])

    route_steps = pickup.get("route_steps", [])
    pickup_eta = "15"
    drop_eta = str(round(pickup.get("total_eta_minutes", 30)))
    if route_steps:
        pickup_eta = str(round(route_steps[0].get("cumulative_time_min", 15)))

    mission_id = f"OD-{abs(hash(donor_name + donor_area)) % 10000:04d}"

    def fill_tpl(tpl, drop_inst):
        return tpl.format(
            donor_name=donor_name,
            donor_area=donor_area,
            donor_contact=donor_contact,
            total_meals=total_meals,
            items_summary=items_summary,
            volunteer_name=volunteer_name,
            volunteer_vehicle=volunteer_vehicle,
            volunteer_contact=volunteer_contact,
            recipient_names=recipient_names,
            recipient_name=destinations[0]["name"] if destinations else "Welfare Shelter",
            drop_instructions=drop_inst,
            pickup_eta=pickup_eta,
            drop_eta=drop_eta,
            expires_at=expires_at,
            minutes_remaining=minutes_remaining,
            mission_id=mission_id
        )

    out = {
        "status": "SUCCESS",
        "mission_id": mission_id,
        "languages": ["English", "Hindi", "Odia"],
        "messages": {
            "donor": {
                "en": fill_tpl(templates["donor"]["en"], drop_instructions_en),
                "hi": fill_tpl(templates["donor"]["hi"], drop_instructions_hi),
                "or": fill_tpl(templates["donor"]["or"], drop_instructions_or)
            },
            "recipient": {
                "en": fill_tpl(templates["recipient"]["en"], drop_instructions_en),
                "hi": fill_tpl(templates["recipient"]["hi"], drop_instructions_hi),
                "or": fill_tpl(templates["recipient"]["or"], drop_instructions_or)
            },
            "volunteer": {
                "en": fill_tpl(templates["volunteer"]["en"], drop_instructions_en),
                "hi": fill_tpl(templates["volunteer"]["hi"], drop_instructions_hi),
                "or": fill_tpl(templates["volunteer"]["or"], drop_instructions_or)
            }
        }
    }
    return out

if __name__ == "__main__":
    if len(sys.argv) > 1:
        data = safe_load(sys.argv[1])
    else:
        raw_in = sys.stdin.read().strip()
        data = safe_load(raw_in) if raw_in else {}
    result = build_messages(data)
    print(json.dumps(result, indent=2, ensure_ascii=False))
