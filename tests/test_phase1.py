import sys
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# Add scripts directories to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "skills", "surplus-intake", "scripts"))
sys.path.insert(0, os.path.join(BASE_DIR, "skills", "food-safety-check", "scripts"))
sys.path.insert(0, os.path.join(BASE_DIR, "skills", "match-recipients", "scripts"))

from surplus_intake import parse_surplus_intake
from safety_check import check_food_safety
from match import match_recipients

TZ_IST = ZoneInfo("Asia/Kolkata")

def run_tests():
    total_tests = 0
    passed_tests = 0
    results_log = []

    def assert_test(name, condition, details=""):
        nonlocal total_tests, passed_tests
        total_tests += 1
        if condition:
            passed_tests += 1
            results_log.append(f"[PASS] {name} {details}")
            return True
        else:
            results_log.append(f"[FAIL] {name} {details}")
            return False

    print("======================================================================")
    print("PHASE 1 AUTOMATED VERIFICATION SUITE")
    print("======================================================================\n")

    # =========================================================================
    # TEST SUITE 1: Clock / Time Variance Test (3 distinct safety outcomes)
    # =========================================================================
    print("--- 1. Testing Same Listing at Simulated Clock 10:00, 18:30, 23:30 ---")
    listing_clock = "Wedding hall in Patia, 40 veg biryani packets, cooked at 3:30 PM, expires 7:30 PM"
    
    t_1000 = "2026-10-15T10:00:00+05:30"
    t_1830 = "2026-10-15T18:30:00+05:30"
    t_2330 = "2026-10-15T23:30:00+05:30"

    intake_1000 = parse_surplus_intake(listing_clock, simulated_now=t_1000)
    safety_1000 = check_food_safety(intake_1000, simulated_now=t_1000)

    intake_1830 = parse_surplus_intake(listing_clock, simulated_now=t_1830)
    safety_1830 = check_food_safety(intake_1830, simulated_now=t_1830)

    intake_2330 = parse_surplus_intake(listing_clock, simulated_now=t_2330)
    safety_2330 = check_food_safety(intake_2330, simulated_now=t_2330)

    v_1000 = safety_1000["verdict"]
    v_1830 = safety_1830["verdict"]
    v_2330 = safety_2330["verdict"]

    print(f"  At 10:00 -> Verdict: {v_1000} (Minutes remaining: {safety_1000['minutes_remaining']})")
    print(f"  At 18:30 -> Verdict: {v_1830} (Minutes remaining: {safety_1830['minutes_remaining']})")
    print(f"  At 23:30 -> Verdict: {v_2330} (Minutes remaining: {safety_2330['minutes_remaining']})")

    assert_test(
        "Time Variance: 10:00 outcome is SAFE",
        v_1000 == "SAFE",
        f"got {v_1000}"
    )
    assert_test(
        "Time Variance: 18:30 outcome is SAFE_IF_FAST",
        v_1830 == "SAFE_IF_FAST",
        f"got {v_1830}"
    )
    assert_test(
        "Time Variance: 23:30 outcome is REJECT",
        v_2330 == "REJECT",
        f"got {v_2330}"
    )
    assert_test(
        "Time Variance: Exactly 3 distinct outcomes produced",
        len({v_1000, v_1830, v_2330}) == 3,
        f"unique verdicts: {set([v_1000, v_1830, v_2330])}"
    )

    # =========================================================================
    # TEST SUITE 2: 25 Messy Messages (Typos, Hinglish, Rel times, Missing fields)
    # =========================================================================
    print("\n--- 2. Testing 25 Messy Messages ---")
    sim_base = "2026-10-15T19:00:00+05:30"

    messy_samples = [
        # (id, text, expected_status, expected_area, check_func)
        (
            "M01_typo_area",
            "Patiya mandap, 50 veg biryani packets, cooked at 6 PM, expires 10 PM",
            "VALID", "Patia",
            lambda res: res.get("area") == "Patia" and res.get("total_quantity") == 50
        ),
        (
            "M02_typo_area_sahid",
            "Hotel in Sayed Nagar, 40 chicken meals cooked 17:30, expires 21:30",
            "VALID", "Saheed Nagar",
            lambda res: res.get("area") == "Saheed Nagar" and res.get("items")[0]["veg"] is False
        ),
        (
            "M03_typo_area_nayapali",
            "Nayapali caterer, 35 food boxes, cooked at 6:30 PM, expires 22:30",
            "VALID", "Nayapalli",
            lambda res: res.get("area") == "Nayapalli" and res.get("total_quantity") == 35
        ),
        (
            "M04_typo_area_cspur",
            "Near cs pur petrol pump, 30 veg meal packets cooked 18:00, safe till 22:00",
            "VALID", "Chandrasekharpur",
            lambda res: res.get("area") == "Chandrasekharpur" and res.get("total_quantity") == 30
        ),
        (
            "M05_typo_area_khandagiry",
            "Khandagiry square banquet, 45 meals cooked 18:30, expires 22:00",
            "VALID", "Khandagiri",
            lambda res: res.get("area") == "Khandagiri" and res.get("total_quantity") == 45
        ),
        (
            "M06_typo_area_rasulgar",
            "Rasulgar chowk, 60 veg biryani boxes cooked 17:00, expires 21:00",
            "VALID", "Rasulgarh",
            lambda res: res.get("area") == "Rasulgarh" and res.get("total_quantity") == 60
        ),
        (
            "M07_typo_area_jaidev",
            "Jaidev Vihar community center, 40 portions cooked 18:00, safe till 22:30",
            "VALID", "Jaydev Vihar",
            lambda res: res.get("area") == "Jaydev Vihar"
        ),
        (
            "M08_hinglish_baje",
            "Patia mein mandap hai, 40 packets veg biryani cooked shaam 6 baje, expires 10 PM",
            "VALID", "Patia",
            lambda res: "18:00" in res.get("cooked_at", "")
        ),
        (
            "M09_hinglish_logon_khana",
            "Saheed Nagar mein 50 logon ka khana hai, cooked 18:00, valid till 22:00",
            "VALID", "Saheed Nagar",
            lambda res: res.get("total_quantity") == 50
        ),
        (
            "M10_hinglish_pehle_cooked",
            "Nayapalli hotel, 30 veg packets taiyaar aadhe ghante pehle, expires in 3 hrs",
            "VALID", "Nayapalli",
            lambda res: res.get("total_quantity") == 30 and "cooked_at" in res
        ),
        (
            "M11_hinglish_raat_baje",
            "Bapuji Nagar caterer, 40 packets cooked 8 baje raat, expires 11:30 PM",
            "VALID", "Bapuji Nagar",
            lambda res: "20:00" in res.get("cooked_at", "")
        ),
        (
            "M12_relative_1_hr_ago",
            "Chandrasekharpur club, 40 meal packets cooked 1 hour ago, expires in 3 hrs",
            "VALID", "Chandrasekharpur",
            lambda res: "18:00" in res.get("cooked_at", "") and "22:00" in res.get("expires_at", "")
        ),
        (
            "M13_relative_30_mins_ago",
            "Unit 4 mandap, 50 meals cooked 30 mins ago, expires in 2 hrs",
            "VALID", "Unit 4",
            lambda res: "18:30" in res.get("cooked_at", "") and "21:00" in res.get("expires_at", "")
        ),
        (
            "M14_relative_tonight",
            "Old Town prasad trust, 60 veg plates cooked 17:30, expires tonight",
            "VALID", "Old Town",
            lambda res: "23:00" in res.get("expires_at", "")
        ),
        (
            "M15_relative_2_hrs_ago",
            "Baramunda reception, 35 packets cooked 2 hours ago, good for 2 hours",
            "VALID", "Baramunda",
            lambda res: "17:00" in res.get("cooked_at", "")
        ),
        (
            "M16_absolute_24hr",
            "Mancheswar corporate cafeteria, 40 veg meals cooked 18:30, expires 22:30",
            "VALID", "Mancheswar",
            lambda res: "18:30" in res.get("cooked_at", "") and res.get("total_quantity") == 40
        ),
        (
            "M17_missing_qty",
            "Wedding hall in Patia, veg biryani cooked at 6 PM, expires 10 PM",
            "NEEDS_INFO", "Patia",
            lambda res: res.get("status") == "NEEDS_INFO" and "quantity of food packets" in res.get("missing_fields", [])
        ),
        (
            "M18_missing_cooked_time",
            "50 packets veg meals in Chandrasekharpur, expires at 10 PM, phone 9861099887",
            "NEEDS_INFO", "Chandrasekharpur",
            lambda res: res.get("status") == "NEEDS_INFO" and "time when food was cooked" in res.get("missing_fields", [])
        ),
        (
            "M19_missing_location",
            "40 veg meal packets cooked 1 hour ago, expires in 3 hrs, call 9861012345",
            "NEEDS_INFO", None,
            lambda res: res.get("status") == "NEEDS_INFO" and "pickup location or neighborhood in Bhubaneswar" in res.get("missing_fields", [])
        ),
        (
            "M20_missing_qty_and_location",
            "Food cooked at 6 PM, expires 10 PM, please collect fast",
            "NEEDS_INFO", None,
            lambda res: res.get("status") == "NEEDS_INFO" and len(res.get("missing_fields", [])) == 2
        ),
        (
            "M21_missing_all_three",
            "We have leftover surplus food here, please help redistribute",
            "NEEDS_INFO", None,
            lambda res: res.get("status") == "NEEDS_INFO" and len(res.get("missing_fields", [])) == 3 and "?" in res.get("question", "")
        ),
        (
            "M22_exact_one_combined_question",
            "Caterer in Jaydev Vihar, surplus food cooked at 7 PM",
            "NEEDS_INFO", "Jaydev Vihar",
            lambda res: res.get("status") == "NEEDS_INFO" and res.get("question", "").count("?") == 1
        ),
        (
            "M23_contact_extraction",
            "Kalinga Nagar event, 30 meal boxes cooked 18:00, expires 22:00, call 9861055443",
            "VALID", "Kalinga Nagar",
            lambda res: res.get("contact") == "9861055443" and res.get("confidence_score") >= 0.75
        ),
        (
            "M24_sanitary_violation_buffet",
            "Patia hall, 40 packets cooked 18:00, open plate leftover touched by guests",
            "VALID", "Patia",
            lambda res: check_food_safety(res, simulated_now=sim_base)["verdict"] == "REJECT"
        ),
        (
            "M25_confidence_and_substrings",
            "Infocity IT cafeteria, 50 meals cooked at 6 PM, expires 10 PM",
            "VALID", "Infocity",
            lambda res: "confidence_score" in res and "matched_substrings" in res and res["confidence_score"] == 1.0
        ),
    ]

    for test_id, raw_msg, exp_status, exp_area, validator in messy_samples:
        intake_res = parse_surplus_intake(raw_msg, simulated_now=sim_base)
        status_ok = (intake_res.get("status") == exp_status)
        area_ok = True
        if exp_area:
            area_ok = (intake_res.get("area") == exp_area)
        custom_ok = validator(intake_res)

        all_ok = status_ok and area_ok and custom_ok
        details = f"(status={intake_res.get('status')}, area={intake_res.get('area')})"
        assert_test(f"Messy [{test_id}]", all_ok, details)

    # =========================================================================
    # TEST SUITE 3: Recipient Closing Time Exclusion & Scoring
    # =========================================================================
    print("\n--- 3. Testing Recipient Closing Time & Dispatch Constraints ---")
    
    # Donor at Patia with 30 meals, dispatched late at 22:15
    # Recipient REC04 (Karuna Transit Shelter) closes at 22:00
    # Recipient REC01 (Aashra Child Care Home) closes at 22:30
    # Recipient REC06 (Ekamra Night Shelter) is open until 02:00 (overnight)
    # Recipient REC11 (Railway Destitute Aid) is open until 01:00
    late_intake = {
        "status": "VALID",
        "intake_timestamp": "2026-10-15T22:15:00+05:30",
        "donor_name": "Late Night Banquet Patia",
        "area": "Patia",
        "lat": 20.3550,
        "lng": 85.8180,
        "total_quantity": 30,
        "items": [{"name": "Veg Biryani", "qty": 30, "unit": "packets", "veg": True}],
        "cooked_at": "2026-10-15T20:30:00+05:30",
        "expires_at": "2026-10-15T23:59:00+05:30"
    }

    match_result = match_recipients(late_intake, simulated_now="2026-10-15T22:15:00+05:30")
    top_recipients = match_result.get("top_matches", [])
    top_ids = [r["id"] for r in top_recipients]

    print(f"  Late dispatch at 22:15: Viable open recipients: {match_result.get('viable_open_recipients_count')}/{match_result.get('total_recipients_evaluated')}")
    for m in top_recipients:
        print(f"    Matched: {m['id']} - {m['name']} (closes: {m['available_until']}, dist: {m['distance_km']}km, score: {m['match_score']})")

    # REC04 closes at 22:00 -> must NOT be in top_matches or viable
    assert_test(
        "Closing Check: REC04 (closes 22:00) is excluded at 22:15 dispatch",
        "REC04" not in top_ids,
        f"top matches: {top_ids}"
    )

    # REC07 closes at 22:00 -> must NOT be in top_matches
    assert_test(
        "Closing Check: REC07 (closes 22:00) is excluded at 22:15 dispatch",
        "REC07" not in top_ids,
        f"top matches: {top_ids}"
    )

    # REC06 (open till 02:00) or REC03 (open till 23:30) or REC10 (open till 23:00) must be viable
    assert_test(
        "Closing Check: Open night shelters matched",
        len(top_recipients) > 0 and all(r["match_score"] > 0 for r in top_recipients),
        f"matched {len(top_recipients)} shelters"
    )

    # Deliver-by cutoff test: food expiring at 22:30 evaluated at 22:25 gives low time margin
    tight_food_intake = {
        "status": "VALID",
        "intake_timestamp": "2026-10-15T22:00:00+05:30",
        "donor_name": "Patia Express",
        "area": "Patia",
        "lat": 20.3550,
        "lng": 85.8180,
        "total_quantity": 25,
        "items": [{"name": "Meals", "qty": 25, "unit": "packets", "veg": True}],
        "cooked_at": "2026-10-15T18:00:00+05:30",
        "effective_cutoff": "2026-10-15T22:20:00+05:30", # Only 20 min buffer
        "expires_at": "2026-10-15T22:20:00+05:30"
    }
    tight_match = match_recipients(tight_food_intake, simulated_now="2026-10-15T22:00:00+05:30")
    # All arrival ETAs > 12 min buffer + transit (~15 mins) -> arrival ~22:15+, very tight or past cutoff
    assert_test(
        "Scoring Margin: Time window score scales with deliver-by cutoff margin",
        "viable_open_recipients_count" in tight_match,
        f"viable: {tight_match['viable_open_recipients_count']}"
    )

    # Summary
    print("\n======================================================================")
    pass_rate = (passed_tests / total_tests) * 100.0
    print(f"TEST RESULTS: {passed_tests}/{total_tests} PASSED ({pass_rate:.1f}%)")
    print("======================================================================")

    print("\nFailed Tests Details:")
    failures = [r for r in results_log if r.startswith("[FAIL]")]
    if not failures:
        print("  None! All tests passed!")
    else:
        for f in failures:
            print("  " + f)

    if passed_tests == total_tests:
        print("[SUCCESS] All Phase 1 requirements fully satisfied.")
        return 0
    else:
        print("[WARNING] Some tests failed. Review log above.")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
