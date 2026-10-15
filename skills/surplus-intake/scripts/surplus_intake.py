import re
import json
import sys
import os
import csv
import difflib
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

TZ_IST = ZoneInfo("Asia/Kolkata")

def get_current_time(simulated_now=None):
    """Returns aware datetime in Asia/Kolkata timezone."""
    if simulated_now:
        if isinstance(simulated_now, datetime):
            if simulated_now.tzinfo is None:
                return simulated_now.replace(tzinfo=TZ_IST)
            return simulated_now.astimezone(TZ_IST)
        
        # Parse ISO format or standard string format
        sim_str = str(simulated_now).strip()
        try:
            # Handle ISO-8601 strings
            dt = datetime.fromisoformat(sim_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TZ_IST)
            return dt.astimezone(TZ_IST)
        except Exception:
            # Handle simple HH:MM or HH:MM:SS
            m = re.match(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$', sim_str)
            if m:
                today = datetime.now(TZ_IST).date()
                hr = int(m.group(1))
                mn = int(m.group(2))
                sec = int(m.group(3)) if m.group(3) else 0
                return datetime(today.year, today.month, today.day, hr, mn, sec, tzinfo=TZ_IST)
    return datetime.now(TZ_IST)

def load_areas(csv_path=None):
    """Loads Bhubaneswar localities and aliases from data/areas.csv."""
    if not csv_path:
        csv_path = os.path.join(os.path.dirname(__file__), "../../../data/areas.csv")
    
    areas = []
    if os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                aliases = [a.strip().lower() for a in row.get("aliases", "").split(",") if a.strip()]
                areas.append({
                    "name": row["name"].strip(),
                    "lat": float(row["lat"]),
                    "lng": float(row["lng"]),
                    "aliases": aliases
                })
    return areas

def match_area(text, areas):
    """Fuzzy-matches text against known Bhubaneswar areas and aliases."""
    text_lower = text.lower()
    
    # 1. Direct name / alias substring check (longest match first)
    sorted_areas = sorted(areas, key=lambda a: len(a["name"]), reverse=True)
    for a in sorted_areas:
        if re.search(r'\b' + re.escape(a["name"].lower()) + r'\b', text_lower):
            return a, a["name"], 1.0
        for alias in a["aliases"]:
            if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
                return a, alias, 0.98

    # 2. Tokenized word fuzzy check using difflib
    words = re.findall(r'[a-zA-Z]{3,}', text_lower)
    best_candidate = None
    best_score = 0.0
    matched_word = ""

    # Check 1-word and 2-word sliding windows
    candidates_list = []
    for i in range(len(words)):
        candidates_list.append(words[i])
        if i < len(words) - 1:
            candidates_list.append(words[i] + " " + words[i+1])

    for cand in candidates_list:
        for a in areas:
            # Match against main name
            target_name = a["name"].lower()
            ratio = difflib.SequenceMatcher(None, cand, target_name).ratio()
            if ratio > best_score and ratio >= 0.78:
                best_score = ratio
                best_candidate = a
                matched_word = cand
            # Match against aliases
            for alias in a["aliases"]:
                alias_ratio = difflib.SequenceMatcher(None, cand, alias).ratio()
                if alias_ratio > best_score and alias_ratio >= 0.80:
                    best_score = alias_ratio
                    best_candidate = a
                    matched_word = cand

    if best_candidate and best_score >= 0.78:
        return best_candidate, matched_word, round(best_score, 2)

    return None, None, 0.0

def parse_relative_time(text, now_ist):
    """Parses relative expressions like '1 hour ago', '30 mins ago', 'expires in 2 hrs'."""
    text_lower = text.lower()
    cooked_at = None
    expires_at = None
    matched_cooked = None
    matched_expires = None

    # Cooked ago patterns (e.g. 'cooked 1 hour ago', 'cooked 30 mins ago', '2 ghante pehle', '1 hr ago')
    ago_match = re.search(
        r'(?:cooked|prepared|made|baked|taiyaar)?\s*(\d+(?:\.\d+)?|\bhalf an?\b|\baadhe?\b)?\s*(hours?|hrs?|minutes?|mins?|ghante?|minute)\s*(?:ago|pehle)',
        text_lower
    )
    if ago_match:
        val_str = ago_match.group(1)
        unit = ago_match.group(2)
        if not val_str or val_str in ["half a", "half an", "aadhe"]:
            val = 0.5
        else:
            try:
                val = float(val_str)
            except ValueError:
                val = 1.0

        if any(u in unit for u in ["hour", "hr", "ghante"]):
            delta = timedelta(hours=val)
        else:
            delta = timedelta(minutes=val)
        
        cooked_at = now_ist - delta
        matched_cooked = ago_match.group(0).strip()

    # Expires in patterns (e.g. 'expires in 3 hrs', 'good for 4 hours', 'valid for 2 hours', '3 ghante mein')
    in_match = re.search(
        r'(?:expires?\s*(?:in|for)?|good\s*(?:for|till)?|valid\s*(?:for|till)?|safe\s*(?:for|till)?|\bin)\s*(\d+(?:\.\d+)?|\bhalf an?\b|\baadhe?\b)?\s*(hours?|hrs?|minutes?|mins?|ghante?)\s*(?:in|mein)?',
        text_lower
    )
    # Ensure it's not the ago match
    if in_match and "ago" not in in_match.group(0) and "pehle" not in in_match.group(0):
        val_str = in_match.group(1)
        unit = in_match.group(2)
        if val_str:
            val = 0.5 if "half" in val_str or "aadhe" in val_str else float(val_str)
            delta = timedelta(hours=val) if any(u in unit for u in ["hour", "hr", "ghante"]) else timedelta(minutes=val)
            expires_at = now_ist + delta
            matched_expires = in_match.group(0).strip()

    # 'tonight' / 'aaj raat'
    if not expires_at and ("tonight" in text_lower or "aaj raat" in text_lower):
        expires_at = datetime(now_ist.year, now_ist.month, now_ist.day, 23, 0, 0, tzinfo=TZ_IST)
        matched_expires = "tonight"

    return cooked_at, expires_at, matched_cooked, matched_expires

def parse_time_point(t_str, now_ist, is_cooked=True):
    """
    Parses a time string into an aware datetime.
    If no date is specified, assumes today.
    If is_cooked is True and that time is > 12 hours in the future, assumes yesterday.
    """
    t_clean = t_str.lower().strip()
    hr = None
    mn = 0
    meridiem = None

    # Handle Hinglish: '9 baje', 'shaam 6 baje', '6 baje shaam', '10 baje raat', 'subah 8 baje'
    baje_match = re.search(r'(?:(shaam|raat|subah|dopahar)\s+)?(\d{1,2})(?::(\d{2}))?\s*baje(?:\s+(shaam|raat|subah|dopahar))?', t_clean)
    if baje_match:
        context = baje_match.group(1) or baje_match.group(4)
        hr = int(baje_match.group(2))
        mn = int(baje_match.group(3)) if baje_match.group(3) else 0
        if context in ["shaam", "raat"] and hr < 12:
            hr += 12
        elif context == "subah" and hr == 12:
            hr = 0
        elif context == "dopahar" and hr != 12 and hr < 6:
            hr += 12
        elif not context:
            # Default evening preference for typical hackathon / dinner donation if hr between 6 and 11
            if 6 <= hr <= 11 and hr != 12:
                hr += 12
            elif hr <= 5:
                # e.g. 2 baje or 3 baje is afternoon
                hr += 12
    else:
        # Standard format 6:30 PM, 18:30, 6 PM, 11 AM
        m12 = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', t_clean)
        if m12:
            hr = int(m12.group(1))
            mn = int(m12.group(2)) if m12.group(2) else 0
            meridiem = m12.group(3)
            if meridiem == "pm" and hr != 12:
                hr += 12
            elif meridiem == "am" and hr == 12:
                hr = 0
        else:
            # 24-hr format like 18:30 or 21:00
            m24 = re.search(r'\b([01]?\d|2[0-3]):([0-5]\d)\b', t_clean)
            if m24:
                hr = int(m24.group(1))
                mn = int(m24.group(2))

    if hr is None:
        return None

    # Construct datetime for today
    candidate = datetime(now_ist.year, now_ist.month, now_ist.day, hr, mn, 0, tzinfo=TZ_IST)

    # Date resolution logic:
    # "If a time has no date, assume today, and if that is more than 12 hours in the future, assume yesterday for cooked_at."
    if is_cooked:
        diff_hours = (candidate - now_ist).total_seconds() / 3600.0
        if diff_hours > 12.0:
            candidate -= timedelta(days=1)
    else:
        # Expiry time: if it's already past by more than 6 hours, could refer to tomorrow early AM
        if candidate < now_ist and (now_ist - candidate).total_seconds() > 6 * 3600:
            candidate += timedelta(days=1)

    return candidate

def parse_surplus_intake(raw_text, simulated_now=None, areas_csv=None):
    """
    Main intake function.
    Returns structured JSON with ISO-8601 datetimes, confidence score, and matched substrings.
    Returns status: NEEDS_INFO with exactly one combined question if required fields are missing.
    """
    now_ist = get_current_time(simulated_now)
    text_clean = raw_text.strip()
    text_lower = text_clean.lower()
    
    matched_substrings = {}
    confidence_points = 0.0
    total_points = 4.0

    # 1. Extract Contact Number
    phone_match = re.search(r'\b(?:\+91[-\s]?)?[6-9]\d{9}\b', raw_text)
    contact = phone_match.group(0).replace(" ", "").replace("-", "") if phone_match else None
    if contact:
        matched_substrings["contact"] = phone_match.group(0)

    # 2. Extract Area / Location via Fuzzy Matching against data/areas.csv
    areas = load_areas(areas_csv)
    matched_area_obj, matched_area_word, area_score = match_area(text_clean, areas)
    
    area_name = None
    lat, lng = None, None
    if matched_area_obj:
        area_name = matched_area_obj["name"]
        lat = matched_area_obj["lat"]
        lng = matched_area_obj["lng"]
        matched_substrings["area"] = matched_area_word
        confidence_points += area_score
    
    # 3. Extract Quantity and Items
    items = []
    total_qty = 0
    matched_qty_str = None

    # Check explicit patterns: 40 packets, 30 meals, 50 portions, 20 biryani boxes, 30 patties
    item_matches = re.findall(
        r'(\d+)\s*(?:packets?|boxes?|cups?|pots?|plates?|containers?|trays?|rolls?|patties?|meals?|portions?|servings?)\b(?:\s+(?:of\s+)?([a-zA-Z\s]{2,25}))?',
        raw_text, re.IGNORECASE
    )
    if not item_matches:
        # Alternative order: 40 veg biryani packets
        alt_matches = re.findall(
            r'(\d+)\s+([a-zA-Z\s]{2,25}?)\s*(?:packets?|boxes?|cups?|pots?|plates?|containers?|trays?|rolls?|patties?|meals?|servings?)',
            raw_text, re.IGNORECASE
        )
        if alt_matches:
            for qty_str, name in alt_matches:
                q = int(qty_str)
                n = name.strip()
                n = re.split(r'\b(?:in|at|near|from|cooked|prepared|taiyaar|expires?|phone|call)\b', n, flags=re.IGNORECASE)[0].strip()
                if not n or n.lower() in ["cooked", "prepared", "taiyaar", "veg", "non-veg"]:
                    n = "Assorted Meal Packets"
                is_veg = not any(w in n.lower() for w in ["chicken", "mutton", "fish", "egg", "non-veg"])
                items.append({"name": n, "qty": q, "unit": "packets", "veg": is_veg})
                total_qty += q
                matched_qty_str = f"{qty_str} {name}"
    else:
        for qty_str, name in item_matches:
            q = int(qty_str)
            n = (name or "").strip()
            n = re.split(r'\b(?:in|at|near|from|cooked|prepared|taiyaar|expires?|phone|call)\b', n, flags=re.IGNORECASE)[0].strip()
            if not n or n.lower() in ["cooked", "prepared", "taiyaar", "veg", "non-veg"]:
                n = "Assorted Meal Packets"
            is_veg = not any(w in n.lower() for w in ["chicken", "mutton", "fish", "egg", "non-veg"])
            items.append({"name": n, "qty": q, "unit": "packets", "veg": is_veg})
            total_qty += q
            matched_qty_str = f"{qty_str} packets"

    if total_qty == 0:
        # Check people / persons / log pattern: "food for 50 people", "40 logon ka khana"
        people_match = re.search(r'(?:food|khana|surplus|meals?)?\s*(?:for|of)?\s*(\d+)\s*(?:people|persons?|log|logon)\b', text_lower)
        if people_match:
            total_qty = int(people_match.group(1))
            items.append({"name": "Meal Servings", "qty": total_qty, "unit": "servings", "veg": "non-veg" not in text_lower})
            matched_qty_str = people_match.group(0)

    if total_qty == 0:
        # Direct numeric quantity fallback: e.g. "40 veg meals" or "50 packets"
        num_match = re.search(r'\b(\d{1,4})\s*(?:veg|non-veg|meals?|packets?|boxes?|portions?|plates?|servings?)\b', raw_text, re.IGNORECASE)
        if num_match:
            total_qty = int(num_match.group(1))
            items.append({"name": "Assorted Meal Packets", "qty": total_qty, "unit": "packets", "veg": "non-veg" not in text_lower})
            matched_qty_str = num_match.group(0)

    if total_qty > 0:
        matched_substrings["quantity"] = matched_qty_str or f"{total_qty} units"
        confidence_points += 1.0

    # 4. Extract Times (Relative and Absolute)
    cooked_dt = None
    expires_dt = None

    # Check relative time first
    rel_cooked, rel_expires, m_rel_c, m_rel_e = parse_relative_time(raw_text, now_ist)
    if rel_cooked:
        cooked_dt = rel_cooked
        matched_substrings["cooked_at"] = m_rel_c
    if rel_expires:
        expires_dt = rel_expires
        matched_substrings["expires_at"] = m_rel_e

    # Search absolute times: e.g. 'cooked at 6 PM', '6:30 PM', '9 baje', 'shaam 6 baje'
    time_expr = r'((?:(?:shaam|raat|subah|dopahar)\s+)?\d{1,2}(?::\d{2})?\s*(?:am|pm|baje(?:\s+(?:shaam|raat|subah|dopahar))?)|\b[012]?\d:[0-5]\d\b)'
    cooked_pat = re.search(r'(?:cooked|prepared|made|baked|taiyaar)\s*(?:at|around)?\s*' + time_expr, text_lower)
    if not cooked_dt and cooked_pat:
        cand_str = cooked_pat.group(1)
        parsed_c = parse_time_point(cand_str, now_ist, is_cooked=True)
        if parsed_c:
            cooked_dt = parsed_c
            matched_substrings["cooked_at"] = cooked_pat.group(0)

    expires_pat = re.search(r'(?:expires?|good till|valid till|safe till|till|up to)\s*(?:at|around)?\s*' + time_expr, text_lower)
    if not expires_dt and expires_pat:
        cand_str = expires_pat.group(1)
        parsed_e = parse_time_point(cand_str, now_ist, is_cooked=False)
        if parsed_e:
            expires_dt = parsed_e
            matched_substrings["expires_at"] = expires_pat.group(0)

    # General fallback for raw timestamps if prefix wasn't used: e.g. "cooked 6 PM, expires 11 PM"
    all_time_matches = re.findall(time_expr, text_lower)
    # Collect substrings that have already been attributed to cooked or expires
    consumed_times = []
    if "cooked_at" in matched_substrings:
        consumed_times.append(matched_substrings["cooked_at"])
    if "expires_at" in matched_substrings:
        consumed_times.append(matched_substrings["expires_at"])

    # Only consider time matches that were not part of already matched clauses
    unconsumed = []
    for tm in all_time_matches:
        if not any(tm in c for c in consumed_times):
            unconsumed.append(tm)

    if not cooked_dt and len(unconsumed) > 0:
        cooked_dt = parse_time_point(unconsumed[0], now_ist, is_cooked=True)
        matched_substrings["cooked_at"] = unconsumed[0]
        unconsumed.pop(0)
    if not expires_dt and len(unconsumed) > 0:
        expires_dt = parse_time_point(unconsumed[0], now_ist, is_cooked=False)
        matched_substrings["expires_at"] = unconsumed[0]

    # If expires_dt is still missing but cooked_dt exists, default safe expiry is cooked_at + 4 hours
    if cooked_dt and not expires_dt:
        expires_dt = cooked_dt + timedelta(hours=4)
        matched_substrings["expires_at"] = "derived (cooked_at + 4h)"

    if cooked_dt:
        confidence_points += 1.0
    if expires_dt:
        confidence_points += 1.0

    # 5. Extract Donor Type & Name
    donor_type = "Banquet/Caterer"
    if any(w in text_lower for w in ["wedding", "mandap", "banquet", "hall", "reception"]):
        donor_type = "Wedding/Event Mandap"
    elif any(w in text_lower for w in ["corporate", "summit", "tech", "office", "towers"]):
        donor_type = "Corporate Cafeteria"
    elif any(w in text_lower for w in ["temple", "prasad", "samiti", "seva"]):
        donor_type = "Religious / Temple Trust"
    elif any(w in text_lower for w in ["bakery", "cafe", "restaurant", "hotel"]):
        donor_type = "Restaurant / Bakery"

    donor_name = None
    name_match = re.search(r'(?:at|from)\s+([A-Za-z0-9\s]{3,35}?)(?:,|\.|\s+in|\s+near)', text_clean, re.IGNORECASE)
    if name_match:
        candidate = name_match.group(1).strip()
        if not re.search(r'\b\d{1,2}\s*(?:am|pm|baje)\b', candidate, re.IGNORECASE):
            donor_name = candidate

    if not donor_name:
        first_clause = re.split(r'[,.\n]', text_clean)[0].strip()
        if len(first_clause) <= 35 and not re.search(r'\b\d{1,2}\s*(?:am|pm|baje)\b', first_clause, re.IGNORECASE):
            donor_name = first_clause
        else:
            donor_name = f"Surplus Donor ({area_name or 'Bhubaneswar'})"

    # 6. Check missing required fields: quantity, cooked_at, location
    missing_fields = []
    if total_qty == 0:
        missing_fields.append("quantity of food packets")
    if not cooked_dt:
        missing_fields.append("time when food was cooked")
    if not area_name:
        missing_fields.append("pickup location or neighborhood in Bhubaneswar")

    if missing_fields:
        # Formulate EXACTLY ONE combined question. Never guess.
        if len(missing_fields) == 1:
            q_text = f"Could you please specify the {missing_fields[0]}?"
        elif len(missing_fields) == 2:
            q_text = f"Could you please clarify the {missing_fields[0]} and {missing_fields[1]}?"
        else:
            q_text = f"Could you please provide the {missing_fields[0]}, {missing_fields[1]}, and {missing_fields[2]}?"
        
        return {
            "status": "NEEDS_INFO",
            "question": q_text,
            "missing_fields": missing_fields,
            "donor_name": donor_name,
            "donor_type": donor_type,
            "area": area_name,
            "lat": lat,
            "lng": lng,
            "total_quantity": total_qty,
            "intake_timestamp": now_ist.isoformat(),
            "confidence_score": round(confidence_points / total_points, 2),
            "matched_substrings": matched_substrings,
            "raw_text": text_clean
        }

    # Storage condition
    storage_condition = "ambient"
    if any(w in text_lower for w in ["hot box", "insulated", "steaming", "hot", "above 60", "above 65"]):
        storage_condition = "hot_insulated"
    elif any(w in text_lower for w in ["chilled", "refrigerated", "cold", "below 5"]):
        storage_condition = "chilled"
    elif any(w in text_lower for w in ["open", "plate food", "half-eaten", "buffet trays"]):
        storage_condition = "open_leftover"

    confidence_score = round(confidence_points / total_points, 2)

    return {
        "status": "VALID",
        "intake_timestamp": now_ist.isoformat(),
        "donor_name": donor_name,
        "donor_type": donor_type,
        "area": area_name,
        "lat": lat,
        "lng": lng,
        "items": items,
        "total_quantity": total_qty,
        "storage_condition": storage_condition,
        "cooked_at": cooked_dt.isoformat(),
        "expires_at": expires_dt.isoformat(),
        "contact": contact or "Not provided",
        "raw_text": text_clean,
        "confidence_score": confidence_score,
        "matched_substrings": matched_substrings
    }

if __name__ == "__main__":
    sim_now_arg = None
    for arg in sys.argv[1:]:
        if arg.startswith("--simulated-now="):
            sim_now_arg = arg.split("=", 1)[1]
    
    clean_args = [a for a in sys.argv[1:] if not a.startswith("--simulated-now=")]
    raw_in = " ".join(clean_args) if clean_args else sys.stdin.read().strip()
    
    result = parse_surplus_intake(raw_in, simulated_now=sim_now_arg)
    print(json.dumps(result, indent=2, ensure_ascii=False))
